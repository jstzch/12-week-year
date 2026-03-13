"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional, Annotated
from pydantic import BaseModel, ConfigDict, computed_field


class TaskBase(BaseModel):
    """Base task schema."""
    title: str
    description: Optional[str] = None
    status: str = "pending"  # pending, in_progress, completed
    priority: str = "medium"  # low, medium, high
    due_date: Optional[datetime] = None
    completed: bool = False  # Backward compatibility


class TaskCreate(TaskBase):
    """Schema for creating a task."""
    pass


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None  # pending, in_progress, completed
    priority: Optional[str] = None  # low, medium, high
    due_date: Optional[datetime] = None
    completed: Optional[bool] = None


class Task(TaskBase):
    """Schema for task response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if self.due_date is None:
            return False
        if self.status == "completed" or self.completed:
            return False
        return datetime.utcnow() > self.due_date


class TaskStats(BaseModel):
    """Schema for task statistics."""
    total: int
    completed: int
    in_progress: int
    pending: int
    overdue: int
