"""CRUD operations for Task model."""
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from models import Task
from schemas import TaskCreate, TaskUpdate, TaskStats, ExecutionScore, WeeklyReport


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
        completed=task.completed
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_tasks(db: Session, skip: int = 0, limit: int = 100) -> List[Task]:
    """Get all tasks."""
    return db.query(Task).offset(skip).limit(limit).all()


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
