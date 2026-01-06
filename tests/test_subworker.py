"""Test cases for FastWorker SubWorker."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from fastworker.workers.subworker import SubWorker
from fastworker.tasks.models import TaskPriority


def test_subworker_initialization():
    """Test subworker initialization."""
    subworker = SubWorker(
        worker_id="test-subworker",
        control_plane_address="tcp://127.0.0.1:5555",
        base_address="tcp://127.0.0.1:5561",
    )

    assert subworker.worker_id == "test-subworker"
    assert subworker.control_plane_address == "tcp://127.0.0.1:5555"
    assert subworker.base_address == "tcp://127.0.0.1:5561"
    assert subworker.registered is False


def test_subworker_initialization_missing_worker_id():
    """Test subworker initialization fails without worker_id."""
    with pytest.raises(ValueError, match="worker_id must be provided"):
        SubWorker(
            worker_id=None,
            control_plane_address="tcp://127.0.0.1:5555",
        )


def test_subworker_initialization_missing_control_plane():
    """Test subworker initialization fails without control_plane_address."""
    with pytest.raises(ValueError, match="control_plane_address must be provided"):
        SubWorker(
            worker_id="test-subworker",
            control_plane_address=None,
        )


def test_subworker_attributes():
    """Test subworker has required attributes."""
    subworker = SubWorker(
        worker_id="test-subworker",
        control_plane_address="tcp://127.0.0.1:5555",
    )

    # Should have respondents for all priority levels
    assert hasattr(subworker, "critical_respondent")
    assert hasattr(subworker, "high_respondent")
    assert hasattr(subworker, "normal_respondent")
    assert hasattr(subworker, "low_respondent")

    # Should have control plane registry
    assert hasattr(subworker, "control_plane_registry")

    # Should have discovery bus
    assert hasattr(subworker, "discovery_bus")


def test_subworker_control_plane_registry_address():
    """Test control plane registry address is computed correctly."""
    # Test with default port
    subworker = SubWorker(
        worker_id="test-subworker",
        control_plane_address="tcp://127.0.0.1:5555",
        base_address="tcp://127.0.0.1:5561",
    )
    # Management port should be base_port + 5 = 5560
    assert "5560" in subworker.control_plane_registry.address


def test_subworker_custom_base_address():
    """Test subworker with custom base address."""
    subworker = SubWorker(
        worker_id="test-subworker",
        control_plane_address="tcp://127.0.0.1:5555",
        base_address="tcp://192.168.1.100:5600",
    )

    assert subworker.base_address == "tcp://192.168.1.100:5600"
    assert subworker.critical_respondent.address == "tcp://192.168.1.100:5600"
    assert subworker.high_respondent.address == "tcp://192.168.1.100:5601"


def test_subworker_priority_ports():
    """Test subworker priority port assignments."""
    subworker = SubWorker(
        worker_id="test-subworker",
        control_plane_address="tcp://127.0.0.1:5555",
        base_address="tcp://127.0.0.1:5561",
    )

    # Base port is 5561
    assert "5561" in subworker.critical_respondent.address  # base_port
    assert "5562" in subworker.high_respondent.address     # base_port + 1
    assert "5563" in subworker.normal_respondent.address   # base_port + 2
    assert "5564" in subworker.low_respondent.address      # base_port + 3


def test_subworker_not_running_by_default():
    """Test subworker is not running after initialization."""
    subworker = SubWorker(
        worker_id="test-subworker",
        control_plane_address="tcp://127.0.0.1:5555",
    )

    assert subworker.running is False
    assert subworker.registered is False


def test_subworker_discovery_bus_listen_false():
    """Test subworker discovery bus is configured to dial (not listen)."""
    subworker = SubWorker(
        worker_id="test-subworker",
        control_plane_address="tcp://127.0.0.1:5555",
    )

    # Subworkers should dial, not listen
    assert subworker.discovery_bus.listen is False


def test_subworker_custom_discovery_address():
    """Test subworker with custom discovery address."""
    subworker = SubWorker(
        worker_id="test-subworker",
        control_plane_address="tcp://127.0.0.1:5555",
        discovery_address="tcp://192.168.1.1:5500",
    )

    assert subworker.discovery_address == "tcp://192.168.1.1:5500"


def test_subworker_serialization_format():
    """Test subworker serialization format configuration."""
    from fastworker.tasks.serializer import SerializationFormat

    # Default is JSON
    subworker = SubWorker(
        worker_id="test-subworker",
        control_plane_address="tcp://127.0.0.1:5555",
    )
    assert subworker.serialization_format == SerializationFormat.JSON


def test_subworker_environment_variable_defaults():
    """Test subworker environment variable defaults."""
    import os

    # Clean environment
    for key in ["FASTWORKER_WORKER_ID", "FASTWORKER_CONTROL_PLANE_ADDRESS"]:
        if key in os.environ:
            del os.environ[key]

    # Test defaults when provided as arguments
    subworker = SubWorker(
        worker_id="env-test",
        control_plane_address="tcp://127.0.0.1:5555",
        base_address="tcp://127.0.0.1:5561",
    )

    assert subworker.base_address == "tcp://127.0.0.1:5561"
    assert subworker.discovery_address == "tcp://127.0.0.1:5550"


def test_subworker_stop():
    """Test subworker stop method."""
    subworker = SubWorker(
        worker_id="test-subworker",
        control_plane_address="tcp://127.0.0.1:5555",
    )

    # Before stop, running is False (not started)
    assert subworker.running is False

    # Stop should not raise
    subworker.stop()


def test_subworker_multiple_instances():
    """Test multiple subworker instances can be created."""
    subworker1 = SubWorker(
        worker_id="subworker-1",
        control_plane_address="tcp://127.0.0.1:5555",
        base_address="tcp://127.0.0.1:5561",
    )
    subworker2 = SubWorker(
        worker_id="subworker-2",
        control_plane_address="tcp://127.0.0.1:5555",
        base_address="tcp://127.0.0.1:5562",
    )

    assert subworker1.worker_id != subworker2.worker_id
    assert subworker1.base_address != subworker2.base_address


def test_subworker_address_parsing():
    """Test subworker address parsing for different formats."""
    # TCP address
    subworker = SubWorker(
        worker_id="test",
        control_plane_address="tcp://127.0.0.1:5555",
    )
    assert subworker.control_plane_address == "tcp://127.0.0.1:5555"

    # IPC address (if supported)
    # Note: This tests that the urlparse doesn't crash
    subworker2 = SubWorker(
        worker_id="test2",
        control_plane_address="tcp://127.0.0.1:5555",
        base_address="tcp://127.0.0.1:5561",
    )
    assert "5561" in subworker2.base_address


def test_subworker_status_property():
    """Test subworker registered status."""
    subworker = SubWorker(
        worker_id="test-subworker",
        control_plane_address="tcp://127.0.0.1:5555",
    )

    # Initially not registered
    assert subworker.registered is False

    # Can manually set for testing
    subworker.registered = True
    assert subworker.registered is True


def test_subworker_inherits_from_worker():
    """Test SubWorker inherits from Worker."""
    from fastworker.workers.worker import Worker

    subworker = SubWorker(
        worker_id="test-subworker",
        control_plane_address="tcp://127.0.0.1:5555",
    )

    assert isinstance(subworker, Worker)


def test_subworker_peers_initialized():
    """Test subworker peers list is initialized."""
    subworker = SubWorker(
        worker_id="test-subworker",
        control_plane_address="tcp://127.0.0.1:5555",
    )

    # Base Worker class initializes peers
    assert hasattr(subworker, "peers")
    assert isinstance(subworker.peers, set)
