from datetime import datetime, date
from typing import List, Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class GoalStatus(str, Enum):
    """Status of a career goal"""
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    """Priority levels for tasks and goals"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class SkillLevel(str, Enum):
    """User's skill level in a particular area"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class User(BaseModel):
    """User profile model"""
    id: str
    name: str
    email: str
    current_role: Optional[str] = None
    years_experience: Optional[int] = None
    skills: Dict[str, SkillLevel] = Field(default_factory=dict)
    interests: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    education: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Goal(BaseModel):
    """Career goal model following SMART criteria"""
    id: str
    user_id: str
    title: str
    description: str
    specific: str  # What exactly will be accomplished
    measurable: str  # How will progress be measured
    achievable: str  # How is this goal achievable
    relevant: str  # Why is this goal important
    time_bound: date  # When will this be completed
    status: GoalStatus = GoalStatus.PLANNING
    priority: Priority = Priority.MEDIUM
    progress: float = 0.0  # 0-100 percentage
    sub_goals: List[str] = Field(default_factory=list)  # IDs of sub-goals
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Task(BaseModel):
    """Individual task within a goal"""
    id: str
    goal_id: str
    title: str
    description: str
    due_date: Optional[date] = None
    completed: bool = False
    priority: Priority = Priority.MEDIUM
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    resources: List[str] = Field(default_factory=list)  # URLs, books, courses
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class LearningResource(BaseModel):
    """Learning resource recommendation"""
    id: str
    title: str
    type: str  # course, book, video, article, practice
    url: Optional[str] = None
    description: str
    skill_focus: List[str] = Field(default_factory=list)
    difficulty_level: SkillLevel
    estimated_duration: Optional[str] = None  # "2 weeks", "30 hours", etc.
    cost: Optional[str] = None  # "free", "$50", "subscription"
    rating: Optional[float] = None


class JobRecommendation(BaseModel):
    """Job recommendation from various sources"""
    id: str
    title: str
    company: str
    location: str
    job_type: str  # full-time, part-time, contract, remote
    salary_range: Optional[str] = None
    description: str
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    experience_level: str
    application_url: Optional[str] = None
    match_score: Optional[float] = None  # How well it matches user's profile
    discovered_at: datetime = Field(default_factory=datetime.now)


class MemoryEntry(BaseModel):
    """Memory entry for long-term context storage"""
    id: str
    user_id: str
    content: str
    type: str  # conversation, goal_update, progress, insight
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    importance: float = 0.5  # 0-1 scale for memory importance


class AgentAction(BaseModel):
    """Record of autonomous actions taken by the agent"""
    id: str
    user_id: str
    action_type: str  # reminder, suggestion, tool_use, plan_update
    description: str
    success: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


class ConversationMessage(BaseModel):
    """Chat conversation message"""
    id: str
    user_id: str
    role: str  # user, assistant, system
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


class PlanningSession(BaseModel):
    """Planning session record"""
    id: str
    user_id: str
    goal_id: str
    session_type: str  # initial_planning, progress_review, adjustment
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    reasoning: str
    created_at: datetime = Field(default_factory=datetime.now)


class UserFeedback(BaseModel):
    """User feedback on agent suggestions and actions"""
    id: str
    user_id: str
    feedback_type: str  # rating, comment, correction
    target_id: str  # ID of the item being rated (goal, task, suggestion)
    rating: Optional[int] = None  # 1-5 scale
    comment: Optional[str] = None
    helpful: Optional[bool] = None
    created_at: datetime = Field(default_factory=datetime.now)