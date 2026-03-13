"""Tests for CRUD operations."""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta

from main import app
from database import Base, get_db
from models import Task
from schemas import TaskCreate, TaskUpdate, TaskStats
import crud


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    """Create a test client."""
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


# ==================== Unit Tests ====================

class TestCrudOperations:
    """Unit tests for CRUD operations."""

    def test_create_task(self, db_session):
        """Test creating a task."""
        task_data = TaskCreate(title="Test Task", description="Test Description")
        task = crud.create_task(db_session, task_data)
        
        assert task.id is not None
        assert task.title == "Test Task"
        assert task.description == "Test Description"
        assert task.completed is False
        assert task.status == "pending"  # Default status
        assert task.priority == "medium"  # Default priority

    def test_create_task_with_new_fields(self, db_session):
        """Test creating a task with new fields."""
        due = datetime.utcnow() + timedelta(days=1)
        task_data = TaskCreate(
            title="Priority Task",
            description="High priority",
            status="in_progress",
            priority="high",
            due_date=due
        )
        task = crud.create_task(db_session, task_data)
        
        assert task.status == "in_progress"
        assert task.priority == "high"
        assert task.due_date is not None

    def test_get_tasks(self, db_session):
        """Test getting all tasks."""
        # Create some tasks
        task1 = crud.create_task(db_session, TaskCreate(title="Task 1"))
        task2 = crud.create_task(db_session, TaskCreate(title="Task 2"))
        
        tasks = crud.get_tasks(db_session)
        
        assert len(tasks) == 2
        assert tasks[0].title == "Task 1"
        assert tasks[1].title == "Task 2"

    def test_get_task(self, db_session):
        """Test getting a single task."""
        created_task = crud.create_task(db_session, TaskCreate(title="Test"))
        retrieved_task = crud.get_task(db_session, created_task.id)
        
        assert retrieved_task is not None
        assert retrieved_task.id == created_task.id
        assert retrieved_task.title == "Test"

    def test_get_task_not_found(self, db_session):
        """Test getting a non-existent task."""
        task = crud.get_task(db_session, 999)
        assert task is None

    def test_update_task(self, db_session):
        """Test updating a task."""
        created_task = crud.create_task(db_session, TaskCreate(title="Original"))
        
        update_data = TaskUpdate(title="Updated", completed=True, status="completed")
        updated_task = crud.update_task(db_session, created_task.id, update_data)
        
        assert updated_task.title == "Updated"
        assert updated_task.completed is True
        assert updated_task.status == "completed"

    def test_update_task_with_priority(self, db_session):
        """Test updating task priority."""
        created_task = crud.create_task(db_session, TaskCreate(title="Task"))
        
        update_data = TaskUpdate(priority="high", status="in_progress")
        updated_task = crud.update_task(db_session, created_task.id, update_data)
        
        assert updated_task.priority == "high"
        assert updated_task.status == "in_progress"

    def test_update_task_partial(self, db_session):
        """Test partial update of a task."""
        created_task = crud.create_task(db_session, TaskCreate(title="Original", description="Desc"))
        
        update_data = TaskUpdate(title="New Title")
        updated_task = crud.update_task(db_session, created_task.id, update_data)
        
        assert updated_task.title == "New Title"
        assert updated_task.description == "Desc"  # Unchanged

    def test_update_task_not_found(self, db_session):
        """Test updating a non-existent task."""
        result = crud.update_task(db_session, 999, TaskUpdate(title="Test"))
        assert result is None

    def test_delete_task(self, db_session):
        """Test deleting a task."""
        created_task = crud.create_task(db_session, TaskCreate(title="To Delete"))
        task_id = created_task.id
        
        success = crud.delete_task(db_session, task_id)
        assert success is True
        
        deleted_task = crud.get_task(db_session, task_id)
        assert deleted_task is None

    def test_delete_task_not_found(self, db_session):
        """Test deleting a non-existent task."""
        success = crud.delete_task(db_session, 999)
        assert success is False

    def test_get_task_stats_empty(self, db_session):
        """Test statistics with no tasks."""
        stats = crud.get_task_stats(db_session)
        
        assert stats.total == 0
        assert stats.completed == 0
        assert stats.in_progress == 0
        assert stats.pending == 0
        assert stats.overdue == 0

    def test_get_task_stats(self, db_session):
        """Test task statistics."""
        # Create tasks with different statuses
        crud.create_task(db_session, TaskCreate(title="Pending Task", status="pending"))
        crud.create_task(db_session, TaskCreate(title="In Progress Task", status="in_progress"))
        crud.create_task(db_session, TaskCreate(title="Completed Task", status="completed"))
        crud.create_task(db_session, TaskCreate(title="Completed Task 2", completed=True))
        
        # Create overdue task
        overdue_task = TaskCreate(title="Overdue Task", status="pending")
        db_task = crud.create_task(db_session, overdue_task)
        db_task.due_date = datetime.utcnow() - timedelta(days=1)
        db_session.commit()
        
        stats = crud.get_task_stats(db_session)
        
        assert stats.total == 5
        assert stats.pending == 2  # Pending + overdue
        assert stats.in_progress == 1
        assert stats.completed == 2
        assert stats.overdue == 1

    def test_backward_compatibility_completed(self, db_session):
        """Test backward compatibility - completed field."""
        created_task = crud.create_task(db_session, TaskCreate(title="Task"))
        
        # Update using old completed field
        update_data = TaskUpdate(completed=True)
        updated_task = crud.update_task(db_session, created_task.id, update_data)
        
        # Should sync status with completed
        assert updated_task.completed is True
        assert updated_task.status == "completed"


# ==================== Integration Tests (API Tests) ====================

class TestAPIEndpoints:
    """Integration tests for API endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "Hello from 12-Week Year API!"

    def test_hello_endpoint(self, client):
        """Test hello endpoint."""
        response = client.get("/api/hello")
        assert response.status_code == 200
        assert response.json()["message"] == "Hello, World!"

    def test_create_task_api(self, client):
        """Test creating a task via API."""
        response = client.post(
            "/api/tasks",
            json={"title": "API Task", "description": "Created via API"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "API Task"
        assert data["description"] == "Created via API"
        assert data["completed"] is False
        assert data["status"] == "pending"  # Default
        assert data["priority"] == "medium"  # Default

    def test_create_task_with_new_fields_api(self, client):
        """Test creating task with new fields via API."""
        due_date = (datetime.utcnow() + timedelta(days=1)).isoformat()
        response = client.post(
            "/api/tasks",
            json={
                "title": "API Task",
                "status": "in_progress",
                "priority": "high",
                "due_date": due_date
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["priority"] == "high"

    def test_get_all_tasks_api(self, client):
        """Test getting all tasks via API."""
        # Create tasks first
        client.post("/api/tasks", json={"title": "Task 1"})
        client.post("/api/tasks", json={"title": "Task 2"})
        
        response = client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_single_task_api(self, client):
        """Test getting a single task via API."""
        create_response = client.post("/api/tasks", json={"title": "Test Task"})
        task_id = create_response.json()["id"]
        
        response = client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Test Task"

    def test_get_single_task_not_found_api(self, client):
        """Test getting a non-existent task via API."""
        response = client.get("/api/tasks/999")
        assert response.status_code == 404

    def test_update_task_api(self, client):
        """Test updating a task via API."""
        create_response = client.post("/api/tasks", json={"title": "Original"})
        task_id = create_response.json()["id"]
        
        response = client.put(
            f"/api/tasks/{task_id}",
            json={"title": "Updated", "completed": True, "status": "completed", "priority": "high"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"
        assert data["completed"] is True
        assert data["status"] == "completed"
        assert data["priority"] == "high"

    def test_update_task_not_found_api(self, client):
        """Test updating a non-existent task via API."""
        response = client.put("/api/tasks/999", json={"title": "Test"})
        assert response.status_code == 404

    def test_delete_task_api(self, client):
        """Test deleting a task via API."""
        create_response = client.post("/api/tasks", json={"title": "To Delete"})
        task_id = create_response.json()["id"]
        
        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 204
        
        # Verify it's gone
        get_response = client.get(f"/api/tasks/{task_id}")
        assert get_response.status_code == 404

    def test_delete_task_not_found_api(self, client):
        """Test deleting a non-existent task via API."""
        response = client.delete("/api/tasks/999")
        assert response.status_code == 404

    def test_get_task_stats_api(self, client):
        """Test getting task statistics via API."""
        # Create tasks
        client.post("/api/tasks", json={"title": "Task 1", "status": "pending"})
        client.post("/api/tasks", json={"title": "Task 2", "status": "in_progress"})
        client.post("/api/tasks", json={"title": "Task 3", "status": "completed"})
        
        response = client.get("/api/tasks/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["pending"] == 1
        assert data["in_progress"] == 1
        assert data["completed"] == 1

    def test_get_task_stats_empty_api(self, client):
        """Test getting task statistics when no tasks exist."""
        response = client.get("/api/tasks/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_is_overdue_property(self, client):
        """Test is_overdue property in response."""
        # Create overdue task
        due_date = (datetime.utcnow() - timedelta(days=1)).isoformat()
        response = client.post(
            "/api/tasks",
            json={"title": "Overdue Task", "due_date": due_date, "status": "pending"}
        )
        data = response.json()
        
        # is_overdue should be True for pending task past due_date
        assert data["is_overdue"] is True

    def test_is_overdue_completed(self, client):
        """Test is_overdue is False for completed tasks."""
        due_date = (datetime.utcnow() - timedelta(days=1)).isoformat()
        response = client.post(
            "/api/tasks",
            json={"title": "Completed Overdue", "due_date": due_date, "status": "completed"}
        )
        data = response.json()
        
        # is_overdue should be False for completed tasks
        assert data["is_overdue"] is False

    def test_backward_compatibility_api(self, client):
        """Test backward compatibility with existing API."""
        # Using old API format (without new fields)
        response = client.post(
            "/api/tasks",
            json={"title": "Old Format Task", "completed": True}
        )
        data = response.json()
        
        # Should still work and have default values
        assert data["title"] == "Old Format Task"
        assert data["completed"] is True
        assert data["status"] == "completed"  # Synced from completed
