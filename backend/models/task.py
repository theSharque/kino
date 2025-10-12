"""
Task data models for generator system
"""
from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class TaskStatus(str, Enum):
    """Task status enum"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class TaskBase(BaseModel):
    """Base task model with common fields"""
    name: str = Field(..., min_length=1, max_length=255, description="Task name")
    type: str = Field(..., min_length=1, max_length=100, description="Plugin/module type")
    data: Dict[str, Any] = Field(default_factory=dict, description="Task data for plugin")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name is not empty"""
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Ensure type is not empty"""
        if not v.strip():
            raise ValueError('Type cannot be empty')
        return v.strip()


class TaskCreate(TaskBase):
    """Model for creating a new task"""
    pass


class TaskUpdate(BaseModel):
    """Model for updating an existing task"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[TaskStatus] = None
    progress: Optional[float] = Field(None, ge=0.0, le=100.0)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskResponse(TaskBase):
    """Model for task response"""
    id: int
    status: TaskStatus
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Model for list of tasks response"""
    total: int
    tasks: list[TaskResponse]

