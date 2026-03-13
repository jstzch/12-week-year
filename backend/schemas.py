"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TaskBase(BaseModel):
    """Base task schema."""
    title: str
    description: Optional[str] = None
    completed: bool = False


class TaskCreate(TaskBase):
    """Schema for creating a task."""
    pass


class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None


class Task(TaskBase):
    """Schema for task response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
