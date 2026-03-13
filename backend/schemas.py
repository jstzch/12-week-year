"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional, Annotated
from pydantic import BaseModel, ConfigDict, computed_field


# ==================== Goal Schemas ====================

class GoalBase(BaseModel):
    """Base goal schema."""
    name: str
    start_date: Optional[datetime] = None


class GoalCreate(GoalBase):
    """Schema for creating a goal."""
    pass


class GoalUpdate(BaseModel):
    """Schema for updating a goal."""
    name: Optional[str] = None
    start_date: Optional[datetime] = None


class Goal(GoalBase):
    """Schema for goal response."""
    id: int
    week_number: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class GoalProgress(BaseModel):
    """Schema for goal progress."""
    goal_id: int
    goal_name: str
    week_number: int
    total_tasks: int
    completed_tasks: int
    score: float
    is_excellent: bool
    
    model_config = ConfigDict(populate_by_name=True)


# ==================== Task Schemas ====================

class TaskBase(BaseModel):
    """Base task schema."""
    title: str
    description: Optional[str] = None
    status: str = "pending"  # pending, in_progress, completed
    priority: str = "medium"  # low, medium, high
    due_date: Optional[datetime] = None
    completed: bool = False  # Backward compatibility
    goal_id: Optional[int] = None


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
    goal_id: Optional[int] = None


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


class ExecutionScore(BaseModel):
    """Schema for execution score."""
    score: float
    completed: int
    total: int
    is_excellent: bool
    
    model_config = ConfigDict(populate_by_name=True)


class WeeklyReport(BaseModel):
    """Schema for weekly report."""
    tasks_this_week: int
    completed_this_week: int
    completion_rate: float
    
    model_config = ConfigDict(populate_by_name=True)
