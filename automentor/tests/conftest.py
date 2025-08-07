import pytest
import tempfile
import shutil
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import User, Goal, Task, GoalStatus, Priority, SkillLevel


@pytest.fixture
def temp_directory():
    """Create temporary directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_user():
    """Create a sample user for testing"""
    return User(
        id="test_user_001",
        name="Alex Test",
        email="alex@test.com",
        current_role="Junior Developer",
        years_experience=2,
        skills={
            "Python": SkillLevel.INTERMEDIATE,
            "JavaScript": SkillLevel.INTERMEDIATE,
            "React": SkillLevel.BEGINNER,
            "SQL": SkillLevel.INTERMEDIATE,
            "Git": SkillLevel.ADVANCED
        },
        interests=["Web Development", "Machine Learning", "Open Source"],
        location="San Francisco, CA",
        education=["Computer Science Degree"]
    )


@pytest.fixture
def sample_goal():
    """Create a sample goal for testing"""
    return Goal(
        id="goal_001",
        user_id="test_user_001",
        title="Learn React Development",
        description="Master React for frontend development",
        specific="Learn React fundamentals and build 3 projects",
        measurable="Complete course and portfolio projects",
        achievable="Study 10 hours per week",
        relevant="For frontend developer career",
        time_bound=date.today() + timedelta(days=90),
        status=GoalStatus.PLANNING,
        progress=0.0,
        priority=Priority.HIGH
    )


@pytest.fixture
def sample_tasks():
    """Create sample tasks for testing"""
    goal_id = "goal_001"
    return [
        Task(
            id="task_001",
            goal_id=goal_id,
            title="Setup Development Environment",
            description="Install Node.js, VS Code, and create React app",
            priority=Priority.HIGH,
            estimated_hours=4,
            due_date=date.today() + timedelta(days=7)
        ),
        Task(
            id="task_002",
            goal_id=goal_id,
            title="Complete React Tutorial",
            description="Finish official React tutorial and exercises",
            priority=Priority.HIGH,
            estimated_hours=20,
            due_date=date.today() + timedelta(days=21)
        ),
        Task(
            id="task_003",
            goal_id=goal_id,
            title="Build Portfolio Project",
            description="Create a todo app using React",
            priority=Priority.MEDIUM,
            estimated_hours=30,
            due_date=date.today() + timedelta(days=45)
        )
    ]


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response for testing"""
    return {
        "choices": [
            {
                "message": {
                    "content": "This is a mock response from the AI assistant for testing purposes."
                }
            }
        ]
    }


@pytest.fixture
def mock_sentence_transformer():
    """Mock SentenceTransformer for testing"""
    with patch('core.memory.vector_store.SentenceTransformer') as mock:
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_model.encode.return_value = [[0.1] * 384]  # Mock embedding
        mock.return_value = mock_model
        yield mock_model


# Configure pytest settings
def pytest_configure(config):
    """Configure pytest settings"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


# Test collection configuration
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers"""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid or "TestIntegration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        # Mark unit tests
        elif "test_" in item.name and "integration" not in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Mark slow tests
        if any(keyword in item.nodeid.lower() for keyword in ["slow", "performance", "load"]):
            item.add_marker(pytest.mark.slow)