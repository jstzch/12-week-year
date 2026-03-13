"""12-Week Year - Backend API"""
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import get_db, init_db
from models import Task
from schemas import Task, TaskCreate, TaskUpdate, TaskStats, ExecutionScore, WeeklyReport
from schemas import Goal, GoalCreate, GoalUpdate, GoalProgress
import crud

app = FastAPI()


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """Initialize database on startup."""
    init_db()


@app.get("/")
def root():
    """Root endpoint - Hello API"""
    return {"message": "Hello from 12-Week Year API!", "status": "ok"}


@app.get("/api/hello")
def hello():
    """Hello endpoint"""
    return {"message": "Hello, World!"}


# ==================== Goal Endpoints ====================

@app.post("/api/goals", response_model=Goal, status_code=status.HTTP_201_CREATED)
def create_goal(goal: GoalCreate, db: Session = Depends(get_db)):
    """Create a new goal."""
    db_goal = crud.create_goal(db, goal)
    db_goal.week_number = crud.calculate_week_number(db_goal.start_date)
    return db_goal


@app.get("/api/goals", response_model=List[Goal])
def read_goals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all goals."""
    goals = crud.get_goals(db, skip=skip, limit=limit)
    # Add week_number to each goal
    for goal in goals:
        goal.week_number = crud.calculate_week_number(goal.start_date)
    return goals


@app.get("/api/goals/{goal_id}", response_model=Goal)
def read_goal(goal_id: int, db: Session = Depends(get_db)):
    """Get a single goal by ID."""
    db_goal = crud.get_goal(db, goal_id)
    if db_goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    db_goal.week_number = crud.calculate_week_number(db_goal.start_date)
    return db_goal


@app.put("/api/goals/{goal_id}", response_model=Goal)
def update_goal(goal_id: int, goal_update: GoalUpdate, db: Session = Depends(get_db)):
    """Update a goal."""
    db_goal = crud.update_goal(db, goal_id, goal_update)
    if db_goal is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    db_goal.week_number = crud.calculate_week_number(db_goal.start_date)
    return db_goal


@app.delete("/api/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: int, db: Session = Depends(get_db)):
    """Delete a goal and its associated tasks."""
    success = crud.delete_goal(db, goal_id)
    if not success:
        raise HTTPException(status_code=404, detail="Goal not found")


@app.get("/api/goals/{goal_id}/progress", response_model=GoalProgress)
def get_goal_progress(goal_id: int, db: Session = Depends(get_db)):
    """Get progress for a specific goal."""
    progress = crud.get_goal_progress(db, goal_id)
    if progress is None:
        raise HTTPException(status_code=404, detail="Goal not found")
    return progress


# ==================== Task Endpoints ====================

@app.post("/api/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    return crud.create_task(db, task)


@app.get("/api/tasks", response_model=List[Task])
def read_tasks(skip: int = 0, limit: int = 100, goal_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get all tasks, optionally filtered by goal_id."""
    return crud.get_tasks(db, skip=skip, limit=limit, goal_id=goal_id)


@app.get("/api/tasks/stats", response_model=TaskStats)
def get_task_stats(db: Session = Depends(get_db)):
    """Get task statistics."""
    return crud.get_task_stats(db)


@app.get("/api/tasks/{task_id}", response_model=Task)
def read_task(task_id: int, db: Session = Depends(get_db)):
    """Get a single task by ID."""
    db_task = crud.get_task(db, task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@app.put("/api/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task_update: TaskUpdate, db: Session = Depends(get_db)):
    """Update a task."""
    db_task = crud.update_task(db, task_id, task_update)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@app.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task."""
    success = crud.delete_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")


# ==================== Stats Endpoints ====================

@app.get("/api/score", response_model=ExecutionScore)
def get_execution_score(db: Session = Depends(get_db)):
    """Get execution score."""
    return crud.get_execution_score(db)


@app.get("/api/weekly", response_model=WeeklyReport)
def get_weekly_report(db: Session = Depends(get_db)):
    """Get weekly report."""
    return crud.get_weekly_report(db)
