"""Database models."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Goal(Base):
    """Goal model for 12-Week Year tracking."""
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    start_date = Column(DateTime, default=datetime.utcnow)
    # Weekly plan: number of tasks planned for the current week
    weekly_plan = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to tasks
    tasks = relationship("Task", back_populates="goal")
    # Relationship to WAMs
    wams = relationship("WAM", back_populates="goal")


class Task(Base):
    """Task model."""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, in_progress, completed
    priority = Column(String, default="medium")  # low, medium, high
    due_date = Column(DateTime, nullable=True)
    completed = Column(Boolean, default=False)  # Backward compatibility
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    # Lead/Lag indicator: "lead" = controllable action, "lag" = result
    indicator_type = Column(String, default="lead")  # "lead" | "lag"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to goal
    goal = relationship("Goal", back_populates="tasks")


class WAM(Base):
    """WAM (Weekly Accountability Meeting) model."""
    __tablename__ = "wams"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    week_number = Column(Integer, nullable=False)
    execution_score = Column(Integer, nullable=False)  # 0-100
    notes = Column(String, nullable=True)
    plan_next = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to goal
    goal = relationship("Goal", back_populates="wams")
