"""Subworker implementation for FastQueue."""
import asyncio
import logging
import os
import signal
from typing import Dict, Optional
from datetime import datetime
from urllib.parse import urlparse

from fastqueue.patterns.nng_patterns import (
    ReqRepPattern, 
    BusPattern
)
from fastqueue.tasks.registry import task_registry
from fastqueue.tasks.models import Task, TaskResult, TaskStatus, TaskPriority
from fastqueue.tasks.serializer import TaskSerializer, SerializationFormat
from fastqueue.workers.worker import Worker

logger = logging.getLogger(__name__)

class SubWorker(Worker):
    """Subworker that registers with control plane and processes tasks.

    Configuration can be provided via environment variables:
    - FASTQUEUE_WORKER_ID: Worker ID (required if not provided as argument)
    - FASTQUEUE_CONTROL_PLANE_ADDRESS: Control plane address (required if not provided as argument)
    - FASTQUEUE_BASE_ADDRESS: Base address for this subworker (default: tcp://127.0.0.1:5555)
    - FASTQUEUE_DISCOVERY_ADDRESS: Service discovery address (default: tcp://127.0.0.1:5550)
    - FASTQUEUE_SERIALIZATION_FORMAT: Serialization format - JSON or PICKLE (default: JSON)
    """

    def __init__(self,
                 worker_id: Optional[str] = None,
                 control_plane_address: Optional[str] = None,
                 base_address: Optional[str] = None,
                 discovery_address: Optional[str] = None,
                 serialization_format: Optional[SerializationFormat] = None):
        # Load from environment variables with fallback to defaults
        worker_id = worker_id or os.getenv("FASTQUEUE_WORKER_ID")
        if not worker_id:
            raise ValueError("worker_id must be provided either as argument or via FASTQUEUE_WORKER_ID environment variable")

        control_plane_address = control_plane_address or os.getenv("FASTQUEUE_CONTROL_PLANE_ADDRESS")
        if not control_plane_address:
            raise ValueError("control_plane_address must be provided either as argument or via FASTQUEUE_CONTROL_PLANE_ADDRESS environment variable")

        base_address = base_address or os.getenv("FASTQUEUE_BASE_ADDRESS", "tcp://127.0.0.1:5555")
        discovery_address = discovery_address or os.getenv("FASTQUEUE_DISCOVERY_ADDRESS", "tcp://127.0.0.1:5550")

        # Parse serialization format from string if needed
        if serialization_format is None:
            format_str = os.getenv("FASTQUEUE_SERIALIZATION_FORMAT", "JSON").upper()
            serialization_format = (
                SerializationFormat.PICKLE if format_str == "PICKLE"
                else SerializationFormat.JSON
            )
        super().__init__(worker_id, base_address, discovery_address, serialization_format)
        
        # Override discovery bus - subworkers should DIAL, not LISTEN
        # Only the control plane listens on the discovery bus
        self.discovery_bus = BusPattern(discovery_address, listen=False)
        
        # Override patterns to use ReqRepPattern instead of SurveyorRespondentPattern
        # (control plane uses ReqRepPattern to send tasks, so subworker must match)
        parsed = urlparse(base_address)
        host = parsed.hostname or "127.0.0.1"
        base_port = parsed.port or 5555
        scheme = parsed.scheme or "tcp"
        
        priority_ports = {
            'critical': base_port,
            'high': base_port + 1,
            'normal': base_port + 2,
            'low': base_port + 3
        }
        
        # Replace SurveyorRespondentPattern with ReqRepPattern (is_server=True means listen)
        self.critical_respondent = ReqRepPattern(
            f"{scheme}://{host}:{priority_ports['critical']}", is_server=True)
        self.high_respondent = ReqRepPattern(
            f"{scheme}://{host}:{priority_ports['high']}", is_server=True)
        self.normal_respondent = ReqRepPattern(
            f"{scheme}://{host}:{priority_ports['normal']}", is_server=True)
        self.low_respondent = ReqRepPattern(
            f"{scheme}://{host}:{priority_ports['low']}", is_server=True)
        
        self.control_plane_address = control_plane_address
        self.registered = False
        
        # Parse control plane address to get management port
        parsed_cp = urlparse(control_plane_address)
        host_cp = parsed_cp.hostname or "127.0.0.1"
        scheme_cp = parsed_cp.scheme or "tcp"
        # Assume control plane management port is base_port + 5 (5560)
        base_port_cp = parsed_cp.port or 5555
        management_port = base_port_cp + 5
        
        self.control_plane_registry = ReqRepPattern(
            f"{scheme_cp}://{host_cp}:{management_port}", is_server=False)
    
    async def start(self):
        """Start the subworker and register with control plane."""
        logger.info(f"Starting subworker {self.worker_id}")
        
        # Set up signal handlers
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._signal_handler, sig)
        
        # Start service discovery bus
        await self.discovery_bus.start()
        
        # Start all respondents (for receiving tasks from control plane)
        await self.critical_respondent.start()
        await self.high_respondent.start()
        await self.normal_respondent.start()
        await self.low_respondent.start()
        
        self.running = True
        
        # Register with control plane
        await self._register_with_control_plane()
        
        # Start periodic re-registration
        asyncio.create_task(self._periodic_reregistration())
        
        logger.info(f"Subworker {self.worker_id} started and registered")
        
        # Start processing tasks for each priority
        tasks = [
            asyncio.create_task(self._process_tasks(self.critical_respondent, TaskPriority.CRITICAL)),
            asyncio.create_task(self._process_tasks(self.high_respondent, TaskPriority.HIGH)),
            asyncio.create_task(self._process_tasks(self.normal_respondent, TaskPriority.NORMAL)),
            asyncio.create_task(self._process_tasks(self.low_respondent, TaskPriority.LOW))
        ]
        
        # Wait for shutdown
        await self.shutdown_event.wait()
        
        # Cancel all tasks
        for task in tasks:
            task.cancel()
        
        self.stop()
    
    async def _register_with_control_plane(self):
        """Register this subworker with the control plane."""
        try:
            await self.control_plane_registry.start()
            
            registration = {
                'subworker_id': self.worker_id,
                'address': self.base_address,
                'status': 'active'
            }
            
            registration_data = TaskSerializer.serialize(registration, self.serialization_format)
            await self.control_plane_registry.send(registration_data)
            
            # Wait for acknowledgment
            ack_data = await asyncio.wait_for(
                self.control_plane_registry.recv(), timeout=5.0)
            ack = TaskSerializer.deserialize(ack_data, self.serialization_format)
            
            if ack.get('status') == 'registered':
                self.registered = True
                logger.info(f"Subworker {self.worker_id} registered with control plane")
            else:
                logger.warning(f"Registration failed for subworker {self.worker_id}")
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout registering subworker {self.worker_id} with control plane")
            self.registered = False
        except Exception as e:
            logger.error(f"Error registering with control plane: {e}")
            self.registered = False
    
    async def _periodic_reregistration(self):
        """Periodically re-register with control plane to maintain connection."""
        while self.running:
            try:
                await asyncio.sleep(10.0)  # Re-register every 10 seconds
                if not self.registered:
                    await self._register_with_control_plane()
                else:
                    # Send heartbeat/update
                    try:
                        update = {
                            'subworker_id': self.worker_id,
                            'address': self.base_address,
                            'status': 'active',
                            'heartbeat': True
                        }
                        update_data = TaskSerializer.serialize(update, self.serialization_format)
                        await self.control_plane_registry.send(update_data)
                        # Wait for ack (non-blocking, with timeout)
                        try:
                            ack_data = await asyncio.wait_for(
                                self.control_plane_registry.recv(), timeout=1.0)
                            ack = TaskSerializer.deserialize(ack_data, self.serialization_format)
                            if ack.get('status') != 'registered':
                                self.registered = False
                        except asyncio.TimeoutError:
                            # No response, but that's okay for heartbeat
                            pass
                    except Exception as e:
                        logger.debug(f"Error sending heartbeat: {e}")
                        self.registered = False
            except Exception as e:
                logger.error(f"Error in periodic re-registration: {e}")
                await asyncio.sleep(10.0)
    
    def stop(self):
        """Stop the subworker."""
        logger.info(f"Stopping subworker {self.worker_id}")
        super().stop()
        if hasattr(self, 'control_plane_registry'):
            self.control_plane_registry.close()