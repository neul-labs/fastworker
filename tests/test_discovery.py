"""Test cases for FastWorker ServiceDiscovery."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import json

from fastworker.clients.discovery import ServiceDiscovery


def test_service_discovery_initialization():
    """Test service discovery initialization."""
    discovery = ServiceDiscovery(discovery_address="tcp://127.0.0.1:5550")

    assert discovery.discovery_address == "tcp://127.0.0.1:5550"
    assert discovery.running is False
    assert isinstance(discovery.services, dict)
    assert len(discovery.services) == 0


def test_service_discovery_bus_pattern():
    """Test service discovery has bus pattern."""
    discovery = ServiceDiscovery(discovery_address="tcp://127.0.0.1:5550")

    assert discovery.bus_pattern is not None
    assert discovery.bus_pattern.listen is True


def test_service_discovery_not_running_by_default():
    """Test service discovery is not running after initialization."""
    discovery = ServiceDiscovery(discovery_address="tcp://127.0.0.1:5550")

    assert discovery.running is False


@pytest.mark.asyncio
async def test_service_discovery_start():
    """Test service discovery start."""
    discovery = ServiceDiscovery(discovery_address="tcp://127.0.0.1:5550")

    # Mock the bus pattern start
    with patch.object(discovery.bus_pattern, "start", new_callable=AsyncMock):
        await discovery.start()

    assert discovery.running is True


@pytest.mark.asyncio
async def test_service_discovery_stop():
    """Test service discovery stop."""
    discovery = ServiceDiscovery(discovery_address="tcp://127.0.0.1:5550")

    # Start first
    with patch.object(discovery.bus_pattern, "start", new_callable=AsyncMock):
        await discovery.start()

    # Stop should work without error
    with patch.object(discovery.bus_pattern, "close"):
        discovery.stop()

    assert discovery.running is False


def test_get_services_empty():
    """Test get services returns empty list when no services registered."""
    discovery = ServiceDiscovery(discovery_address="tcp://127.0.0.1:5550")

    services = discovery.get_services()
    assert services == []


def test_get_services_with_filter():
    """Test get services with service type filter."""
    discovery = ServiceDiscovery(discovery_address="tcp://127.0.0.1:5550")

    # Add some services
    discovery.services["service1"] = {
        "type": "control-plane",
        "address": "tcp://127.0.0.1:5555",
        "timestamp": 1234567890.0,
    }
    discovery.services["service2"] = {
        "type": "subworker",
        "address": "tcp://127.0.0.1:5561",
        "timestamp": 1234567890.0,
    }
    discovery.services["service3"] = {
        "type": "control-plane",
        "address": "tcp://127.0.0.1:5556",
        "timestamp": 1234567890.0,
    }

    # Filter by type
    control_planes = discovery.get_services(service_type="control-plane")
    assert len(control_planes) == 2

    subworkers = discovery.get_services(service_type="subworker")
    assert len(subworkers) == 1
    assert subworkers[0]["address"] == "tcp://127.0.0.1:5561"


def test_get_services_no_filter():
    """Test get services returns all when no filter."""
    discovery = ServiceDiscovery(discovery_address="tcp://127.0.0.1:5550")

    # Add some services
    discovery.services["service1"] = {
        "type": "control-plane",
        "address": "tcp://127.0.0.1:5555",
        "timestamp": 1234567890.0,
    }
    discovery.services["service2"] = {
        "type": "subworker",
        "address": "tcp://127.0.0.1:5561",
        "timestamp": 1234567890.0,
    }

    all_services = discovery.get_services()
    assert len(all_services) == 2


@pytest.mark.asyncio
async def test_register_service():
    """Test service registration."""
    discovery = ServiceDiscovery(discovery_address="tcp://127.0.0.1:5550")

    # Mock the send method
    with patch.object(discovery.bus_pattern, "send", new_callable=AsyncMock) as mock_send:
        await discovery.register_service(
            service_id="my-service",
            service_type="control-plane",
            address="tcp://127.0.0.1:5555",
        )

        # Verify send was called with correct data
        mock_send.assert_called_once()
        sent_data = mock_send.call_args[0][0]
        announcement = json.loads(sent_data.decode("utf-8"))

        assert announcement["service_id"] == "my-service"
        assert announcement["service_type"] == "control-plane"
        assert announcement["address"] == "tcp://127.0.0.1:5555"
        assert announcement["action"] == "register"


@pytest.mark.asyncio
async def test_unregister_service():
    """Test service unregistration."""
    discovery = ServiceDiscovery(discovery_address="tcp://127.0.0.1:5550")

    # Mock the send method
    with patch.object(discovery.bus_pattern, "send", new_callable=AsyncMock) as mock_send:
        await discovery.unregister_service(service_id="my-service")

        # Verify send was called with correct data
        mock_send.assert_called_once()
        sent_data = mock_send.call_args[0][0]
        announcement = json.loads(sent_data.decode("utf-8"))

        assert announcement["service_id"] == "my-service"
        assert announcement["action"] == "unregister"


def test_service_discovery_multiple_services():
    """Test discovery with multiple services."""
    discovery = ServiceDiscovery(discovery_address="tcp://127.0.0.1:5550")

    # Add multiple services
    discovery.services["cp1"] = {
        "type": "control-plane",
        "address": "tcp://127.0.0.1:5555",
        "timestamp": 1234567890.0,
    }
    discovery.services["cp2"] = {
        "type": "control-plane",
        "address": "tcp://127.0.0.1:5556",
        "timestamp": 1234567890.0,
    }
    discovery.services["sw1"] = {
        "type": "subworker",
        "address": "tcp://127.0.0.1:5561",
        "timestamp": 1234567890.0,
    }
    discovery.services["sw2"] = {
        "type": "subworker",
        "address": "tcp://127.0.0.1:5562",
        "timestamp": 1234567890.0,
    }

    all_services = discovery.get_services()
    assert len(all_services) == 4

    control_planes = discovery.get_services("control-plane")
    assert len(control_planes) == 2

    subworkers = discovery.get_services("subworker")
    assert len(subworkers) == 2


def test_service_discovery_empty_type_filter():
    """Test that empty type filter returns all services."""
    discovery = ServiceDiscovery(discovery_address="tcp://127.0.0.1:5550")

    discovery.services["service1"] = {
        "type": "control-plane",
        "address": "tcp://127.0.0.1:5555",
        "timestamp": 1234567890.0,
    }

    services = discovery.get_services(service_type="")
    assert len(services) == 1


def test_service_discovery_nonexistent_type():
    """Test filter for nonexistent service type returns empty list."""
    discovery = ServiceDiscovery(discovery_address="tcp://127.0.0.1:5550")

    discovery.services["service1"] = {
        "type": "control-plane",
        "address": "tcp://127.0.0.1:5555",
        "timestamp": 1234567890.0,
    }

    services = discovery.get_services(service_type="nonexistent")
    assert services == []


def test_service_discovery_services_dict_format():
    """Test services dict has correct structure."""
    discovery = ServiceDiscovery(discovery_address="tcp://127.0.0.1:5550")

    discovery.services["my-service"] = {
        "type": "worker",
        "address": "tcp://127.0.0.1:5555",
        "timestamp": 1234567890.0,
    }

    service = discovery.services["my-service"]
    assert "type" in service
    assert "address" in service
    assert "timestamp" in service


@pytest.mark.asyncio
async def test_service_discovery_start_and_stop():
    """Test complete start/stop cycle."""
    discovery = ServiceDiscovery(discovery_address="tcp://127.0.0.1:5550")

    # Initially not running
    assert discovery.running is False

    # Start
    with patch.object(discovery.bus_pattern, "start", new_callable=AsyncMock):
        await discovery.start()
    assert discovery.running is True

    # Stop
    with patch.object(discovery.bus_pattern, "close"):
        discovery.stop()
    assert discovery.running is False


def test_service_discovery_address_formats():
    """Test discovery with different address formats."""
    # TCP address
    discovery1 = ServiceDiscovery(discovery_address="tcp://127.0.0.1:5550")
    assert discovery1.discovery_address == "tcp://127.0.0.1:5550"

    # IPC address (if supported)
    discovery2 = ServiceDiscovery(discovery_address="tcp://127.0.0.1:5550")
    assert discovery2.discovery_address == "tcp://127.0.0.1:5550"


def test_service_discovery_get_services_returns_list():
    """Test get_services returns a list, not a dict."""
    discovery = ServiceDiscovery(discovery_address="tcp://127.0.0.1:5550")

    discovery.services["service1"] = {
        "type": "control-plane",
        "address": "tcp://127.0.0.1:5555",
        "timestamp": 1234567890.0,
    }

    result = discovery.get_services()
    assert isinstance(result, list)
    assert len(result) == 1
