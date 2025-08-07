import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.planning.goal_manager import GoalManager, GoalSuggestion
from core.planning.task_planner import TaskPlanner, PlanningStrategy
from core.models import Goal, Task, User, GoalStatus, Priority, SkillLevel
from core.memory import MemoryManager


class TestGoalManager:
    """Test cases for GoalManager"""
    
    @pytest.fixture
    def memory_manager(self):
        """Mock MemoryManager for testing"""
        mock_manager = Mock(spec=MemoryManager)
        mock_manager.store_goal_update.return_value = "mock_memory_id"
        mock_manager.store_insight.return_value = "mock_insight_id"
        mock_manager.get_goal_history.return_value = []
        mock_manager.get_user_preferences.return_value = {}
        return mock_manager
    
    @pytest.fixture
    def goal_manager(self, memory_manager):
        """Create GoalManager for testing"""
        return GoalManager(memory_manager)
    
    def test_create_collaborative_goal(self, goal_manager):
        """Test collaborative goal creation"""
        user_id = "test_user_001"
        goal_description = "I want to learn React development"
        
        result = goal_manager.create_collaborative_goal(
            user_id=user_id,
            initial_goal_description=goal_description
        )
        
        assert result["user_id"] == user_id
        assert result["description"] == goal_description
        assert "smart_status" in result
        assert "questions" in result
        assert "suggestions" in result
        assert len(result["questions"]) > 0
    
    def test_analyze_goal_description_specific(self, goal_manager):
        """Test goal description analysis for specificity"""
        specific_goal = "Learn React fundamentals and build 3 portfolio projects"
        vague_goal = "Get better at programming"
        
        specific_analysis = goal_manager._analyze_goal_description(specific_goal)
        vague_analysis = goal_manager._analyze_goal_description(vague_goal)
        
        assert specific_analysis["smart_status"]["specific"] == True
        assert vague_analysis["smart_status"]["specific"] == False
    
    def test_analyze_goal_description_measurable(self, goal_manager):
        """Test goal description analysis for measurability"""
        measurable_goal = "Complete React certification course and build 3 projects"
        unmeasurable_goal = "Learn some React"
        
        measurable_analysis = goal_manager._analyze_goal_description(measurable_goal)
        unmeasurable_analysis = goal_manager._analyze_goal_description(unmeasurable_goal)
        
        assert measurable_analysis["smart_status"]["measurable"] == True
        assert unmeasurable_analysis["smart_status"]["measurable"] == False
    
    def test_analyze_goal_description_time_bound(self, goal_manager):
        """Test goal description analysis for time constraints"""
        time_bound_goal = "Learn React within 3 months"
        no_time_goal = "Learn React development"
        
        time_bound_analysis = goal_manager._analyze_goal_description(time_bound_goal)
        no_time_analysis = goal_manager._analyze_goal_description(no_time_goal)
        
        assert time_bound_analysis["smart_status"]["time_bound"] == True
        assert no_time_analysis["smart_status"]["time_bound"] == False
    
    def test_generate_smart_questions(self, goal_manager):
        """Test SMART questions generation"""
        analysis = {
            "smart_status": {
                "specific": False,
                "measurable": True,
                "achievable": True,
                "relevant": True,
                "time_bound": False
            }
        }
        
        questions = goal_manager._generate_smart_questions(analysis)
        
        # Should generate questions for missing criteria
        categories = [q["category"] for q in questions]
        assert "specific" in categories
        assert "time_bound" in categories
        assert "measurable" not in categories  # Already satisfied
    
    def test_finalize_goal(self, goal_manager):
        """Test goal finalization"""
        user_id = "test_user_001"
        goal_data = {
            "id": "goal_001",
            "title": "Learn React Development",
            "description": "Master React for frontend development"
        }
        smart_answers = {
            "specific": "Learn React fundamentals and build 3 projects",
            "measurable": "Complete course and 3 portfolio projects",
            "achievable": "Study 10 hours per week",
            "relevant": "Essential for frontend developer career",
            "time_bound": "6 months"
        }
        
        goal = goal_manager.finalize_goal(user_id, goal_data, smart_answers)
        
        assert isinstance(goal, Goal)
        assert goal.id == goal_data["id"]
        assert goal.user_id == user_id
        assert goal.title == goal_data["title"]
        assert goal.status == GoalStatus.PLANNING
        assert goal.time_bound > date.today()
    
    def test_parse_timeline_to_date(self, goal_manager):
        """Test timeline parsing"""
        today = date.today()
        
        # Test weeks
        week_date = goal_manager._parse_timeline_to_date("2 weeks")
        assert week_date == today + timedelta(weeks=2)
        
        # Test months
        month_date = goal_manager._parse_timeline_to_date("3 months")
        assert month_date == today + timedelta(days=90)
        
        # Test year
        year_date = goal_manager._parse_timeline_to_date("1 year")
        assert year_date == today + timedelta(days=365)
        
        # Test default
        default_date = goal_manager._parse_timeline_to_date("soon")
        assert default_date == today + timedelta(days=180)
    
    def test_update_goal_progress(self, goal_manager):
        """Test goal progress updates"""
        user_id = "test_user_001"
        goal = Goal(
            id="goal_001",
            user_id=user_id,
            title="Learn React",
            description="Master React development",
            specific="Learn React fundamentals",
            measurable="Complete course",
            achievable="Study regularly",
            relevant="For career",
            time_bound=date.today() + timedelta(days=90),
            progress=25.0
        )
        
        # Add goal to manager
        goal_manager.active_goals[user_id] = [goal]
        
        # Update progress
        updated_goal = goal_manager.update_goal_progress(
            user_id=user_id,
            goal_id=goal.id,
            progress=75.0
        )
        
        assert updated_goal.progress == 75.0
        assert updated_goal.status == GoalStatus.ACTIVE
        
        # Test completion
        completed_goal = goal_manager.update_goal_progress(
            user_id=user_id,
            goal_id=goal.id,
            progress=100.0
        )
        
        assert completed_goal.progress == 100.0
        assert completed_goal.status == GoalStatus.COMPLETED
    
    def test_suggest_goal_improvements(self, goal_manager):
        """Test goal improvement suggestions"""
        user_id = "test_user_001"
        overdue_goal = Goal(
            id="goal_001",
            user_id=user_id,
            title="Learn React",
            description="Master React development",
            specific="Learn React fundamentals",
            measurable="Complete course",
            achievable="Study regularly",
            relevant="For career",
            time_bound=date.today() - timedelta(days=1),  # Overdue
            progress=50.0
        )
        
        goal_manager.active_goals[user_id] = [overdue_goal]
        
        suggestions = goal_manager.suggest_goal_improvements(user_id, overdue_goal.id)
        
        assert len(suggestions) > 0
        assert any("deadline" in s.description.lower() for s in suggestions)
    
    def test_get_goal_analytics(self, goal_manager):
        """Test goal analytics"""
        user_id = "test_user_001"
        goals = [
            Goal(
                id="goal_001", user_id=user_id, title="Goal 1",
                description="Test goal 1", specific="Test", measurable="Test",
                achievable="Test", relevant="Test",
                time_bound=date.today() + timedelta(days=30),
                status=GoalStatus.ACTIVE, progress=50.0, priority=Priority.HIGH
            ),
            Goal(
                id="goal_002", user_id=user_id, title="Goal 2",
                description="Test goal 2", specific="Test", measurable="Test",
                achievable="Test", relevant="Test",
                time_bound=date.today() + timedelta(days=60),
                status=GoalStatus.COMPLETED, progress=100.0, priority=Priority.MEDIUM
            )
        ]
        
        goal_manager.active_goals[user_id] = goals
        
        analytics = goal_manager.get_goal_analytics(user_id)
        
        assert analytics["total_goals"] == 2
        assert analytics["by_status"]["active"] == 1
        assert analytics["by_status"]["completed"] == 1
        assert analytics["completion_rate"] == 50.0
        assert analytics["average_progress"] == 75.0


class TestTaskPlanner:
    """Test cases for TaskPlanner"""
    
    @pytest.fixture
    def memory_manager(self):
        """Mock MemoryManager for testing"""
        mock_manager = Mock(spec=MemoryManager)
        mock_manager.store_insight.return_value = "mock_insight_id"
        mock_manager.get_user_preferences.return_value = {}
        return mock_manager
    
    @pytest.fixture
    def task_planner(self, memory_manager):
        """Create TaskPlanner for testing"""
        return TaskPlanner(memory_manager)
    
    @pytest.fixture
    def sample_goal(self):
        """Create sample goal for testing"""
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
            progress=0.0
        )
    
    def test_create_comprehensive_plan(self, task_planner, sample_goal):
        """Test comprehensive planning"""
        user_id = "test_user_001"
        
        plan = task_planner.create_comprehensive_plan(
            user_id=user_id,
            goal=sample_goal,
            strategy=PlanningStrategy.MILESTONE
        )
        
        assert "goal_id" in plan
        assert "strategy_used" in plan
        assert "total_tasks" in plan
        assert "tasks" in plan
        assert "timeline" in plan
        assert "insights" in plan
        assert len(plan["tasks"]) > 0
    
    def test_categorize_goal(self, task_planner):
        """Test goal categorization"""
        # Test software developer goal
        dev_goal = "Become a full-stack developer"
        assert task_planner._categorize_goal(dev_goal) == "software_developer"
        
        # Test data science goal
        data_goal = "Learn machine learning and data analytics"
        assert task_planner._categorize_goal(data_goal) == "data_scientist"
        
        # Test product management goal
        pm_goal = "Become a product manager"
        assert task_planner._categorize_goal(pm_goal) == "product_manager"
        
        # Test general goal
        general_goal = "Improve my leadership skills"
        assert task_planner._categorize_goal(general_goal) == "general"
    
    def test_analyze_goal_complexity(self, task_planner, sample_goal):
        """Test goal complexity analysis"""
        user_context = {
            "skills": {"Python": "intermediate", "JavaScript": "beginner"},
            "experience": 2
        }
        
        analysis = task_planner._analyze_goal_complexity(sample_goal, user_context)
        
        assert "goal_category" in analysis
        assert "complexity_factors" in analysis
        assert "complexity_score" in analysis
        assert "success_metrics" in analysis
        assert "risk_factors" in analysis
        assert 0.0 <= analysis["complexity_score"] <= 1.0
    
    def test_assess_skill_gap(self, task_planner, sample_goal):
        """Test skill gap assessment"""
        # User with relevant skills
        high_skill_context = {
            "skills": {"React": "advanced", "JavaScript": "expert"}
        }
        low_gap = task_planner._assess_skill_gap(sample_goal, high_skill_context)
        assert low_gap == "low"
        
        # User with no relevant skills
        low_skill_context = {
            "skills": {"Python": "beginner"}
        }
        high_gap = task_planner._assess_skill_gap(sample_goal, low_skill_context)
        assert high_gap == "high"
        
        # No context
        unknown_gap = task_planner._assess_skill_gap(sample_goal, None)
        assert unknown_gap == "unknown"
    
    def test_assess_time_constraint(self, task_planner):
        """Test time constraint assessment"""
        # Short deadline
        short_goal = Goal(
            id="test", user_id="test", title="Test", description="Test",
            specific="Test", measurable="Test", achievable="Test", relevant="Test",
            time_bound=date.today() + timedelta(days=15)  # 15 days
        )
        assert task_planner._assess_time_constraint(short_goal) == "high"
        
        # Medium deadline
        medium_goal = Goal(
            id="test", user_id="test", title="Test", description="Test",
            specific="Test", measurable="Test", achievable="Test", relevant="Test",
            time_bound=date.today() + timedelta(days=60)  # 60 days
        )
        assert task_planner._assess_time_constraint(medium_goal) == "medium"
        
        # Long deadline
        long_goal = Goal(
            id="test", user_id="test", title="Test", description="Test",
            specific="Test", measurable="Test", achievable="Test", relevant="Test",
            time_bound=date.today() + timedelta(days=180)  # 180 days
        )
        assert task_planner._assess_time_constraint(long_goal) == "low"
    
    def test_plan_linear(self, task_planner, sample_goal):
        """Test linear planning strategy"""
        analysis = {
            "goal_category": "software_developer",
            "complexity_factors": {"skill_gap": "medium"}
        }
        
        tasks = task_planner._plan_linear(sample_goal, analysis, None)
        
        assert len(tasks) > 0
        assert all(isinstance(task, Task) for task in tasks)
        assert all(task.goal_id == sample_goal.id for task in tasks)
    
    def test_plan_milestone(self, task_planner, sample_goal):
        """Test milestone planning strategy"""
        analysis = {
            "goal_category": "software_developer",
            "complexity_factors": {"skill_gap": "medium"}
        }
        
        tasks = task_planner._plan_milestone(sample_goal, analysis, None)
        
        assert len(tasks) > 0
        # Should have tasks for different milestones
        milestone_tasks = [t for t in tasks if "foundation" in t.title.lower() or 
                          "development" in t.title.lower()]
        assert len(milestone_tasks) > 0
    
    def test_prioritize_tasks(self, task_planner, sample_goal):
        """Test task prioritization"""
        tasks = [
            Task(id="1", goal_id=sample_goal.id, title="Setup environment", 
                 description="Test", priority=Priority.MEDIUM, estimated_hours=2),
            Task(id="2", goal_id=sample_goal.id, title="Learn basics", 
                 description="Test", priority=Priority.LOW, estimated_hours=10),
            Task(id="3", goal_id=sample_goal.id, title="Build project", 
                 description="Test", priority=Priority.MEDIUM, estimated_hours=20),
        ]
        
        analysis = {"complexity_factors": {"time_constraint": "high"}}
        
        prioritized = task_planner._prioritize_tasks(tasks, sample_goal, analysis)
        
        assert len(prioritized) == 3
        # Setup tasks should be high priority
        setup_task = next(t for t in prioritized if "setup" in t.title.lower())
        assert setup_task.priority == Priority.HIGH
    
    def test_calculate_timeline(self, task_planner, sample_goal):
        """Test timeline calculation"""
        tasks = [
            Task(id="1", goal_id=sample_goal.id, title="Task 1", 
                 description="Test", estimated_hours=10),
            Task(id="2", goal_id=sample_goal.id, title="Task 2", 
                 description="Test", estimated_hours=20),
        ]
        
        timeline = task_planner._calculate_timeline(tasks, sample_goal)
        
        assert timeline["total_hours"] == 30
        assert timeline["estimated_weeks"] == 3.0  # 30 hours / 10 hours per week
        assert "feasibility" in timeline
        assert "weekly_commitment" in timeline
    
    def test_generate_planning_insights(self, task_planner, sample_goal):
        """Test planning insights generation"""
        tasks = [
            Task(id="1", goal_id=sample_goal.id, title="Task 1", 
                 description="Test", estimated_hours=100)  # Very long task
        ]
        
        analysis = {
            "complexity_factors": {
                "time_constraint": "high",
                "skill_gap": "high",
                "resource_requirements": "high"
            }
        }
        
        insights = task_planner._generate_planning_insights(sample_goal, tasks, analysis)
        
        assert len(insights) >= 1
        # Should generate insights about time pressure, skill gap, or resources
        insight_types = [insight.insight_type for insight in insights]
        assert any(itype in ["time_pressure", "skill_development", "resource_planning"] 
                  for itype in insight_types)