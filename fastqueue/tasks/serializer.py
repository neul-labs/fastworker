"""Task serialization for FastQueue."""
import json
import pickle
from typing import Any
from enum import Enum

class SerializationFormat(str, Enum):
    """Serialization formats."""
    JSON = "json"
    PICKLE = "pickle"

class TaskSerializer:
    """Serializer for tasks and results."""
    
    @staticmethod
    def serialize(data: Any, format: SerializationFormat = SerializationFormat.JSON) -> bytes:
        """Serialize data to bytes."""
        if format == SerializationFormat.JSON:
            return json.dumps(data, default=str).encode('utf-8')
        elif format == SerializationFormat.PICKLE:
            return pickle.dumps(data)
        else:
            raise ValueError(f"Unsupported serialization format: {format}")
    
    @staticmethod
    def deserialize(data: bytes, format: SerializationFormat = SerializationFormat.JSON) -> Any:
        """Deserialize bytes to data."""
        if format == SerializationFormat.JSON:
            return json.loads(data.decode('utf-8'))
        elif format == SerializationFormat.PICKLE:
            return pickle.loads(data)
        else:
            raise ValueError(f"Unsupported serialization format: {format}")