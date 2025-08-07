import uuid
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from enum import Enum

from ..models import Goal, Task, User, GoalStatus, Priority, AgentAction
from ..memory import MemoryManager


class ProgressTrend(str, Enum):
    """Progress trend indicators"""
    EXCELLENT = "excellent"  # Ahead of schedule
    GOOD = "good"           # On track
    MODERATE = "moderate"   # Slightly behind
    POOR = "poor"          # Significantly behind
    STAGNANT = "stagnant"  # No progress


class ReflectionType(str, Enum):
    """Types of reflection analysis"""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    GOAL_COMPLETION = "goal_completion"
    MILESTONE = "milestone"
    ON_DEMAND = "on_demand"


@dataclass
class ProgressInsight:
    """Individual insight about user's progress"""
    insight_type: str
    title: str
    description: str
    confidence: float  # 0-1
    impact: str  # low, medium, high
    recommendations: List[str]
    data_points: Dict[str, Any]


@dataclass
class ReflectionReport:
    """Comprehensive reflection report"""
    id: str
    user_id: str
    reflection_type: ReflectionType
    period_start: datetime
    period_end: datetime
    overall_progress: ProgressTrend
    insights: List[ProgressInsight]
    recommendations: List[str]
    plan_adjustments: List[Dict[str, Any]]
    created_at: datetime
    
    def get_summary(self) -> str:
        """Get a text summary of the reflection"""
        return f"Progress: {self.overall_progress.value.title()}, {len(self.insights)} insights, {len(self.recommendations)} recommendations"


class ProgressEvaluator:
    """
    Analyzes user progress, identifies patterns, and provides insights
    for continuous improvement and plan adjustment.
    """
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        
    def conduct_reflection(self, user_id: str, goals: List[Goal],
                         reflection_type: ReflectionType = ReflectionType.WEEKLY,
                         period_days: int = 7) -> ReflectionReport:
        """
        Conduct a comprehensive reflection analysis
        """
        
        # Define analysis period
        end_time = datetime.now()
        start_time = end_time - timedelta(days=period_days)
        
        # Gather data for analysis
        progress_data = self._gather_progress_data(user_id, goals, start_time, end_time)
        
        # Analyze progress trends
        overall_trend = self._analyze_overall_progress(progress_data)
        
        # Generate insights
        insights = self._generate_insights(user_id, progress_data, goals)
        
        # Create recommendations
        recommendations = self._generate_recommendations(insights, progress_data)
        
        # Suggest plan adjustments
        plan_adjustments = self._suggest_plan_adjustments(insights, goals)
        
        # Create reflection report
        report = ReflectionReport(
            id=str(uuid.uuid4()),
            user_id=user_id,
            reflection_type=reflection_type,
            period_start=start_time,
            period_end=end_time,
            overall_progress=overall_trend,
            insights=insights,
            recommendations=recommendations,
            plan_adjustments=plan_adjustments,
            created_at=datetime.now()
        )
        
        # Store reflection in memory
        self._store_reflection_insights(user_id, report)
        
        return report
    
    def _gather_progress_data(self, user_id: str, goals: List[Goal],
                            start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Gather progress data for analysis"""
        
        # Get goal-related memories from the period
        goal_memories = self.memory_manager.get_goal_history(user_id)
        recent_memories = [m for m in goal_memories 
                          if start_time <= m.created_at <= end_time]
        
        # Get conversation memories
        conversations = self.memory_manager.get_conversation_history(user_id, limit=50)
        recent_conversations = [c for c in conversations 
                              if start_time <= c.created_at <= end_time]
        
        # Analyze goal progress changes
        goal_progress = {}
        for goal in goals:
            goal_history = [m for m in recent_memories 
                          if m.metadata.get("goal_id") == goal.id]
            
            progress_updates = []
            for memory in goal_history:
                if "progress_update" in memory.content.lower():
                    progress_updates.append({
                        "timestamp": memory.created_at,
                        "content": memory.content,
                        "metadata": memory.metadata
                    })
            
            goal_progress[goal.id] = {
                "goal": goal,
                "updates": progress_updates,
                "current_progress": goal.progress,
                "memories_count": len(goal_history)
            }
        
        # Calculate activity metrics
        activity_metrics = {
            "total_memories": len(recent_memories),
            "conversation_count": len(recent_conversations),
            "goal_updates": sum(len(gp["updates"]) for gp in goal_progress.values()),
            "active_goals": len([g for g in goals if g.status == GoalStatus.ACTIVE]),
            "days_analyzed": (end_time - start_time).days
        }
        
        return {
            "goals": goal_progress,
            "recent_memories": recent_memories,
            "conversations": recent_conversations,
            "activity_metrics": activity_metrics,
            "analysis_period": {"start": start_time, "end": end_time}
        }
    
    def _analyze_overall_progress(self, progress_data: Dict[str, Any]) -> ProgressTrend:
        """Analyze overall progress trend"""
        
        goals_data = progress_data["goals"]
        activity_metrics = progress_data["activity_metrics"]
        
        if not goals_data:
            return ProgressTrend.STAGNANT
        
        # Calculate progress scores
        progress_scores = []
        activity_score = 0
        
        # Analyze individual goal progress
        for goal_id, goal_info in goals_data.items():
            goal = goal_info["goal"]
            updates = goal_info["updates"]
            
            # Score based on progress updates frequency
            days_analyzed = activity_metrics["days_analyzed"]
            expected_updates = max(1, days_analyzed // 3)  # Expect update every 3 days
            update_score = min(1.0, len(updates) / expected_updates)
            
            # Score based on progress amount
            days_remaining = (goal.time_bound - date.today()).days
            total_days = (goal.time_bound - goal.created_at.date()).days
            expected_progress = min(100, ((total_days - days_remaining) / total_days) * 100)
            progress_score = min(1.0, goal.progress / max(expected_progress, 1))
            
            combined_score = (update_score * 0.4 + progress_score * 0.6)
            progress_scores.append(combined_score)
        
        # Overall activity score
        expected_activity = activity_metrics["days_analyzed"]  # At least 1 interaction per day
        actual_activity = activity_metrics["conversation_count"] + activity_metrics["goal_updates"]
        activity_score = min(1.0, actual_activity / expected_activity)
        
        # Calculate overall score
        if progress_scores:
            avg_progress = sum(progress_scores) / len(progress_scores)
            overall_score = (avg_progress * 0.7 + activity_score * 0.3)
        else:
            overall_score = activity_score
        
        # Map score to trend
        if overall_score >= 0.9:
            return ProgressTrend.EXCELLENT
        elif overall_score >= 0.7:
            return ProgressTrend.GOOD
        elif overall_score >= 0.5:
            return ProgressTrend.MODERATE
        elif overall_score >= 0.3:
            return ProgressTrend.POOR
        else:
            return ProgressTrend.STAGNANT
    
    def _generate_insights(self, user_id: str, progress_data: Dict[str, Any], 
                          goals: List[Goal]) -> List[ProgressInsight]:
        """Generate insights about user's progress patterns"""
        
        insights = []
        goals_data = progress_data["goals"]
        activity_metrics = progress_data["activity_metrics"]
        
        # Insight 1: Goal progress analysis
        if goals_data:
            behind_schedule = []
            ahead_schedule = []
            
            for goal_id, goal_info in goals_data.items():
                goal = goal_info["goal"]
                days_remaining = (goal.time_bound - date.today()).days
                total_days = (goal.time_bound - goal.created_at.date()).days
                expected_progress = ((total_days - days_remaining) / total_days) * 100
                
                if goal.progress < expected_progress - 15:
                    behind_schedule.append(goal.title)
                elif goal.progress > expected_progress + 15:
                    ahead_schedule.append(goal.title)
            
            if behind_schedule:
                insights.append(ProgressInsight(
                    insight_type="goal_timing",
                    title="Goals Behind Schedule",
                    description=f"{len(behind_schedule)} goal(s) are behind their expected timeline",
                    confidence=0.8,
                    impact="high",
                    recommendations=[
                        "Review and break down large tasks into smaller steps",
                        "Increase time allocation for these goals",
                        "Consider extending deadlines if necessary",
                        "Identify and remove blockers"
                    ],
                    data_points={"behind_goals": behind_schedule}
                ))
            
            if ahead_schedule:
                insights.append(ProgressInsight(
                    insight_type="goal_timing",
                    title="Goals Ahead of Schedule",
                    description=f"{len(ahead_schedule)} goal(s) are ahead of their timeline",
                    confidence=0.9,
                    impact="medium",
                    recommendations=[
                        "Consider setting more ambitious targets",
                        "Use extra time to add quality improvements",
                        "Start planning next phase goals"
                    ],
                    data_points={"ahead_goals": ahead_schedule}
                ))
        
        # Insight 2: Engagement patterns
        conversations = progress_data["conversations"]
        if conversations:
            engagement_insight = self._analyze_engagement_patterns(conversations)
            if engagement_insight:
                insights.append(engagement_insight)
        
        # Insight 3: Learning consistency
        learning_insight = self._analyze_learning_consistency(user_id, progress_data)
        if learning_insight:
            insights.append(learning_insight)
        
        # Insight 4: Goal completion patterns
        completion_insight = self._analyze_completion_patterns(user_id, goals)
        if completion_insight:
            insights.append(completion_insight)
        
        return insights
    
    def _analyze_engagement_patterns(self, conversations: List) -> Optional[ProgressInsight]:
        """Analyze user engagement patterns"""
        
        if len(conversations) < 3:
            return ProgressInsight(
                insight_type="engagement",
                title="Low Engagement",
                description="Limited interaction with career coaching system",
                confidence=0.7,
                impact="medium",
                recommendations=[
                    "Set up regular check-in reminders",
                    "Break goals into smaller, more manageable tasks",
                    "Schedule dedicated time for career development"
                ],
                data_points={"conversation_count": len(conversations)}
            )
        
        # Analyze conversation timing
        conversation_days = set()
        for conv in conversations:
            conversation_days.add(conv.created_at.date())
        
        days_with_activity = len(conversation_days)
        period_days = 7  # Assuming weekly analysis
        
        if days_with_activity >= period_days * 0.7:  # 70% of days
            return ProgressInsight(
                insight_type="engagement",
                title="Consistent Engagement",
                description="Regular and consistent interaction with career development",
                confidence=0.9,
                impact="high",
                recommendations=[
                    "Maintain this excellent engagement pattern",
                    "Consider setting more challenging goals",
                    "Share your progress with others for accountability"
                ],
                data_points={"active_days": days_with_activity, "total_days": period_days}
            )
        
        return None
    
    def _analyze_learning_consistency(self, user_id: str, progress_data: Dict[str, Any]) -> Optional[ProgressInsight]:
        """Analyze learning and skill development consistency"""
        
        memories = progress_data["recent_memories"]
        learning_activities = []
        
        for memory in memories:
            content_lower = memory.content.lower()
            if any(keyword in content_lower for keyword in 
                   ["learn", "study", "course", "tutorial", "practice", "skill"]):
                learning_activities.append(memory)
        
        if not learning_activities:
            return ProgressInsight(
                insight_type="learning",
                title="Limited Learning Activity",
                description="Few learning or skill development activities detected",
                confidence=0.6,
                impact="medium",
                recommendations=[
                    "Schedule regular learning sessions",
                    "Set aside dedicated time for skill development",
                    "Choose specific learning resources and track progress"
                ],
                data_points={"learning_activities": 0}
            )
        
        # Analyze learning frequency
        learning_days = set()
        for activity in learning_activities:
            learning_days.add(activity.created_at.date())
        
        consistency_score = len(learning_days) / 7  # For weekly analysis
        
        if consistency_score >= 0.4:  # 3+ days per week
            return ProgressInsight(
                insight_type="learning",
                title="Good Learning Consistency",
                description="Regular learning and skill development activities",
                confidence=0.8,
                impact="high",
                recommendations=[
                    "Continue this excellent learning routine",
                    "Consider tracking specific learning outcomes",
                    "Set measurable skill development milestones"
                ],
                data_points={"learning_days": len(learning_days), "activities": len(learning_activities)}
            )
        
        return None
    
    def _analyze_completion_patterns(self, user_id: str, goals: List[Goal]) -> Optional[ProgressInsight]:
        """Analyze goal and task completion patterns"""
        
        # Get historical goal data
        all_goal_memories = self.memory_manager.get_goal_history(user_id)
        
        completed_goals = []
        stalled_goals = []
        
        for goal in goals:
            if goal.status == GoalStatus.COMPLETED:
                completed_goals.append(goal)
            elif goal.status == GoalStatus.ACTIVE and goal.progress < 10:
                # Check if goal has been stagnant
                goal_memories = [m for m in all_goal_memories 
                               if m.metadata.get("goal_id") == goal.id]
                if goal_memories:
                    last_update = max(m.created_at for m in goal_memories)
                    days_since_update = (datetime.now() - last_update).days
                    if days_since_update > 14:  # No updates for 2 weeks
                        stalled_goals.append(goal)
        
        if stalled_goals:
            return ProgressInsight(
                insight_type="completion",
                title="Stalled Goals Detected",
                description=f"{len(stalled_goals)} goal(s) appear to be stalled with minimal progress",
                confidence=0.7,
                impact="high",
                recommendations=[
                    "Review and break down stalled goals into smaller tasks",
                    "Identify specific blockers or challenges",
                    "Consider adjusting goal scope or timeline",
                    "Set up accountability measures"
                ],
                data_points={"stalled_goals": [g.title for g in stalled_goals]}
            )
        
        return None
    
    def _generate_recommendations(self, insights: List[ProgressInsight], 
                                progress_data: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on insights"""
        
        recommendations = []
        
        # Collect all recommendations from insights
        for insight in insights:
            recommendations.extend(insight.recommendations)
        
        # Add general recommendations based on progress data
        activity_metrics = progress_data["activity_metrics"]
        
        if activity_metrics["conversation_count"] < 3:
            recommendations.append("Increase engagement with career coaching system through regular check-ins")
        
        if activity_metrics["goal_updates"] == 0:
            recommendations.append("Update goal progress at least twice per week")
        
        if activity_metrics["active_goals"] == 0:
            recommendations.append("Set at least one active career goal to maintain momentum")
        
        # Remove duplicates and prioritize
        unique_recommendations = list(set(recommendations))
        
        # Sort by importance (basic heuristic)
        priority_keywords = ["goal", "progress", "schedule", "plan"]
        prioritized = []
        remaining = []
        
        for rec in unique_recommendations:
            if any(keyword in rec.lower() for keyword in priority_keywords):
                prioritized.append(rec)
            else:
                remaining.append(rec)
        
        return prioritized + remaining
    
    def _suggest_plan_adjustments(self, insights: List[ProgressInsight], 
                                goals: List[Goal]) -> List[Dict[str, Any]]:
        """Suggest specific plan adjustments"""
        
        adjustments = []
        
        # Analyze insights for adjustment opportunities
        for insight in insights:
            if insight.insight_type == "goal_timing" and "behind" in insight.title.lower():
                behind_goals = insight.data_points.get("behind_goals", [])
                for goal_title in behind_goals:
                    goal = next((g for g in goals if g.title == goal_title), None)
                    if goal:
                        adjustments.append({
                            "type": "timeline_extension",
                            "goal_id": goal.id,
                            "goal_title": goal.title,
                            "suggestion": "Extend deadline by 2-4 weeks",
                            "reason": "Goal is behind expected progress timeline",
                            "impact": "medium"
                        })
            
            elif insight.insight_type == "completion" and "stalled" in insight.title.lower():
                stalled_goals = insight.data_points.get("stalled_goals", [])
                for goal_title in stalled_goals:
                    goal = next((g for g in goals if g.title == goal_title), None)
                    if goal:
                        adjustments.append({
                            "type": "goal_restructure",
                            "goal_id": goal.id,
                            "goal_title": goal.title,
                            "suggestion": "Break down into smaller, actionable tasks",
                            "reason": "Goal appears to be stalled with minimal progress",
                            "impact": "high"
                        })
            
            elif insight.insight_type == "learning" and "limited" in insight.description.lower():
                adjustments.append({
                    "type": "learning_schedule",
                    "suggestion": "Add dedicated learning sessions 3x per week",
                    "reason": "Insufficient learning activity detected",
                    "impact": "medium"
                })
        
        return adjustments
    
    def _store_reflection_insights(self, user_id: str, report: ReflectionReport):
        """Store reflection insights in memory"""
        
        # Store overall reflection summary
        summary_content = f"Reflection Report ({report.reflection_type.value}): {report.get_summary()}"
        self.memory_manager.store_insight(
            user_id=user_id,
            insight=summary_content,
            source="reflection_system"
        )
        
        # Store individual insights
        for insight in report.insights:
            insight_content = f"{insight.title}: {insight.description}"
            self.memory_manager.store_insight(
                user_id=user_id,
                insight=insight_content,
                source="progress_analysis"
            )
    
    def get_progress_trends(self, user_id: str, goals: List[Goal], 
                          days_back: int = 30) -> Dict[str, Any]:
        """Get progress trends over time"""
        
        # Get goal history over time period
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days_back)
        
        goal_memories = self.memory_manager.get_goal_history(user_id)
        period_memories = [m for m in goal_memories 
                          if start_time <= m.created_at <= end_time]
        
        # Analyze trends for each goal
        goal_trends = {}
        for goal in goals:
            goal_updates = [m for m in period_memories 
                          if m.metadata.get("goal_id") == goal.id]
            
            progress_points = []
            for update in goal_updates:
                if "progress" in update.metadata:
                    progress_points.append({
                        "date": update.created_at.date(),
                        "progress": update.metadata["progress"]
                    })
            
            # Calculate trend
            if len(progress_points) >= 2:
                first_progress = progress_points[0]["progress"]
                last_progress = progress_points[-1]["progress"]
                trend = "improving" if last_progress > first_progress else "declining"
            else:
                trend = "insufficient_data"
            
            goal_trends[goal.id] = {
                "goal_title": goal.title,
                "current_progress": goal.progress,
                "trend": trend,
                "updates_count": len(progress_points),
                "progress_points": progress_points
            }
        
        return {
            "period": {"start": start_time, "end": end_time, "days": days_back},
            "goal_trends": goal_trends,
            "total_updates": len(period_memories)
        }