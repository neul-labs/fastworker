"""Test cases for FastQueue serializer."""
import pytest
import json
import pickle
from fastqueue.tasks.serializer import TaskSerializer, SerializationFormat


def test_json_serialization():
    """Test JSON serialization and deserialization."""
    data = {
        "name": "test_task",
        "args": [1, 2, 3],
        "kwargs": {"key": "value"},
        "priority": "normal"
    }

    # Serialize
    serialized = TaskSerializer.serialize(data, SerializationFormat.JSON)
    assert isinstance(serialized, bytes)

    # Deserialize
    deserialized = TaskSerializer.deserialize(serialized, SerializationFormat.JSON)
    assert deserialized == data


def test_pickle_serialization():
    """Test Pickle serialization and deserialization."""
    data = {
        "name": "test_task",
        "args": (1, 2, 3),
        "kwargs": {"key": "value"},
        "complex_object": {"nested": {"data": [1, 2, 3]}}
    }

    # Serialize
    serialized = TaskSerializer.serialize(data, SerializationFormat.PICKLE)
    assert isinstance(serialized, bytes)

    # Deserialize
    deserialized = TaskSerializer.deserialize(serialized, SerializationFormat.PICKLE)
    assert deserialized == data


def test_json_with_complex_data():
    """Test JSON serialization with complex but JSON-compatible data."""
    data = {
        "task_id": "12345-abcde",
        "result": {
            "status": "success",
            "data": [
                {"id": 1, "name": "Item 1"},
                {"id": 2, "name": "Item 2"}
            ],
            "metadata": {
                "count": 2,
                "timestamp": "2024-09-05T10:30:00Z"
            }
        }
    }

    serialized = TaskSerializer.serialize(data, SerializationFormat.JSON)
    deserialized = TaskSerializer.deserialize(serialized, SerializationFormat.JSON)
    assert deserialized == data


def test_pickle_with_builtin_objects():
    """Test Pickle serialization with builtin objects."""
    # Use builtin objects that can be pickled
    data = {
        "name": "custom_task",
        "custom_arg": {"nested": "value"},
        "list_arg": [1, 2, 3, {"inner": "data"}],
        "tuple_arg": (1, "string", [4, 5, 6])
    }

    serialized = TaskSerializer.serialize(data, SerializationFormat.PICKLE)
    deserialized = TaskSerializer.deserialize(serialized, SerializationFormat.PICKLE)

    assert deserialized == data
    assert isinstance(deserialized["tuple_arg"], tuple)


def test_serialization_format_enum():
    """Test SerializationFormat enum values."""
    assert SerializationFormat.JSON.value == "json"
    assert SerializationFormat.PICKLE.value == "pickle"


def test_empty_data_serialization():
    """Test serialization of empty data structures."""
    empty_dict = {}
    empty_list = []

    # JSON
    json_serialized = TaskSerializer.serialize(empty_dict, SerializationFormat.JSON)
    json_deserialized = TaskSerializer.deserialize(json_serialized, SerializationFormat.JSON)
    assert json_deserialized == empty_dict

    # Pickle
    pickle_serialized = TaskSerializer.serialize(empty_list, SerializationFormat.PICKLE)
    pickle_deserialized = TaskSerializer.deserialize(pickle_serialized, SerializationFormat.PICKLE)
    assert pickle_deserialized == empty_list


def test_none_value_serialization():
    """Test serialization of None values."""
    data = {"value": None, "other": "not_none"}

    # JSON
    json_serialized = TaskSerializer.serialize(data, SerializationFormat.JSON)
    json_deserialized = TaskSerializer.deserialize(json_serialized, SerializationFormat.JSON)
    assert json_deserialized == data

    # Pickle
    pickle_serialized = TaskSerializer.serialize(data, SerializationFormat.PICKLE)
    pickle_deserialized = TaskSerializer.deserialize(pickle_serialized, SerializationFormat.PICKLE)
    assert pickle_deserialized == data


def test_large_data_serialization():
    """Test serialization of larger data structures."""
    large_data = {
        "large_list": list(range(1000)),
        "large_dict": {f"key_{i}": f"value_{i}" for i in range(100)},
        "nested": {
            "level1": {
                "level2": {
                    "level3": "deep_value"
                }
            }
        }
    }

    # Test both formats
    for format_type in [SerializationFormat.JSON, SerializationFormat.PICKLE]:
        serialized = TaskSerializer.serialize(large_data, format_type)
        deserialized = TaskSerializer.deserialize(serialized, format_type)
        assert deserialized == large_data