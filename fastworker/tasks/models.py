"""Task models for FastWorker."""

import uuid
from typing import Any, Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Task status — managed by TaskStateMachine."""

    PENDING = "pending"
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    ASSIGNED = "assigned"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class CallbackInfo(BaseModel):
    """Callback information for task completion notifications."""

    address: str
    data: Optional[dict[str, Any]] = None


class Task(BaseModel):
    """Task model. Status transitions are enforced by TaskStateMachine at runtime."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = Field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    callback: Optional[CallbackInfo] = None

    # Retry policy
    retry_count: int = 0
    max_retries: int = 0
    retry_delay: float = 60.0
    retry_backoff: float = 2.0
    retry_backoff_max: float = 3600.0

    # Scheduling
    timeout: Optional[float] = None
    eta: Optional[datetime] = None

    # Routing
    assigned_worker: Optional[str] = None


class TaskResult(BaseModel):
    """Task result model."""

    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    callback: Optional[CallbackInfo] = None
