"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional, Annotated, List
from pydantic import BaseModel, ConfigDict, computed_field


# ==================== Goal Schemas ====================

class GoalBase(BaseModel):
    """Base goal schema."""
    name: str
    start_date: Optional[datetime] = None
    weekly_plan: Optional[int] = 0  # Weekly planned tasks


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


class ScoreHistory(BaseModel):
    """Schema for score history entry."""
    week_number: int
    execution_score: int
    
    model_config = ConfigDict(populate_by_name=True)


class ScoreHistoryResponse(BaseModel):
    """Schema for score history response."""
    goal_id: int
    goal_name: str
    scores: List[ScoreHistory]
    target_score: int = 85
    
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
    indicator_type: str = "lead"  # "lead" = controllable action, "lag" = result


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


class WeeklyPlanUpdate(BaseModel):
    """Schema for updating weekly plan."""
    weekly_plan: int


class WeeklyProgress(BaseModel):
    """Schema for weekly progress."""
    goal_id: int
    goal_name: str
    week_number: int
    weekly_plan: int  # Planned number of tasks for this week
    completed_this_week: int  # Actual completed tasks this week
    completion_rate: float  # Completion rate (actual / plan * 100)
    
    model_config = ConfigDict(populate_by_name=True)


class IndicatorStats(BaseModel):
    """Schema for lead/lag indicator statistics."""
    lead_total: int
    lead_completed: int
    lead_completion_rate: float
    lag_total: int
    lag_completed: int
    lag_completion_rate: float
    
    model_config = ConfigDict(populate_by_name=True)


# ==================== WAM Schemas ====================

class WAMBase(BaseModel):
    """Base WAM schema."""
    goal_id: Optional[int] = None
    week_number: int
    execution_score: int  # 0-100
    notes: Optional[str] = None
    plan_next: Optional[str] = None


class WAMCreate(WAMBase):
    """Schema for creating a WAM."""
    pass


class WAMUpdate(BaseModel):
    """Schema for updating a WAM."""
    goal_id: Optional[int] = None
    week_number: Optional[int] = None
    execution_score: Optional[int] = None
    notes: Optional[str] = None
    plan_next: Optional[str] = None


class WAM(WAMBase):
    """Schema for WAM response."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==================== Dashboard Schemas ====================

class GoalCard(BaseModel):
    """Schema for goal card in dashboard."""
    id: int
    name: str
    week_number: int
    total_tasks: int
    completed_tasks: int
    score: float
    is_excellent: bool
    
    model_config = ConfigDict(populate_by_name=True)


class DashboardStats(BaseModel):
    """Schema for dashboard statistics."""
    total_goals: int
    leading_indicator_tasks: int
    lagging_indicator_tasks: int
    weekly_execution_score: float
    is_excellent: bool
    
    model_config = ConfigDict(populate_by_name=True)


class DashboardResponse(BaseModel):
    """Schema for dashboard response."""
    stats: DashboardStats
    goals: List[GoalCard]
    
    model_config = ConfigDict(populate_by_name=True)
