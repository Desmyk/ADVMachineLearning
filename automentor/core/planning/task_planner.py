import uuid
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from enum import Enum

from ..models import Goal, Task, User, Priority, SkillLevel
from ..memory import MemoryManager


class PlanningStrategy(str, Enum):
    """Different approaches to planning task breakdown"""
    LINEAR = "linear"  # Sequential steps
    PARALLEL = "parallel"  # Tasks that can be done simultaneously
    MILESTONE = "milestone"  # Major checkpoints with sub-tasks
    ADAPTIVE = "adaptive"  # Adjusts based on user preferences and context


@dataclass
class TaskTemplate:
    """Template for common task types"""
    title: str
    description: str
    typical_duration: str
    prerequisites: List[str]
    resources_needed: List[str]
    success_criteria: str
    difficulty_level: SkillLevel


@dataclass
class PlanningInsight:
    """Insight generated during planning process"""
    insight_type: str
    description: str
    confidence: float
    recommendations: List[str]


class TaskPlanner:
    """
    Multi-step reasoning engine that breaks down goals into actionable tasks
    with intelligent prioritization and resource planning.
    """
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.task_templates = self._initialize_task_templates()
        self.planning_strategies = {
            PlanningStrategy.LINEAR: self._plan_linear,
            PlanningStrategy.PARALLEL: self._plan_parallel,
            PlanningStrategy.MILESTONE: self._plan_milestone,
            PlanningStrategy.ADAPTIVE: self._plan_adaptive
        }
    
    def _initialize_task_templates(self) -> Dict[str, List[TaskTemplate]]:
        """Initialize common task templates for different career goals"""
        
        templates = {
            "software_developer": [
                TaskTemplate(
                    title="Learn Programming Language",
                    description="Master the fundamentals of {language}",
                    typical_duration="4-8 weeks",
                    prerequisites=["Basic computer skills"],
                    resources_needed=["Online course", "Practice projects", "Development environment"],
                    success_criteria="Complete 3 projects demonstrating proficiency",
                    difficulty_level=SkillLevel.INTERMEDIATE
                ),
                TaskTemplate(
                    title="Build Portfolio Projects",
                    description="Create {num_projects} projects showcasing different skills",
                    typical_duration="2-3 months",
                    prerequisites=["Programming language knowledge"],
                    resources_needed=["GitHub account", "Hosting platform", "Design tools"],
                    success_criteria="Live projects with clean code and documentation",
                    difficulty_level=SkillLevel.INTERMEDIATE
                ),
                TaskTemplate(
                    title="Technical Interview Preparation",
                    description="Practice coding interviews and system design",
                    typical_duration="4-6 weeks",
                    prerequisites=["Strong programming foundation"],
                    resources_needed=["Interview prep books", "Practice platforms", "Mock interviews"],
                    success_criteria="Consistently solve medium-level problems",
                    difficulty_level=SkillLevel.ADVANCED
                )
            ],
            "data_scientist": [
                TaskTemplate(
                    title="Learn Data Analysis",
                    description="Master Python/R for data manipulation and analysis",
                    typical_duration="6-8 weeks",
                    prerequisites=["Basic statistics", "Programming fundamentals"],
                    resources_needed=["Python/R environment", "Datasets", "Online courses"],
                    success_criteria="Complete end-to-end data analysis project",
                    difficulty_level=SkillLevel.INTERMEDIATE
                ),
                TaskTemplate(
                    title="Machine Learning Foundation",
                    description="Understand ML algorithms and implementations",
                    typical_duration="8-12 weeks",
                    prerequisites=["Data analysis skills", "Statistics knowledge"],
                    resources_needed=["ML libraries", "Datasets", "Jupyter notebooks"],
                    success_criteria="Build and deploy a ML model",
                    difficulty_level=SkillLevel.ADVANCED
                )
            ],
            "product_manager": [
                TaskTemplate(
                    title="Product Strategy Course",
                    description="Learn product strategy, roadmapping, and metrics",
                    typical_duration="4-6 weeks",
                    prerequisites=["Business acumen"],
                    resources_needed=["Online course", "Case studies", "Product management books"],
                    success_criteria="Create a product strategy document",
                    difficulty_level=SkillLevel.INTERMEDIATE
                ),
                TaskTemplate(
                    title="Stakeholder Management Practice",
                    description="Develop skills in cross-functional collaboration",
                    typical_duration="Ongoing",
                    prerequisites=["Communication skills"],
                    resources_needed=["Practice opportunities", "Feedback mechanisms"],
                    success_criteria="Successfully lead cross-functional project",
                    difficulty_level=SkillLevel.ADVANCED
                )
            ]
        }
        
        return templates
    
    def create_comprehensive_plan(self, user_id: str, goal: Goal,
                                user_context: Optional[Dict[str, Any]] = None,
                                strategy: PlanningStrategy = PlanningStrategy.ADAPTIVE) -> Dict[str, Any]:
        """
        Create a comprehensive plan for achieving a goal using multi-step reasoning
        """
        
        # Analyze goal and context
        analysis = self._analyze_goal_complexity(goal, user_context)
        
        # Select appropriate planning strategy
        if strategy == PlanningStrategy.ADAPTIVE:
            strategy = self._select_optimal_strategy(goal, analysis, user_context)
        
        # Generate tasks using selected strategy
        planning_func = self.planning_strategies[strategy]
        tasks = planning_func(goal, analysis, user_context)
        
        # Prioritize and sequence tasks
        prioritized_tasks = self._prioritize_tasks(tasks, goal, analysis)
        
        # Calculate timeline and dependencies
        timeline = self._calculate_timeline(prioritized_tasks, goal)
        
        # Generate insights and recommendations
        insights = self._generate_planning_insights(goal, tasks, analysis)
        
        # Create execution roadmap
        roadmap = self._create_execution_roadmap(prioritized_tasks, timeline)
        
        plan = {
            "goal_id": goal.id,
            "strategy_used": strategy.value,
            "total_tasks": len(prioritized_tasks),
            "estimated_duration": timeline["total_duration"],
            "tasks": [task.__dict__ for task in prioritized_tasks],
            "timeline": timeline,
            "roadmap": roadmap,
            "insights": [insight.__dict__ for insight in insights],
            "success_metrics": analysis["success_metrics"],
            "risk_factors": analysis["risk_factors"]
        }
        
        # Store planning session
        self.memory_manager.store_insight(
            user_id=user_id,
            insight=f"Created comprehensive plan for '{goal.title}' using {strategy.value} strategy",
            source="task_planner",
            related_items=[goal.id]
        )
        
        return plan
    
    def _analyze_goal_complexity(self, goal: Goal, 
                                user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze goal complexity and determine planning requirements"""
        
        # Determine goal category
        goal_category = self._categorize_goal(goal.description)
        
        # Assess complexity factors
        complexity_factors = {
            "skill_gap": self._assess_skill_gap(goal, user_context),
            "time_constraint": self._assess_time_constraint(goal),
            "resource_requirements": self._assess_resource_requirements(goal),
            "dependencies": self._identify_dependencies(goal)
        }
        
        # Calculate overall complexity score
        complexity_score = self._calculate_complexity_score(complexity_factors)
        
        # Define success metrics
        success_metrics = self._define_success_metrics(goal)
        
        # Identify potential risks
        risk_factors = self._identify_risk_factors(goal, complexity_factors)
        
        return {
            "goal_category": goal_category,
            "complexity_factors": complexity_factors,
            "complexity_score": complexity_score,
            "success_metrics": success_metrics,
            "risk_factors": risk_factors,
            "recommended_approach": self._recommend_approach(complexity_score)
        }
    
    def _categorize_goal(self, description: str) -> str:
        """Categorize the goal based on description keywords"""
        description_lower = description.lower()
        
        # Software development keywords
        if any(keyword in description_lower for keyword in 
               ["developer", "programming", "coding", "software", "web", "app"]):
            return "software_developer"
        
        # Data science keywords
        elif any(keyword in description_lower for keyword in
                ["data", "analytics", "machine learning", "ai", "statistics"]):
            return "data_scientist"
        
        # Product management keywords
        elif any(keyword in description_lower for keyword in
                ["product", "manager", "strategy", "roadmap", "stakeholder"]):
            return "product_manager"
        
        # Marketing keywords
        elif any(keyword in description_lower for keyword in
                ["marketing", "digital", "social media", "content", "brand"]):
            return "marketing"
        
        # Sales keywords
        elif any(keyword in description_lower for keyword in
                ["sales", "business development", "account", "revenue"]):
            return "sales"
        
        else:
            return "general"
    
    def _assess_skill_gap(self, goal: Goal, user_context: Optional[Dict[str, Any]]) -> str:
        """Assess the skill gap between current abilities and goal requirements"""
        if not user_context or "skills" not in user_context:
            return "unknown"
        
        # This would involve more sophisticated skill matching
        # For now, simplified assessment
        goal_keywords = goal.description.lower().split()
        user_skills = user_context.get("skills", {})
        
        relevant_skills = 0
        total_needed = 0
        
        for keyword in goal_keywords:
            if keyword in ["python", "javascript", "react", "sql", "aws"]:
                total_needed += 1
                if keyword in user_skills:
                    relevant_skills += 1
        
        if total_needed == 0:
            return "low"
        
        skill_ratio = relevant_skills / total_needed
        
        if skill_ratio >= 0.8:
            return "low"
        elif skill_ratio >= 0.5:
            return "medium"
        else:
            return "high"
    
    def _assess_time_constraint(self, goal: Goal) -> str:
        """Assess time pressure for the goal"""
        days_until_deadline = (goal.time_bound - date.today()).days
        
        if days_until_deadline < 30:
            return "high"
        elif days_until_deadline < 90:
            return "medium"
        else:
            return "low"
    
    def _assess_resource_requirements(self, goal: Goal) -> str:
        """Assess resource requirements for the goal"""
        description_lower = goal.description.lower()
        
        # Check for expensive resources
        expensive_keywords = ["course", "certification", "degree", "bootcamp", "conference"]
        has_expensive = any(keyword in description_lower for keyword in expensive_keywords)
        
        # Check for equipment/software needs
        equipment_keywords = ["laptop", "software", "tools", "subscription"]
        needs_equipment = any(keyword in description_lower for keyword in equipment_keywords)
        
        if has_expensive and needs_equipment:
            return "high"
        elif has_expensive or needs_equipment:
            return "medium"
        else:
            return "low"
    
    def _identify_dependencies(self, goal: Goal) -> List[str]:
        """Identify dependencies and prerequisites for the goal"""
        dependencies = []
        description_lower = goal.description.lower()
        
        # Common dependencies based on goal type
        if "job" in description_lower:
            dependencies.extend(["resume", "portfolio", "interview_prep"])
        
        if "certification" in description_lower:
            dependencies.extend(["study_materials", "practice_tests"])
        
        if "promotion" in description_lower:
            dependencies.extend(["performance_review", "skill_development"])
        
        return dependencies
    
    def _calculate_complexity_score(self, factors: Dict[str, Any]) -> float:
        """Calculate overall complexity score (0-1)"""
        weights = {
            "skill_gap": 0.3,
            "time_constraint": 0.2,
            "resource_requirements": 0.2,
            "dependencies": 0.3
        }
        
        scores = {
            "low": 0.2,
            "medium": 0.5,
            "high": 0.8,
            "unknown": 0.5
        }
        
        total_score = 0
        for factor, value in factors.items():
            if factor in weights:
                if isinstance(value, str):
                    factor_score = scores.get(value, 0.5)
                elif isinstance(value, list):
                    factor_score = min(0.8, len(value) * 0.1)
                else:
                    factor_score = 0.5
                
                total_score += weights[factor] * factor_score
        
        return total_score
    
    def _define_success_metrics(self, goal: Goal) -> List[str]:
        """Define measurable success criteria"""
        metrics = []
        
        # Use the measurable component from SMART goal
        if goal.measurable:
            metrics.append(goal.measurable)
        
        # Add common metrics based on goal type
        description_lower = goal.description.lower()
        
        if "job" in description_lower:
            metrics.extend([
                "Job offer received",
                "Salary meets expectations",
                "Position aligns with career goals"
            ])
        
        if "skill" in description_lower or "learn" in description_lower:
            metrics.extend([
                "Complete all learning materials",
                "Pass assessments/tests",
                "Build practical projects"
            ])
        
        return metrics
    
    def _identify_risk_factors(self, goal: Goal, complexity_factors: Dict[str, Any]) -> List[str]:
        """Identify potential risks and obstacles"""
        risks = []
        
        # Time-based risks
        if complexity_factors["time_constraint"] == "high":
            risks.append("Insufficient time to complete all necessary steps")
        
        # Skill-based risks
        if complexity_factors["skill_gap"] == "high":
            risks.append("Significant learning curve may cause delays")
        
        # Resource-based risks
        if complexity_factors["resource_requirements"] == "high":
            risks.append("High resource costs may limit progress")
        
        # Dependency risks
        if len(complexity_factors["dependencies"]) > 3:
            risks.append("Multiple dependencies may create bottlenecks")
        
        return risks
    
    def _recommend_approach(self, complexity_score: float) -> str:
        """Recommend planning approach based on complexity"""
        if complexity_score < 0.3:
            return "Simple linear approach with weekly check-ins"
        elif complexity_score < 0.6:
            return "Structured milestone approach with regular reviews"
        else:
            return "Intensive planning with parallel tracks and frequent monitoring"
    
    def _select_optimal_strategy(self, goal: Goal, analysis: Dict[str, Any],
                               user_context: Optional[Dict[str, Any]]) -> PlanningStrategy:
        """Select the best planning strategy based on goal and context"""
        
        complexity = analysis["complexity_score"]
        time_constraint = analysis["complexity_factors"]["time_constraint"]
        
        # High complexity goals benefit from milestone approach
        if complexity > 0.7:
            return PlanningStrategy.MILESTONE
        
        # Time-constrained goals need parallel execution
        elif time_constraint == "high":
            return PlanningStrategy.PARALLEL
        
        # Simple goals can use linear approach
        elif complexity < 0.3:
            return PlanningStrategy.LINEAR
        
        # Default to milestone for balanced approach
        else:
            return PlanningStrategy.MILESTONE
    
    def _plan_linear(self, goal: Goal, analysis: Dict[str, Any],
                    user_context: Optional[Dict[str, Any]]) -> List[Task]:
        """Create a linear sequence of tasks"""
        tasks = []
        goal_category = analysis["goal_category"]
        
        # Get relevant templates
        templates = self.task_templates.get(goal_category, [])
        
        # Create tasks based on templates
        for i, template in enumerate(templates):
            task = Task(
                id=str(uuid.uuid4()),
                goal_id=goal.id,
                title=template.title,
                description=template.description,
                priority=Priority.MEDIUM,
                estimated_hours=self._estimate_hours(template.typical_duration),
                resources=template.resources_needed,
                due_date=goal.time_bound - timedelta(days=(len(templates) - i - 1) * 14)
            )
            tasks.append(task)
        
        return tasks
    
    def _plan_parallel(self, goal: Goal, analysis: Dict[str, Any],
                      user_context: Optional[Dict[str, Any]]) -> List[Task]:
        """Create parallel tracks of tasks that can be executed simultaneously"""
        tasks = []
        goal_category = analysis["goal_category"]
        
        # Identify tasks that can be done in parallel
        preparation_tasks = []
        skill_building_tasks = []
        application_tasks = []
        
        if goal_category == "software_developer":
            # Parallel tracks for software development
            preparation_tasks.extend([
                self._create_task(goal.id, "Set up development environment", Priority.HIGH, 8),
                self._create_task(goal.id, "Create GitHub profile", Priority.MEDIUM, 2),
            ])
            
            skill_building_tasks.extend([
                self._create_task(goal.id, "Complete programming course", Priority.HIGH, 80),
                self._create_task(goal.id, "Build portfolio projects", Priority.HIGH, 120),
            ])
            
            application_tasks.extend([
                self._create_task(goal.id, "Update resume", Priority.MEDIUM, 4),
                self._create_task(goal.id, "Practice technical interviews", Priority.HIGH, 40),
            ])
        
        # Combine all parallel tracks
        tasks.extend(preparation_tasks)
        tasks.extend(skill_building_tasks)
        tasks.extend(application_tasks)
        
        return tasks
    
    def _plan_milestone(self, goal: Goal, analysis: Dict[str, Any],
                       user_context: Optional[Dict[str, Any]]) -> List[Task]:
        """Create milestone-based plan with major checkpoints"""
        tasks = []
        timeline_days = (goal.time_bound - date.today()).days
        
        # Define major milestones (typically 3-4 for most goals)
        milestones = [
            ("Foundation", 0.25),  # 25% of timeline
            ("Development", 0.60),  # 60% of timeline
            ("Application", 0.85),  # 85% of timeline
            ("Achievement", 1.0)    # 100% of timeline
        ]
        
        goal_category = analysis["goal_category"]
        
        for milestone_name, progress_ratio in milestones:
            milestone_date = date.today() + timedelta(days=int(timeline_days * progress_ratio))
            
            # Create milestone-specific tasks
            if milestone_name == "Foundation":
                tasks.extend(self._create_foundation_tasks(goal, goal_category))
            elif milestone_name == "Development":
                tasks.extend(self._create_development_tasks(goal, goal_category))
            elif milestone_name == "Application":
                tasks.extend(self._create_application_tasks(goal, goal_category))
            elif milestone_name == "Achievement":
                tasks.extend(self._create_achievement_tasks(goal, goal_category))
            
            # Set due dates for milestone tasks
            for task in tasks[-3:]:  # Last 3 tasks added
                task.due_date = milestone_date
        
        return tasks
    
    def _plan_adaptive(self, goal: Goal, analysis: Dict[str, Any],
                      user_context: Optional[Dict[str, Any]]) -> List[Task]:
        """Create adaptive plan that adjusts based on user preferences and context"""
        
        # Get user preferences from memory
        user_preferences = self.memory_manager.get_user_preferences(goal.user_id)
        
        # Determine preferred approach
        preferred_approach = user_preferences.get("planning_style", "milestone")
        
        if preferred_approach == "linear":
            return self._plan_linear(goal, analysis, user_context)
        elif preferred_approach == "parallel":
            return self._plan_parallel(goal, analysis, user_context)
        else:
            return self._plan_milestone(goal, analysis, user_context)
    
    def _create_task(self, goal_id: str, title: str, priority: Priority, 
                    estimated_hours: float, description: str = "") -> Task:
        """Helper to create a task"""
        return Task(
            id=str(uuid.uuid4()),
            goal_id=goal_id,
            title=title,
            description=description,
            priority=priority,
            estimated_hours=estimated_hours
        )
    
    def _create_foundation_tasks(self, goal: Goal, category: str) -> List[Task]:
        """Create foundational tasks for goal achievement"""
        tasks = []
        
        if category == "software_developer":
            tasks.extend([
                self._create_task(goal.id, "Research target role requirements", Priority.HIGH, 8),
                self._create_task(goal.id, "Set up learning environment", Priority.HIGH, 4),
                self._create_task(goal.id, "Create study schedule", Priority.MEDIUM, 2),
            ])
        elif category == "data_scientist":
            tasks.extend([
                self._create_task(goal.id, "Assess current technical skills", Priority.HIGH, 4),
                self._create_task(goal.id, "Identify skill gaps", Priority.HIGH, 4),
                self._create_task(goal.id, "Select learning resources", Priority.MEDIUM, 6),
            ])
        
        return tasks
    
    def _create_development_tasks(self, goal: Goal, category: str) -> List[Task]:
        """Create skill development tasks"""
        tasks = []
        
        if category == "software_developer":
            tasks.extend([
                self._create_task(goal.id, "Complete core programming course", Priority.HIGH, 60),
                self._create_task(goal.id, "Build first portfolio project", Priority.HIGH, 40),
                self._create_task(goal.id, "Learn version control (Git)", Priority.MEDIUM, 8),
            ])
        elif category == "data_scientist":
            tasks.extend([
                self._create_task(goal.id, "Master data analysis tools", Priority.HIGH, 80),
                self._create_task(goal.id, "Complete statistics course", Priority.HIGH, 40),
                self._create_task(goal.id, "Work on data projects", Priority.HIGH, 60),
            ])
        
        return tasks
    
    def _create_application_tasks(self, goal: Goal, category: str) -> List[Task]:
        """Create job application related tasks"""
        tasks = []
        
        tasks.extend([
            self._create_task(goal.id, "Update resume and LinkedIn", Priority.HIGH, 8),
            self._create_task(goal.id, "Practice interview skills", Priority.HIGH, 20),
            self._create_task(goal.id, "Network with professionals", Priority.MEDIUM, 16),
            self._create_task(goal.id, "Apply to target positions", Priority.HIGH, 12),
        ])
        
        return tasks
    
    def _create_achievement_tasks(self, goal: Goal, category: str) -> List[Task]:
        """Create final achievement tasks"""
        tasks = []
        
        tasks.extend([
            self._create_task(goal.id, "Prepare for final interviews", Priority.HIGH, 16),
            self._create_task(goal.id, "Negotiate job offers", Priority.MEDIUM, 4),
            self._create_task(goal.id, "Complete goal reflection", Priority.LOW, 2),
        ])
        
        return tasks
    
    def _estimate_hours(self, duration_str: str) -> float:
        """Estimate hours from duration string"""
        duration_lower = duration_str.lower()
        
        if "week" in duration_lower:
            # Extract weeks and assume 10 hours per week
            words = duration_lower.split()
            for word in words:
                if word.replace('-', '').isdigit():
                    weeks = float(word.split('-')[0])
                    return weeks * 10
            return 40  # Default 4 weeks
        
        elif "hour" in duration_lower:
            words = duration_lower.split()
            for word in words:
                if word.replace('-', '').isdigit():
                    return float(word.split('-')[0])
            return 20  # Default
        
        else:
            return 20  # Default estimate
    
    def _prioritize_tasks(self, tasks: List[Task], goal: Goal, 
                         analysis: Dict[str, Any]) -> List[Task]:
        """Prioritize and order tasks based on dependencies and importance"""
        
        # Simple prioritization based on task characteristics
        for task in tasks:
            # High priority for foundational tasks
            if any(keyword in task.title.lower() for keyword in 
                   ["setup", "environment", "foundation", "research"]):
                task.priority = Priority.HIGH
            
            # Medium priority for development tasks
            elif any(keyword in task.title.lower() for keyword in 
                    ["learn", "course", "project", "build"]):
                task.priority = Priority.MEDIUM
            
            # Adjust priority based on time constraints
            if analysis["complexity_factors"]["time_constraint"] == "high":
                if task.priority == Priority.MEDIUM:
                    task.priority = Priority.HIGH
        
        # Sort by priority and estimated effort
        priority_order = {Priority.HIGH: 3, Priority.MEDIUM: 2, Priority.LOW: 1}
        
        tasks.sort(key=lambda t: (
            priority_order.get(t.priority, 1),
            -t.estimated_hours  # Larger tasks first within same priority
        ), reverse=True)
        
        return tasks
    
    def _calculate_timeline(self, tasks: List[Task], goal: Goal) -> Dict[str, Any]:
        """Calculate realistic timeline for task completion"""
        
        total_hours = sum(task.estimated_hours or 0 for task in tasks)
        
        # Assume 10 hours per week of dedicated effort
        hours_per_week = 10
        estimated_weeks = total_hours / hours_per_week
        
        goal_weeks = (goal.time_bound - date.today()).days / 7
        
        timeline = {
            "total_hours": total_hours,
            "estimated_weeks": estimated_weeks,
            "goal_weeks": goal_weeks,
            "total_duration": f"{estimated_weeks:.1f} weeks",
            "feasibility": "feasible" if estimated_weeks <= goal_weeks else "challenging",
            "weekly_commitment": f"{hours_per_week} hours/week",
            "buffer_time": max(0, goal_weeks - estimated_weeks)
        }
        
        return timeline
    
    def _create_execution_roadmap(self, tasks: List[Task], 
                                 timeline: Dict[str, Any]) -> Dict[str, Any]:
        """Create week-by-week execution roadmap"""
        
        roadmap = {
            "weekly_schedule": {},
            "milestones": [],
            "checkpoints": []
        }
        
        # Distribute tasks across weeks
        hours_per_week = 10
        current_week = 1
        current_week_hours = 0
        
        for task in tasks:
            task_hours = task.estimated_hours or 0
            
            # If task fits in current week
            if current_week_hours + task_hours <= hours_per_week:
                week_key = f"Week {current_week}"
                if week_key not in roadmap["weekly_schedule"]:
                    roadmap["weekly_schedule"][week_key] = []
                
                roadmap["weekly_schedule"][week_key].append({
                    "task": task.title,
                    "hours": task_hours,
                    "priority": task.priority.value
                })
                
                current_week_hours += task_hours
            
            else:
                # Move to next week
                current_week += 1
                current_week_hours = task_hours
                
                week_key = f"Week {current_week}"
                roadmap["weekly_schedule"][week_key] = [{
                    "task": task.title,
                    "hours": task_hours,
                    "priority": task.priority.value
                }]
        
        # Add weekly checkpoints
        for week in range(1, current_week + 1):
            if week % 2 == 0:  # Bi-weekly checkpoints
                roadmap["checkpoints"].append({
                    "week": week,
                    "focus": "Progress review and plan adjustment"
                })
        
        return roadmap
    
    def _generate_planning_insights(self, goal: Goal, tasks: List[Task],
                                  analysis: Dict[str, Any]) -> List[PlanningInsight]:
        """Generate insights about the planning process"""
        
        insights = []
        
        # Time feasibility insight
        timeline = self._calculate_timeline(tasks, goal)
        if timeline["feasibility"] == "challenging":
            insights.append(PlanningInsight(
                insight_type="time_pressure",
                description="The planned timeline is ambitious given the scope of work",
                confidence=0.8,
                recommendations=[
                    "Consider extending the deadline",
                    "Prioritize most critical tasks",
                    "Increase weekly time commitment"
                ]
            ))
        
        # Skill gap insight
        if analysis["complexity_factors"]["skill_gap"] == "high":
            insights.append(PlanningInsight(
                insight_type="skill_development",
                description="Significant skill development will be required",
                confidence=0.9,
                recommendations=[
                    "Allocate extra time for learning",
                    "Consider mentorship or courses",
                    "Start with foundational skills"
                ]
            ))
        
        # Resource insight
        if analysis["complexity_factors"]["resource_requirements"] == "high":
            insights.append(PlanningInsight(
                insight_type="resource_planning",
                description="This goal will require significant resources",
                confidence=0.7,
                recommendations=[
                    "Budget for courses and tools",
                    "Look for free alternatives",
                    "Consider spreading costs over time"
                ]
            ))
        
        return insights