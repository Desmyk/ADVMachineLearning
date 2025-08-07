import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime, date, timedelta
from dataclasses import dataclass

from ..models import Goal, Task, User, GoalStatus, Priority, SkillLevel
from ..memory import MemoryManager


@dataclass
class GoalSuggestion:
    """Suggestion for goal improvement or creation"""
    title: str
    description: str
    rationale: str
    urgency: Priority
    estimated_timeline: str


class GoalManager:
    """
    Manages goal creation, validation, tracking, and collaborative refinement
    using SMART criteria (Specific, Measurable, Achievable, Relevant, Time-bound)
    """
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.active_goals: Dict[str, List[Goal]] = {}  # user_id -> list of goals
        
    def create_collaborative_goal(self, user_id: str, initial_goal_description: str,
                                user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Collaboratively create a SMART goal through interactive refinement
        """
        # Analyze the initial goal description
        analysis = self._analyze_goal_description(initial_goal_description, user_context)
        
        # Generate questions to make the goal SMART
        smart_questions = self._generate_smart_questions(analysis)
        
        # Create initial goal structure
        goal_id = str(uuid.uuid4())
        initial_goal = {
            "id": goal_id,
            "user_id": user_id,
            "title": analysis["suggested_title"],
            "description": initial_goal_description,
            "smart_status": analysis["smart_status"],
            "questions": smart_questions,
            "suggestions": analysis["suggestions"]
        }
        
        return initial_goal
    
    def _analyze_goal_description(self, description: str, 
                                user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze goal description and identify SMART criteria gaps"""
        
        analysis = {
            "suggested_title": self._extract_title(description),
            "smart_status": {
                "specific": self._check_specific(description),
                "measurable": self._check_measurable(description),
                "achievable": self._check_achievable(description, user_context),
                "relevant": self._check_relevant(description, user_context),
                "time_bound": self._check_time_bound(description)
            },
            "suggestions": []
        }
        
        # Generate suggestions based on gaps
        if not analysis["smart_status"]["specific"]:
            analysis["suggestions"].append(
                "Goal needs more specificity. What exactly do you want to achieve?"
            )
        
        if not analysis["smart_status"]["measurable"]:
            analysis["suggestions"].append(
                "How will you measure success? What are the concrete indicators?"
            )
        
        if not analysis["smart_status"]["time_bound"]:
            analysis["suggestions"].append(
                "When do you want to achieve this goal? Setting a deadline helps with accountability."
            )
        
        return analysis
    
    def _extract_title(self, description: str) -> str:
        """Extract a concise title from the goal description"""
        # Simple extraction - take first sentence or first 50 characters
        sentences = description.split('.')
        if sentences:
            title = sentences[0].strip()
            if len(title) > 50:
                title = title[:47] + "..."
            return title
        return description[:50] + "..." if len(description) > 50 else description
    
    def _check_specific(self, description: str) -> bool:
        """Check if goal is specific enough"""
        # Look for specific action verbs and concrete nouns
        specific_indicators = [
            "learn", "build", "complete", "earn", "get", "develop",
            "create", "improve", "achieve", "obtain", "master"
        ]
        vague_terms = ["better", "more", "good", "some", "many"]
        
        has_specific = any(word in description.lower() for word in specific_indicators)
        has_vague = any(word in description.lower() for word in vague_terms)
        
        return has_specific and not has_vague and len(description.split()) > 5
    
    def _check_measurable(self, description: str) -> bool:
        """Check if goal has measurable criteria"""
        measurable_indicators = [
            "certificate", "job", "salary", "portfolio", "project",
            "course", "interview", "application", "skill level",
            "rating", "score", "certification"
        ]
        
        # Look for numbers or quantifiable terms
        has_numbers = any(char.isdigit() for char in description)
        has_measurable_terms = any(term in description.lower() for term in measurable_indicators)
        
        return has_numbers or has_measurable_terms
    
    def _check_achievable(self, description: str, 
                         user_context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if goal seems achievable given user context"""
        if not user_context:
            return True  # Can't assess without context, assume achievable
        
        # This would involve more sophisticated analysis of user's current skills,
        # experience, and resources vs. goal requirements
        
        # For now, simple heuristic based on timeline and complexity
        timeline_indicators = ["week", "month", "year", "6 months"]
        has_timeline = any(term in description.lower() for term in timeline_indicators)
        
        complexity_indicators = ["PhD", "CEO", "expert level", "10 years experience"]
        high_complexity = any(term in description.lower() for term in complexity_indicators)
        
        return has_timeline and not high_complexity
    
    def _check_relevant(self, description: str,
                       user_context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if goal aligns with user's career direction"""
        if not user_context:
            return True  # Can't assess without context
        
        # This would analyze alignment with user's current role, interests, and industry
        # For now, assume relevant if it's career-related
        career_terms = [
            "job", "career", "skill", "promotion", "salary", "role",
            "position", "interview", "resume", "portfolio", "certification"
        ]
        
        return any(term in description.lower() for term in career_terms)
    
    def _check_time_bound(self, description: str) -> bool:
        """Check if goal has a clear deadline or timeline"""
        time_indicators = [
            "by", "within", "in", "before", "after", "until",
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december",
            "week", "month", "year", "2024", "2025"
        ]
        
        return any(term in description.lower() for term in time_indicators)
    
    def _generate_smart_questions(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate questions to help refine the goal into SMART criteria"""
        questions = []
        smart_status = analysis["smart_status"]
        
        if not smart_status["specific"]:
            questions.append({
                "category": "specific",
                "question": "What exactly do you want to achieve? Can you be more specific about the outcome?",
                "purpose": "To make the goal more specific and concrete"
            })
        
        if not smart_status["measurable"]:
            questions.append({
                "category": "measurable",
                "question": "How will you know when you've achieved this goal? What will success look like?",
                "purpose": "To define clear success criteria"
            })
        
        if not smart_status["achievable"]:
            questions.append({
                "category": "achievable",
                "question": "What skills and resources do you currently have? What will you need to develop or acquire?",
                "purpose": "To assess feasibility and identify requirements"
            })
        
        if not smart_status["relevant"]:
            questions.append({
                "category": "relevant",
                "question": "How does this goal align with your career aspirations? Why is this important to you?",
                "purpose": "To ensure goal relevance and motivation"
            })
        
        if not smart_status["time_bound"]:
            questions.append({
                "category": "time_bound",
                "question": "When do you want to achieve this goal? What's your target timeline?",
                "purpose": "To establish accountability and urgency"
            })
        
        return questions
    
    def finalize_goal(self, user_id: str, goal_data: Dict[str, Any],
                     smart_answers: Dict[str, str]) -> Goal:
        """
        Create final SMART goal from collaborative refinement
        """
        
        # Extract SMART components from answers
        specific = smart_answers.get("specific", goal_data["description"])
        measurable = smart_answers.get("measurable", "Track progress weekly")
        achievable = smart_answers.get("achievable", "Leverage current skills and dedicate time")
        relevant = smart_answers.get("relevant", "Aligns with career goals")
        time_bound_str = smart_answers.get("time_bound", "6 months")
        
        # Parse time_bound into a date
        time_bound = self._parse_timeline_to_date(time_bound_str)
        
        # Create the goal
        goal = Goal(
            id=goal_data["id"],
            user_id=user_id,
            title=goal_data["title"],
            description=specific,
            specific=specific,
            measurable=measurable,
            achievable=achievable,
            relevant=relevant,
            time_bound=time_bound,
            status=GoalStatus.PLANNING,
            priority=Priority.MEDIUM
        )
        
        # Store in memory
        self.memory_manager.store_goal_update(
            user_id=user_id,
            goal=goal,
            update_type="created"
        )
        
        # Add to active goals
        if user_id not in self.active_goals:
            self.active_goals[user_id] = []
        self.active_goals[user_id].append(goal)
        
        return goal
    
    def _parse_timeline_to_date(self, timeline_str: str) -> date:
        """Parse timeline string into a target date"""
        timeline_lower = timeline_str.lower()
        today = date.today()
        
        if "week" in timeline_lower:
            # Extract number of weeks
            weeks = 1
            words = timeline_lower.split()
            for i, word in enumerate(words):
                if word.isdigit():
                    weeks = int(word)
                    break
                elif word in ["one", "two", "three", "four", "six", "eight"]:
                    weeks_map = {"one": 1, "two": 2, "three": 3, "four": 4, "six": 6, "eight": 8}
                    weeks = weeks_map.get(word, 1)
                    break
            return today + timedelta(weeks=weeks)
        
        elif "month" in timeline_lower:
            months = 6  # Default
            words = timeline_lower.split()
            for word in words:
                if word.isdigit():
                    months = int(word)
                    break
                elif word in ["one", "two", "three", "six", "twelve"]:
                    months_map = {"one": 1, "two": 2, "three": 3, "six": 6, "twelve": 12}
                    months = months_map.get(word, 6)
                    break
            return today + timedelta(days=30 * months)
        
        elif "year" in timeline_lower:
            return today + timedelta(days=365)
        
        else:
            # Default to 6 months
            return today + timedelta(days=180)
    
    def get_user_goals(self, user_id: str, status: Optional[GoalStatus] = None) -> List[Goal]:
        """Get goals for a user, optionally filtered by status"""
        user_goals = self.active_goals.get(user_id, [])
        
        if status:
            return [goal for goal in user_goals if goal.status == status]
        
        return user_goals
    
    def update_goal_progress(self, user_id: str, goal_id: str, 
                           progress: float, notes: Optional[str] = None) -> Goal:
        """Update goal progress and status"""
        goal = self._find_goal(user_id, goal_id)
        if not goal:
            raise ValueError(f"Goal {goal_id} not found for user {user_id}")
        
        previous_progress = goal.progress
        goal.progress = min(100.0, max(0.0, progress))
        goal.updated_at = datetime.now()
        
        # Update status based on progress
        if goal.progress >= 100.0:
            goal.status = GoalStatus.COMPLETED
        elif goal.progress > 0:
            goal.status = GoalStatus.ACTIVE
        
        # Store update in memory
        self.memory_manager.store_goal_update(
            user_id=user_id,
            goal=goal,
            update_type="progress_update",
            previous_state={"progress": previous_progress}
        )
        
        # Store insight if significant progress
        if goal.progress - previous_progress >= 25:
            self.memory_manager.store_insight(
                user_id=user_id,
                insight=f"Significant progress on goal '{goal.title}': {goal.progress}% complete",
                source="goal_tracking"
            )
        
        return goal
    
    def _find_goal(self, user_id: str, goal_id: str) -> Optional[Goal]:
        """Find a specific goal for a user"""
        user_goals = self.active_goals.get(user_id, [])
        for goal in user_goals:
            if goal.id == goal_id:
                return goal
        return None
    
    def suggest_goal_improvements(self, user_id: str, goal_id: str) -> List[GoalSuggestion]:
        """Suggest improvements for an existing goal"""
        goal = self._find_goal(user_id, goal_id)
        if not goal:
            return []
        
        suggestions = []
        
        # Check timeline feasibility
        days_remaining = (goal.time_bound - date.today()).days
        if days_remaining < 0:
            suggestions.append(GoalSuggestion(
                title="Extend Deadline",
                description="This goal's deadline has passed. Consider extending the timeline.",
                rationale="Unrealistic deadlines can be demotivating",
                urgency=Priority.HIGH,
                estimated_timeline="Immediate"
            ))
        
        # Check progress rate
        if goal.status == GoalStatus.ACTIVE and goal.progress < 25 and days_remaining < 60:
            suggestions.append(GoalSuggestion(
                title="Break Down Goal",
                description="Consider breaking this goal into smaller, more manageable sub-goals.",
                rationale="Large goals can feel overwhelming without intermediate milestones",
                urgency=Priority.MEDIUM,
                estimated_timeline="1 week"
            ))
        
        # Check for stagnation
        goal_history = self.memory_manager.get_goal_history(user_id, goal_id)
        if len(goal_history) > 5 and all("progress_update" not in h.content for h in goal_history[-3:]):
            suggestions.append(GoalSuggestion(
                title="Reactivate Goal",
                description="This goal seems to have stagnated. Consider reviewing and adjusting the approach.",
                rationale="Inactive goals may need strategy adjustment or priority changes",
                urgency=Priority.MEDIUM,
                estimated_timeline="2-3 days"
            ))
        
        return suggestions
    
    def get_goal_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get analytics about user's goal performance"""
        user_goals = self.get_user_goals(user_id)
        
        if not user_goals:
            return {"total_goals": 0}
        
        analytics = {
            "total_goals": len(user_goals),
            "by_status": {},
            "by_priority": {},
            "average_progress": 0,
            "completion_rate": 0,
            "overdue_goals": 0
        }
        
        total_progress = 0
        completed_goals = 0
        overdue_count = 0
        today = date.today()
        
        for goal in user_goals:
            # Status distribution
            status = goal.status.value
            analytics["by_status"][status] = analytics["by_status"].get(status, 0) + 1
            
            # Priority distribution
            priority = goal.priority.value
            analytics["by_priority"][priority] = analytics["by_priority"].get(priority, 0) + 1
            
            # Progress tracking
            total_progress += goal.progress
            if goal.status == GoalStatus.COMPLETED:
                completed_goals += 1
            
            # Overdue goals
            if goal.time_bound < today and goal.status != GoalStatus.COMPLETED:
                overdue_count += 1
        
        analytics["average_progress"] = total_progress / len(user_goals)
        analytics["completion_rate"] = (completed_goals / len(user_goals)) * 100
        analytics["overdue_goals"] = overdue_count
        
        return analytics