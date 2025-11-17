"""Task models for FastWorker."""
import uuid
from typing import Any, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime
from pydantic import BaseModel

class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

class TaskStatus(str, Enum):
    """Task status."""
    PENDING = "pending"
    STARTED = "started"
    SUCCESS = "success"
    FAILURE = "failure"

class CallbackInfo(BaseModel):
    """Callback information for task completion notifications."""
    address: str  # NNG address to send callback to
    data: Optional[Dict[str, Any]] = None  # Additional data to send with callback

class Task(BaseModel):
    """Task model."""
    id: str
    name: str
    args: Tuple[Any, ...] = ()
    kwargs: Dict[str, Any] = {}
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    callback: Optional[CallbackInfo] = None  # Callback information
    
    def __init__(self, **data):
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        if 'created_at' not in data:
            data['created_at'] = datetime.now()
        super().__init__(**data)

class TaskResult(BaseModel):
    """Task result model."""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    callback: Optional[CallbackInfo] = None  # Callback information