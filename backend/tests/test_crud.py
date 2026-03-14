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
from models import Task, Goal, WAM
from schemas import TaskCreate, TaskUpdate, TaskStats
from schemas import WAMCreate, WAMUpdate
from schemas import GoalCreate
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


# ==================== WAM Unit Tests ====================

class TestWAMCrud:
    """Unit tests for WAM CRUD operations."""

    def test_create_wam(self, db_session):
        """Test creating a WAM record."""
        wam_data = WAMCreate(
            week_number=1,
            execution_score=85,
            notes="Good progress this week",
            plan_next="Focus on task completion"
        )
        wam = crud.create_wam(db_session, wam_data)
        
        assert wam.id is not None
        assert wam.week_number == 1
        assert wam.execution_score == 85
        assert wam.notes == "Good progress this week"
        assert wam.plan_next == "Focus on task completion"

    def test_create_wam_with_goal(self, db_session):
        """Test creating a WAM with a goal."""
        # Create a goal first
        goal = crud.create_goal(db_session, GoalCreate(name="Test Goal"))
        
        wam_data = WAMCreate(
            goal_id=goal.id,
            week_number=2,
            execution_score=90,
            notes="Excellent progress"
        )
        wam = crud.create_wam(db_session, wam_data)
        
        assert wam.goal_id == goal.id
        assert wam.execution_score == 90

    def test_get_wams(self, db_session):
        """Test getting all WAMs."""
        crud.create_wam(db_session, WAMCreate(week_number=1, execution_score=80))
        crud.create_wam(db_session, WAMCreate(week_number=2, execution_score=85))
        
        wams = crud.get_wams(db_session)
        
        assert len(wams) == 2
        # Should be ordered by week_number desc
        assert wams[0].week_number == 2

    def test_get_wams_by_goal(self, db_session):
        """Test getting WAMs filtered by goal."""
        goal = crud.create_goal(db_session, GoalCreate(name="Test Goal"))
        
        crud.create_wam(db_session, WAMCreate(goal_id=goal.id, week_number=1, execution_score=80))
        crud.create_wam(db_session, WAMCreate(goal_id=goal.id, week_number=2, execution_score=85))
        # WAM without goal
        crud.create_wam(db_session, WAMCreate(week_number=3, execution_score=70))
        
        wams = crud.get_wams(db_session, goal_id=goal.id)
        
        assert len(wams) == 2
        for wam in wams:
            assert wam.goal_id == goal.id

    def test_get_wam(self, db_session):
        """Test getting a single WAM."""
        created_wam = crud.create_wam(db_session, WAMCreate(week_number=1, execution_score=85))
        retrieved_wam = crud.get_wam(db_session, created_wam.id)
        
        assert retrieved_wam is not None
        assert retrieved_wam.id == created_wam.id
        assert retrieved_wam.week_number == 1

    def test_get_wam_not_found(self, db_session):
        """Test getting a non-existent WAM."""
        wam = crud.get_wam(db_session, 999)
        assert wam is None

    def test_update_wam(self, db_session):
        """Test updating a WAM."""
        created_wam = crud.create_wam(db_session, WAMCreate(week_number=1, execution_score=80))
        
        update_data = WAMUpdate(execution_score=90, notes="Updated notes")
        updated_wam = crud.update_wam(db_session, created_wam.id, update_data)
        
        assert updated_wam.execution_score == 90
        assert updated_wam.notes == "Updated notes"
        assert updated_wam.week_number == 1  # Unchanged

    def test_update_wam_not_found(self, db_session):
        """Test updating a non-existent WAM."""
        result = crud.update_wam(db_session, 999, WAMUpdate(execution_score=90))
        assert result is None

    def test_delete_wam(self, db_session):
        """Test deleting a WAM."""
        created_wam = crud.create_wam(db_session, WAMCreate(week_number=1, execution_score=80))
        wam_id = created_wam.id
        
        success = crud.delete_wam(db_session, wam_id)
        assert success is True
        
        deleted_wam = crud.get_wam(db_session, wam_id)
        assert deleted_wam is None

    def test_delete_wam_not_found(self, db_session):
        """Test deleting a non-existent WAM."""
        success = crud.delete_wam(db_session, 999)
        assert success is False


# ==================== WAM API Integration Tests ====================

class TestWAMAPI:
    """Integration tests for WAM API endpoints."""

    def test_create_wam_api(self, client):
        """Test creating a WAM via API."""
        response = client.post(
            "/api/wams",
            json={
                "week_number": 1,
                "execution_score": 85,
                "notes": "Good progress",
                "plan_next": "Focus on completion"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["week_number"] == 1
        assert data["execution_score"] == 85
        assert data["notes"] == "Good progress"
        assert data["plan_next"] == "Focus on completion"

    def test_create_wam_with_goal_api(self, client):
        """Test creating a WAM associated with a goal."""
        # Create a goal first
        goal_response = client.post("/api/goals", json={"name": "Test Goal"})
        goal_id = goal_response.json()["id"]
        
        response = client.post(
            "/api/wams",
            json={
                "goal_id": goal_id,
                "week_number": 2,
                "execution_score": 90
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["goal_id"] == goal_id
        assert data["execution_score"] == 90

    def test_get_all_wams_api(self, client):
        """Test getting all WAMs via API."""
        client.post("/api/wams", json={"week_number": 1, "execution_score": 80})
        client.post("/api/wams", json={"week_number": 2, "execution_score": 85})
        
        response = client.get("/api/wams")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_wams_by_goal_api(self, client):
        """Test getting WAMs filtered by goal."""
        goal_response = client.post("/api/goals", json={"name": "Test Goal"})
        goal_id = goal_response.json()["id"]
        
        client.post("/api/wams", json={"goal_id": goal_id, "week_number": 1, "execution_score": 80})
        client.post("/api/wams", json={"goal_id": goal_id, "week_number": 2, "execution_score": 85})
        client.post("/api/wams", json={"week_number": 3, "execution_score": 70})  # No goal
        
        response = client.get(f"/api/wams?goal_id={goal_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_single_wam_api(self, client):
        """Test getting a single WAM via API."""
        create_response = client.post(
            "/api/wams",
            json={"week_number": 1, "execution_score": 85, "notes": "Test notes"}
        )
        wam_id = create_response.json()["id"]
        
        response = client.get(f"/api/wams/{wam_id}")
        assert response.status_code == 200
        assert response.json()["week_number"] == 1
        assert response.json()["notes"] == "Test notes"

    def test_get_single_wam_not_found_api(self, client):
        """Test getting a non-existent WAM via API."""
        response = client.get("/api/wams/999")
        assert response.status_code == 404

    def test_update_wam_api(self, client):
        """Test updating a WAM via API."""
        create_response = client.post(
            "/api/wams",
            json={"week_number": 1, "execution_score": 80, "notes": "Original"}
        )
        wam_id = create_response.json()["id"]
        
        response = client.put(
            f"/api/wams/{wam_id}",
            json={"execution_score": 95, "notes": "Updated"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["execution_score"] == 95
        assert data["notes"] == "Updated"
        assert data["week_number"] == 1  # Unchanged

    def test_update_wam_not_found_api(self, client):
        """Test updating a non-existent WAM via API."""
        response = client.put("/api/wams/999", json={"execution_score": 90})
        assert response.status_code == 404

    def test_delete_wam_api(self, client):
        """Test deleting a WAM via API."""
        create_response = client.post(
            "/api/wams",
            json={"week_number": 1, "execution_score": 80}
        )
        wam_id = create_response.json()["id"]
        
        response = client.delete(f"/api/wams/{wam_id}")
        assert response.status_code == 204
        
        # Verify it's gone
        get_response = client.get(f"/api/wams/{wam_id}")
        assert get_response.status_code == 404

    def test_delete_wam_not_found_api(self, client):
        """Test deleting a non-existent WAM via API."""
        response = client.delete("/api/wams/999")
        assert response.status_code == 404
