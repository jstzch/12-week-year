"""12-Week Year - Backend API"""
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db, init_db
from models import Task
from schemas import Task, TaskCreate, TaskUpdate, TaskStats
import crud

app = FastAPI()


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


# CRUD Endpoints

@app.post("/api/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    return crud.create_task(db, task)


@app.get("/api/tasks", response_model=List[Task])
def read_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all tasks."""
    return crud.get_tasks(db, skip=skip, limit=limit)


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
