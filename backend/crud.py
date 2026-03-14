"""CRUD operations for Task and Goal models."""
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from models import Task, Goal, WAM
from schemas import TaskCreate, TaskUpdate, TaskStats, ExecutionScore, WeeklyReport, GoalCreate, GoalUpdate, GoalProgress
from schemas import WAMCreate, WAMUpdate, ScoreHistory, ScoreHistoryItem


# ==================== Goal CRUD ====================

def calculate_week_number(start_date: datetime) -> int:
    """Calculate current week number (1-12) from start date."""
    if start_date is None:
        return 1
    now = datetime.utcnow()
    days_elapsed = (now - start_date).days
    week = (days_elapsed // 7) + 1
    return max(1, min(12, week))  # Clamp between 1 and 12


def create_goal(db: Session, goal: GoalCreate) -> Goal:
    """Create a new goal."""
    start_date = goal.start_date or datetime.utcnow()
    db_goal = Goal(
        name=goal.name,
        start_date=start_date
    )
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal


def get_goals(db: Session, skip: int = 0, limit: int = 100) -> List[Goal]:
    """Get all goals."""
    return db.query(Goal).offset(skip).limit(limit).all()


def get_goal(db: Session, goal_id: int) -> Optional[Goal]:
    """Get a single goal by ID."""
    return db.query(Goal).filter(Goal.id == goal_id).first()


def update_goal(db: Session, goal_id: int, goal_update: GoalUpdate) -> Optional[Goal]:
    """Update a goal."""
    db_goal = get_goal(db, goal_id)
    if not db_goal:
        return None
    
    update_data = goal_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_goal, field, value)
    
    db_goal.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_goal)
    return db_goal


def delete_goal(db: Session, goal_id: int) -> bool:
    """Delete a goal and optionally its tasks."""
    db_goal = get_goal(db, goal_id)
    if not db_goal:
        return False
    
    # Delete associated tasks first
    db.query(Task).filter(Task.goal_id == goal_id).delete()
    
    db.delete(db_goal)
    db.commit()
    return True


def get_goal_progress(db: Session, goal_id: int) -> Optional[GoalProgress]:
    """Get progress for a specific goal."""
    db_goal = get_goal(db, goal_id)
    if not db_goal:
        return None
    
    tasks = db.query(Task).filter(Task.goal_id == goal_id).all()
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.status == "completed" or t.completed)
    
    score = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
    week_number = calculate_week_number(db_goal.start_date)
    
    return GoalProgress(
        goal_id=db_goal.id,
        goal_name=db_goal.name,
        week_number=week_number,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        score=round(score, 1),
        is_excellent=score >= 85
    )


# ==================== Task CRUD ====================

def create_task(db: Session, task: TaskCreate) -> Task:
    """Create a new task."""
    # Handle backward compatibility: if completed=True, set status to completed
    status = task.status
    if task.completed and status == "pending":
        status = "completed"
    
    db_task = Task(
        title=task.title,
        description=task.description,
        status=status,
        priority=task.priority,
        due_date=task.due_date,
        completed=task.completed,
        goal_id=task.goal_id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_tasks(db: Session, skip: int = 0, limit: int = 100, goal_id: Optional[int] = None) -> List[Task]:
    """Get all tasks, optionally filtered by goal_id."""
    query = db.query(Task)
    if goal_id is not None:
        query = query.filter(Task.goal_id == goal_id)
    return query.offset(skip).limit(limit).all()


def get_task(db: Session, task_id: int) -> Optional[Task]:
    """Get a single task by ID."""
    return db.query(Task).filter(Task.id == task_id).first()


def update_task(db: Session, task_id: int, task_update: TaskUpdate) -> Optional[Task]:
    """Update a task."""
    db_task = get_task(db, task_id)
    if not db_task:
        return None
    
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)
    
    # Sync status with completed for backward compatibility
    if 'completed' in update_data:
        if update_data['completed']:
            db_task.status = "completed"
        elif db_task.status == "completed":
            db_task.status = "pending"
    
    db_task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int) -> bool:
    """Delete a task."""
    db_task = get_task(db, task_id)
    if not db_task:
        return False
    
    db.delete(db_task)
    db.commit()
    return True


def get_task_stats(db: Session) -> TaskStats:
    """Get task statistics."""
    all_tasks = db.query(Task).all()
    
    total = len(all_tasks)
    completed = sum(1 for t in all_tasks if t.status == "completed" or t.completed)
    in_progress = sum(1 for t in all_tasks if t.status == "in_progress")
    pending = sum(1 for t in all_tasks if t.status == "pending")
    
    # Count overdue tasks (not completed and past due_date)
    now = datetime.utcnow()
    overdue = sum(
        1 for t in all_tasks 
        if t.due_date is not None 
        and t.status != "completed" 
        and not t.completed
        and now > t.due_date
    )
    
    return TaskStats(
        total=total,
        completed=completed,
        in_progress=in_progress,
        pending=pending,
        overdue=overdue
    )


def get_execution_score(db: Session) -> ExecutionScore:
    """Get execution score (completed/total * 100%)."""
    all_tasks = db.query(Task).all()
    
    total = len(all_tasks)
    completed = sum(1 for t in all_tasks if t.status == "completed" or t.completed)
    
    score = (completed / total * 100) if total > 0 else 0.0
    
    return ExecutionScore(
        score=round(score, 1),
        completed=completed,
        total=total,
        is_excellent=score >= 85
    )


def get_weekly_report(db: Session) -> WeeklyReport:
    """Get weekly report."""
    now = datetime.utcnow()
    # Get start of week (Monday)
    from datetime import timedelta
    days_since_monday = now.weekday()
    week_start = now - timedelta(days=days_since_monday)
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get tasks created this week
    tasks_this_week = db.query(Task).filter(
        Task.created_at >= week_start
    ).count()
    
    # Get tasks completed this week
    completed_this_week = db.query(Task).filter(
        Task.updated_at >= week_start,
        (Task.status == "completed") | (Task.completed == True)
    ).count()
    
    completion_rate = (completed_this_week / tasks_this_week * 100) if tasks_this_week > 0 else 0.0
    
    return WeeklyReport(
        tasks_this_week=tasks_this_week,
        completed_this_week=completed_this_week,
        completion_rate=round(completion_rate, 1)
    )


# ==================== WAM CRUD ====================

def create_wam(db: Session, wam: WAMCreate) -> WAM:
    """Create a new WAM record."""
    db_wam = WAM(
        goal_id=wam.goal_id,
        week_number=wam.week_number,
        execution_score=wam.execution_score,
        notes=wam.notes,
        plan_next=wam.plan_next
    )
    db.add(db_wam)
    db.commit()
    db.refresh(db_wam)
    return db_wam


def get_wams(db: Session, skip: int = 0, limit: int = 100, goal_id: Optional[int] = None) -> List[WAM]:
    """Get all WAMs, optionally filtered by goal_id."""
    query = db.query(WAM)
    if goal_id is not None:
        query = query.filter(WAM.goal_id == goal_id)
    return query.order_by(WAM.week_number.desc()).offset(skip).limit(limit).all()


def get_wam(db: Session, wam_id: int) -> Optional[WAM]:
    """Get a single WAM by ID."""
    return db.query(WAM).filter(WAM.id == wam_id).first()


def update_wam(db: Session, wam_id: int, wam_update: WAMUpdate) -> Optional[WAM]:
    """Update a WAM."""
    db_wam = get_wam(db, wam_id)
    if not db_wam:
        return None
    
    update_data = wam_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_wam, field, value)
    
    db_wam.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_wam)
    return db_wam


def delete_wam(db: Session, wam_id: int) -> bool:
    """Delete a WAM."""
    db_wam = get_wam(db, wam_id)
    if not db_wam:
        return False
    
    db.delete(db_wam)
    db.commit()
    return True


def get_wams_by_goal(db: Session, goal_id: int) -> List[WAM]:
    """Get all WAMs for a specific goal."""
    return db.query(WAM).filter(WAM.goal_id == goal_id).order_by(WAM.week_number.desc()).all()


def get_score_history(db: Session, goal_id: int) -> Optional[ScoreHistory]:
    """Get score history for a specific goal."""
    db_goal = get_goal(db, goal_id)
    if not db_goal:
        return None
    
    wams = db.query(WAM).filter(WAM.goal_id == goal_id).order_by(WAM.week_number.asc()).all()
    
    scores = [
        ScoreHistoryItem(
            week_number=wam.week_number,
            execution_score=wam.execution_score,
            created_at=wam.created_at
        )
        for wam in wams
    ]
    
    return ScoreHistory(
        goal_id=goal_id,
        goal_name=db_goal.name,
        scores=scores,
        target_line=85
    )
