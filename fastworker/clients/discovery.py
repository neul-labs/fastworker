"""Service discovery for FastWorker."""
import asyncio
import json
import logging
from typing import Dict, List, Optional
from fastworker.patterns.nng_patterns import BusPattern

logger = logging.getLogger(__name__)

class ServiceDiscovery:
    """Service discovery using nng Bus pattern."""
    
    def __init__(self, discovery_address: str):
        self.discovery_address = discovery_address
        self.bus_pattern = BusPattern(discovery_address, listen=True)
        self.services: Dict[str, Dict] = {}
        self.running = False
    
    async def start(self):
        """Start the service discovery."""
        await self.bus_pattern.start()
        self.running = True
        logger.info(f"Service discovery started on {self.discovery_address}")
        
        # Start listening for service announcements
        asyncio.create_task(self._listen_for_announcements())
    
    async def _listen_for_announcements(self):
        """Listen for service announcements."""
        while self.running:
            try:
                data = await self.bus_pattern.recv()
                announcement = json.loads(data.decode('utf-8'))
                
                service_id = announcement.get('service_id')
                service_type = announcement.get('service_type')
                address = announcement.get('address')
                action = announcement.get('action')
                
                if action == 'register':
                    self.services[service_id] = {
                        'type': service_type,
                        'address': address,
                        'timestamp': asyncio.get_event_loop().time()
                    }
                    logger.info(f"Registered service {service_id} at {address}")
                elif action == 'unregister':
                    if service_id in self.services:
                        del self.services[service_id]
                        logger.info(f"Unregistered service {service_id}")
                        
            except Exception as e:
                logger.error(f"Error in service discovery: {e}")
    
    async def register_service(self, service_id: str, service_type: str, address: str):
        """Register a service."""
        announcement = {
            'service_id': service_id,
            'service_type': service_type,
            'address': address,
            'action': 'register'
        }
        data = json.dumps(announcement).encode('utf-8')
        await self.bus_pattern.send(data)
    
    async def unregister_service(self, service_id: str):
        """Unregister a service."""
        announcement = {
            'service_id': service_id,
            'action': 'unregister'
        }
        data = json.dumps(announcement).encode('utf-8')
        await self.bus_pattern.send(data)
    
    def get_services(self, service_type: Optional[str] = None) -> List[Dict]:
        """Get registered services."""
        if service_type:
            return [service for service in self.services.values() 
                   if service['type'] == service_type]
        return list(self.services.values())
    
    def stop(self):
        """Stop the service discovery."""
        self.running = False
        self.bus_pattern.close()
        logger.info("Service discovery stopped")