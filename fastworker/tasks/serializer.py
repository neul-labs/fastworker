"""Task serialization for FastWorker."""

import json
import pickle
import warnings
from typing import Any
from enum import Enum


class SerializationFormat(str, Enum):
    """Serialization formats.

    Attributes:
        JSON: JSON serialization (safe, recommended for untrusted networks).
        PICKLE: Python pickle serialization (NOT secure, use only on trusted networks).
    """

    JSON = "json"
    PICKLE = "pickle"


class TaskSerializer:
    """Serializer for tasks and results.

    .. warning::
        Using ``SerializationFormat.PICKLE`` is a security risk. The pickle
        module is NOT secure and can execute arbitrary code during deserialization.
        Only use PICKLE when:
        - All workers and clients are on a trusted network
        - You trust all parties submitting tasks
        For untrusted networks, use ``SerializationFormat.JSON`` instead.
    """

    @staticmethod
    def serialize(
        data: Any, format: SerializationFormat = SerializationFormat.JSON
    ) -> bytes:
        """Serialize data to bytes.

        Args:
            data: Data to serialize.
            format: Serialization format to use.

        Returns:
            Serialized data as bytes.
        """
        if format == SerializationFormat.JSON:
            return json.dumps(data, default=str).encode("utf-8")
        elif format == SerializationFormat.PICKLE:
            warnings.warn(
                "PICKLE serialization is NOT secure and can execute arbitrary code. "
                "Consider using JSON serialization for untrusted networks.",
                SecurityWarning,
                stacklevel=2,
            )
            return pickle.dumps(data)
        else:
            raise ValueError(f"Unsupported serialization format: {format}")

    @staticmethod
    def deserialize(
        data: bytes, format: SerializationFormat = SerializationFormat.JSON
    ) -> Any:
        """Deserialize bytes to data.

        Args:
            data: Serialized data as bytes.
            format: Serialization format used.

        Returns:
            Deserialized data.

        .. warning::
            Deserializing untrusted data with PICKLE can lead to code execution.
        """
        if format == SerializationFormat.JSON:
            return json.loads(data.decode("utf-8"))
        elif format == SerializationFormat.PICKLE:
            warnings.warn(
                "PICKLE deserialization is NOT secure. "
                "Only deserialize data from trusted sources.",
                SecurityWarning,
                stacklevel=2,
            )
            return pickle.loads(data)
        else:
            raise ValueError(f"Unsupported serialization format: {format}")
