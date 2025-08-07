import json
from typing import List, Dict, Optional, Any
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from enum import Enum

from ...core.models import Goal, Task, User, Priority


class EventType(str, Enum):
    """Types of calendar events"""
    TASK_DEADLINE = "task_deadline"
    GOAL_CHECKIN = "goal_checkin"
    LEARNING_SESSION = "learning_session"
    INTERVIEW = "interview"
    NETWORKING = "networking"
    REMINDER = "reminder"


@dataclass
class CalendarEvent:
    """Calendar event for scheduling"""
    id: str
    title: str
    description: str
    start_time: datetime
    end_time: datetime
    event_type: EventType
    user_id: str
    related_goal_id: Optional[str] = None
    related_task_id: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    reminder_minutes: int = 15
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CareerScheduler:
    """
    Calendar and scheduling tool for career development activities.
    Manages deadlines, check-ins, learning sessions, and career events.
    """
    
    def __init__(self):
        self.events: Dict[str, List[CalendarEvent]] = {}  # user_id -> events
        self.recurring_patterns: Dict[str, Dict] = {}  # For recurring events
    
    def schedule_goal_milestones(self, user_id: str, goal: Goal, 
                                tasks: List[Task] = None) -> List[CalendarEvent]:
        """
        Schedule milestone check-ins and task deadlines for a goal
        """
        events = []
        
        # Goal completion deadline
        goal_deadline = CalendarEvent(
            id=f"goal_deadline_{goal.id}",
            title=f"Goal Deadline: {goal.title}",
            description=f"Final deadline for achieving goal: {goal.description}",
            start_time=datetime.combine(goal.time_bound, datetime.min.time()),
            end_time=datetime.combine(goal.time_bound, datetime.min.time()) + timedelta(hours=1),
            event_type=EventType.GOAL_CHECKIN,
            user_id=user_id,
            related_goal_id=goal.id,
            priority=Priority.HIGH,
            reminder_minutes=1440,  # 24 hours
            metadata={"milestone": "final_deadline"}
        )
        events.append(goal_deadline)
        
        # Weekly check-ins until goal completion
        start_date = datetime.now()
        end_date = datetime.combine(goal.time_bound, datetime.min.time())
        
        current_date = start_date
        week_number = 1
        
        while current_date < end_date:
            checkin_event = CalendarEvent(
                id=f"goal_checkin_{goal.id}_week_{week_number}",
                title=f"Weekly Check-in: {goal.title}",
                description=f"Review progress on goal: {goal.description}",
                start_time=current_date,
                end_time=current_date + timedelta(minutes=30),
                event_type=EventType.GOAL_CHECKIN,
                user_id=user_id,
                related_goal_id=goal.id,
                priority=Priority.MEDIUM,
                reminder_minutes=60,
                metadata={"milestone": f"week_{week_number}_checkin"}
            )
            events.append(checkin_event)
            
            current_date += timedelta(weeks=1)
            week_number += 1
        
        # Schedule task deadlines if tasks provided
        if tasks:
            for task in tasks:
                if task.due_date:
                    task_event = CalendarEvent(
                        id=f"task_deadline_{task.id}",
                        title=f"Task Due: {task.title}",
                        description=task.description,
                        start_time=datetime.combine(task.due_date, datetime.min.time()),
                        end_time=datetime.combine(task.due_date, datetime.min.time()) + timedelta(hours=1),
                        event_type=EventType.TASK_DEADLINE,
                        user_id=user_id,
                        related_goal_id=goal.id,
                        related_task_id=task.id,
                        priority=task.priority,
                        reminder_minutes=1440,  # 24 hours
                        metadata={"estimated_hours": task.estimated_hours}
                    )
                    events.append(task_event)
        
        # Add events to user's calendar
        if user_id not in self.events:
            self.events[user_id] = []
        self.events[user_id].extend(events)
        
        return events
    
    def schedule_learning_sessions(self, user_id: str, goal: Goal,
                                 learning_plan: Dict[str, Any],
                                 hours_per_week: int = 10) -> List[CalendarEvent]:
        """
        Schedule regular learning sessions based on a learning plan
        """
        events = []
        
        # Calculate session distribution
        sessions_per_week = 3  # Default to 3 sessions per week
        hours_per_session = hours_per_week / sessions_per_week
        
        # Session times (default to evenings)
        session_times = [
            {"day": 1, "hour": 19},  # Tuesday 7 PM
            {"day": 3, "hour": 19},  # Thursday 7 PM
            {"day": 5, "hour": 14}   # Saturday 2 PM
        ]
        
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = datetime.combine(goal.time_bound, datetime.min.time())
        
        # Generate sessions for each week
        current_week_start = start_date
        session_number = 1
        
        while current_week_start < end_date:
            for session_config in session_times:
                session_date = current_week_start + timedelta(days=session_config["day"])
                
                if session_date >= end_date:
                    break
                
                session_start = session_date.replace(hour=session_config["hour"], minute=0)
                session_end = session_start + timedelta(hours=hours_per_session)
                
                # Determine focus area (rotate through learning topics)
                topics = learning_plan.get("topics", ["Study", "Practice", "Project Work"])
                focus_topic = topics[(session_number - 1) % len(topics)]
                
                learning_event = CalendarEvent(
                    id=f"learning_session_{goal.id}_{session_number}",
                    title=f"Learning Session: {focus_topic}",
                    description=f"Dedicated learning time for {goal.title} - Focus: {focus_topic}",
                    start_time=session_start,
                    end_time=session_end,
                    event_type=EventType.LEARNING_SESSION,
                    user_id=user_id,
                    related_goal_id=goal.id,
                    priority=Priority.MEDIUM,
                    reminder_minutes=30,
                    metadata={
                        "focus_topic": focus_topic,
                        "planned_hours": hours_per_session,
                        "session_number": session_number
                    }
                )
                events.append(learning_event)
                session_number += 1
            
            current_week_start += timedelta(weeks=1)
        
        # Add to user's calendar
        if user_id not in self.events:
            self.events[user_id] = []
        self.events[user_id].extend(events)
        
        return events
    
    def schedule_job_application_activities(self, user_id: str, 
                                          application_timeline: Dict[str, Any]) -> List[CalendarEvent]:
        """
        Schedule job application related activities
        """
        events = []
        
        # Resume update session
        resume_update = CalendarEvent(
            id=f"resume_update_{user_id}_{datetime.now().strftime('%Y%m%d')}",
            title="Update Resume",
            description="Review and update resume based on target job requirements",
            start_time=datetime.now() + timedelta(days=1),
            end_time=datetime.now() + timedelta(days=1, hours=2),
            event_type=EventType.TASK_DEADLINE,
            user_id=user_id,
            priority=Priority.HIGH,
            reminder_minutes=120,
            metadata={"activity_type": "resume_preparation"}
        )
        events.append(resume_update)
        
        # Interview preparation sessions
        prep_sessions = [
            {"title": "Technical Interview Prep", "days": 7, "hours": 2},
            {"title": "Behavioral Interview Prep", "days": 10, "hours": 1.5},
            {"title": "Company Research", "days": 14, "hours": 1}
        ]
        
        for prep in prep_sessions:
            prep_event = CalendarEvent(
                id=f"interview_prep_{prep['title'].replace(' ', '_').lower()}_{user_id}",
                title=prep["title"],
                description=f"Dedicated time for {prep['title'].lower()}",
                start_time=datetime.now() + timedelta(days=prep["days"]),
                end_time=datetime.now() + timedelta(days=prep["days"], hours=prep["hours"]),
                event_type=EventType.INTERVIEW,
                user_id=user_id,
                priority=Priority.HIGH,
                reminder_minutes=60,
                metadata={"preparation_type": prep["title"].lower()}
            )
            events.append(prep_event)
        
        # Weekly application targets
        for week in range(1, 5):  # 4 weeks of applications
            application_session = CalendarEvent(
                id=f"job_applications_week_{week}_{user_id}",
                title=f"Job Applications - Week {week}",
                description=f"Apply to 3-5 positions matching your target criteria",
                start_time=datetime.now() + timedelta(weeks=week, days=1),  # Monday
                end_time=datetime.now() + timedelta(weeks=week, days=1, hours=3),
                event_type=EventType.TASK_DEADLINE,
                user_id=user_id,
                priority=Priority.HIGH,
                reminder_minutes=60,
                metadata={
                    "target_applications": 5,
                    "week_number": week
                }
            )
            events.append(application_session)
        
        # Add networking events
        networking_events = [
            {"title": "LinkedIn Networking", "days": 3, "duration": 1},
            {"title": "Industry Meetup Research", "days": 8, "duration": 0.5},
            {"title": "Coffee Chat Outreach", "days": 15, "duration": 1}
        ]
        
        for networking in networking_events:
            network_event = CalendarEvent(
                id=f"networking_{networking['title'].replace(' ', '_').lower()}_{user_id}",
                title=networking["title"],
                description=f"Networking activity: {networking['title']}",
                start_time=datetime.now() + timedelta(days=networking["days"]),
                end_time=datetime.now() + timedelta(days=networking["days"], 
                                                  hours=networking["duration"]),
                event_type=EventType.NETWORKING,
                user_id=user_id,
                priority=Priority.MEDIUM,
                reminder_minutes=30,
                metadata={"networking_type": networking["title"]}
            )
            events.append(network_event)
        
        # Add to user's calendar
        if user_id not in self.events:
            self.events[user_id] = []
        self.events[user_id].extend(events)
        
        return events
    
    def create_custom_event(self, user_id: str, title: str, description: str,
                           start_time: datetime, duration_hours: float,
                           event_type: EventType = EventType.REMINDER,
                           priority: Priority = Priority.MEDIUM,
                           related_goal_id: Optional[str] = None) -> CalendarEvent:
        """
        Create a custom calendar event
        """
        end_time = start_time + timedelta(hours=duration_hours)
        
        event = CalendarEvent(
            id=f"custom_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            event_type=event_type,
            user_id=user_id,
            related_goal_id=related_goal_id,
            priority=priority,
            reminder_minutes=30
        )
        
        if user_id not in self.events:
            self.events[user_id] = []
        self.events[user_id].append(event)
        
        return event
    
    def get_upcoming_events(self, user_id: str, days_ahead: int = 7) -> List[CalendarEvent]:
        """
        Get upcoming events for a user within specified days
        """
        if user_id not in self.events:
            return []
        
        now = datetime.now()
        cutoff_date = now + timedelta(days=days_ahead)
        
        upcoming_events = []
        for event in self.events[user_id]:
            if now <= event.start_time <= cutoff_date:
                upcoming_events.append(event)
        
        # Sort by start time
        upcoming_events.sort(key=lambda e: e.start_time)
        return upcoming_events
    
    def get_overdue_events(self, user_id: str) -> List[CalendarEvent]:
        """
        Get overdue events for a user
        """
        if user_id not in self.events:
            return []
        
        now = datetime.now()
        overdue_events = []
        
        for event in self.events[user_id]:
            if event.start_time < now and event.event_type in [
                EventType.TASK_DEADLINE, EventType.GOAL_CHECKIN
            ]:
                overdue_events.append(event)
        
        return overdue_events
    
    def get_events_for_goal(self, user_id: str, goal_id: str) -> List[CalendarEvent]:
        """
        Get all events related to a specific goal
        """
        if user_id not in self.events:
            return []
        
        goal_events = []
        for event in self.events[user_id]:
            if event.related_goal_id == goal_id:
                goal_events.append(event)
        
        return goal_events
    
    def update_event(self, user_id: str, event_id: str, **updates) -> Optional[CalendarEvent]:
        """
        Update an existing event
        """
        if user_id not in self.events:
            return None
        
        for event in self.events[user_id]:
            if event.id == event_id:
                for key, value in updates.items():
                    if hasattr(event, key):
                        setattr(event, key, value)
                return event
        
        return None
    
    def delete_event(self, user_id: str, event_id: str) -> bool:
        """
        Delete an event
        """
        if user_id not in self.events:
            return False
        
        user_events = self.events[user_id]
        for i, event in enumerate(user_events):
            if event.id == event_id:
                del user_events[i]
                return True
        
        return False
    
    def get_calendar_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get a summary of user's calendar
        """
        if user_id not in self.events:
            return {"total_events": 0}
        
        events = self.events[user_id]
        now = datetime.now()
        
        # Categorize events
        upcoming = len([e for e in events if e.start_time > now])
        overdue = len([e for e in events if e.start_time < now and 
                      e.event_type in [EventType.TASK_DEADLINE, EventType.GOAL_CHECKIN]])
        
        # Events by type
        events_by_type = {}
        for event in events:
            event_type = event.event_type.value
            events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
        
        # Weekly schedule load
        next_week = now + timedelta(weeks=1)
        next_week_events = [e for e in events if now <= e.start_time <= next_week]
        
        summary = {
            "total_events": len(events),
            "upcoming_events": upcoming,
            "overdue_events": overdue,
            "events_by_type": events_by_type,
            "next_week_load": len(next_week_events),
            "next_week_hours": sum((e.end_time - e.start_time).total_seconds() / 3600 
                                 for e in next_week_events)
        }
        
        return summary
    
    def suggest_optimal_schedule_times(self, user_id: str, 
                                     activity_type: str,
                                     duration_hours: float,
                                     preferences: Dict[str, Any] = None) -> List[datetime]:
        """
        Suggest optimal times for scheduling new activities
        """
        suggestions = []
        preferences = preferences or {}
        
        # Default preferences
        preferred_days = preferences.get("preferred_days", [1, 2, 3, 4, 5])  # Mon-Fri
        preferred_hours = preferences.get("preferred_hours", [9, 10, 14, 15, 19, 20])
        avoid_conflicts = preferences.get("avoid_conflicts", True)
        
        # Get existing events to avoid conflicts
        existing_events = self.events.get(user_id, [])
        
        # Look for slots in the next 2 weeks
        start_search = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_search = start_search + timedelta(weeks=2)
        
        current_date = start_search
        while current_date <= end_search and len(suggestions) < 5:
            # Skip if not a preferred day
            if current_date.weekday() not in preferred_days:
                current_date += timedelta(days=1)
                continue
            
            for hour in preferred_hours:
                suggested_start = current_date.replace(hour=hour, minute=0)
                suggested_end = suggested_start + timedelta(hours=duration_hours)
                
                # Check for conflicts if required
                if avoid_conflicts:
                    has_conflict = False
                    for event in existing_events:
                        if (suggested_start < event.end_time and 
                            suggested_end > event.start_time):
                            has_conflict = True
                            break
                    
                    if has_conflict:
                        continue
                
                suggestions.append(suggested_start)
                
                if len(suggestions) >= 5:
                    break
            
            current_date += timedelta(days=1)
        
        return suggestions