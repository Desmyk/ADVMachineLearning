import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from .vector_store import VectorMemoryStore
from ..models import User, Goal, Task, ConversationMessage, MemoryEntry


class MemoryManager:
    """
    High-level memory management system that coordinates between
    vector store and provides intelligent memory operations for the agent.
    """
    
    def __init__(self, vector_store: VectorMemoryStore):
        self.vector_store = vector_store
        
    def store_conversation(self, user_id: str, message: ConversationMessage, 
                          importance: float = 0.5) -> str:
        """Store a conversation message in memory"""
        content = f"Role: {message.role}\nContent: {message.content}"
        
        metadata = {
            "message_id": message.id,
            "role": message.role,
            "timestamp": message.created_at.isoformat()
        }
        
        return self.vector_store.add_memory(
            user_id=user_id,
            content=content,
            memory_type="conversation",
            metadata=metadata,
            importance=importance
        )
    
    def store_goal_update(self, user_id: str, goal: Goal, update_type: str,
                         previous_state: Optional[Dict] = None) -> str:
        """Store goal-related updates"""
        content = f"Goal Update - {update_type}\n"
        content += f"Goal: {goal.title}\n"
        content += f"Description: {goal.description}\n"
        content += f"Status: {goal.status.value}\n"
        content += f"Progress: {goal.progress}%\n"
        content += f"Due: {goal.time_bound}"
        
        metadata = {
            "goal_id": goal.id,
            "update_type": update_type,
            "goal_status": goal.status.value,
            "progress": goal.progress,
            "previous_state": previous_state
        }
        
        # Higher importance for goal completions and major milestones
        importance = 0.8 if update_type in ["completed", "milestone"] else 0.6
        
        return self.vector_store.add_memory(
            user_id=user_id,
            content=content,
            memory_type="goal_update",
            metadata=metadata,
            importance=importance
        )
    
    def store_insight(self, user_id: str, insight: str, source: str = "agent",
                     related_items: Optional[List[str]] = None) -> str:
        """Store insights about user's career progress or patterns"""
        content = f"Insight: {insight}\nSource: {source}"
        
        metadata = {
            "source": source,
            "related_items": related_items or [],
            "insight_type": "career_pattern"
        }
        
        return self.vector_store.add_memory(
            user_id=user_id,
            content=content,
            memory_type="insight",
            metadata=metadata,
            importance=0.7
        )
    
    def store_user_preference(self, user_id: str, preference_type: str, 
                            preference_value: Any, context: str = "") -> str:
        """Store user preferences and behavioral patterns"""
        content = f"User Preference - {preference_type}\n"
        content += f"Value: {preference_value}\n"
        content += f"Context: {context}"
        
        metadata = {
            "preference_type": preference_type,
            "preference_value": preference_value,
            "context": context
        }
        
        return self.vector_store.add_memory(
            user_id=user_id,
            content=content,
            memory_type="preference",
            metadata=metadata,
            importance=0.6
        )
    
    def get_relevant_context(self, user_id: str, query: str, 
                           context_types: Optional[List[str]] = None,
                           max_items: int = 10) -> List[MemoryEntry]:
        """Retrieve relevant context for a given query"""
        # Search for semantically similar memories
        relevant_memories = self.vector_store.search_memories(
            user_id=user_id,
            query=query,
            top_k=max_items,
            memory_types=context_types
        )
        
        return relevant_memories
    
    def get_conversation_history(self, user_id: str, limit: int = 20) -> List[MemoryEntry]:
        """Get recent conversation history"""
        return self.vector_store.search_memories(
            user_id=user_id,
            query="",
            top_k=limit,
            memory_types=["conversation"]
        )
    
    def get_goal_history(self, user_id: str, goal_id: Optional[str] = None) -> List[MemoryEntry]:
        """Get goal-related memory entries"""
        memories = self.vector_store.get_user_context(user_id, context_window=100)
        
        goal_memories = []
        for memory in memories:
            if memory.type == "goal_update":
                if goal_id is None or memory.metadata.get("goal_id") == goal_id:
                    goal_memories.append(memory)
        
        return goal_memories
    
    def get_user_insights(self, user_id: str) -> List[MemoryEntry]:
        """Get all insights about the user"""
        return self.vector_store.search_memories(
            user_id=user_id,
            query="",
            top_k=50,
            memory_types=["insight"]
        )
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Extract user preferences from memory"""
        preference_memories = self.vector_store.search_memories(
            user_id=user_id,
            query="",
            top_k=100,
            memory_types=["preference"]
        )
        
        preferences = {}
        for memory in preference_memories:
            pref_type = memory.metadata.get("preference_type")
            pref_value = memory.metadata.get("preference_value")
            if pref_type and pref_value is not None:
                preferences[pref_type] = pref_value
        
        return preferences
    
    def build_user_context_summary(self, user_id: str, max_context_length: int = 2000) -> str:
        """Build a comprehensive context summary for the user"""
        # Get recent context
        recent_memories = self.vector_store.get_user_context(user_id, context_window=50)
        
        # Categorize memories
        conversations = []
        goals = []
        insights = []
        preferences = []
        
        for memory in recent_memories:
            if memory.type == "conversation":
                conversations.append(memory)
            elif memory.type == "goal_update":
                goals.append(memory)
            elif memory.type == "insight":
                insights.append(memory)
            elif memory.type == "preference":
                preferences.append(memory)
        
        # Build summary
        summary_parts = []
        
        # Recent conversations (last 5)
        if conversations:
            summary_parts.append("=== Recent Conversations ===")
            for conv in conversations[:5]:
                summary_parts.append(f"- {conv.content[:200]}...")
        
        # Current goals
        if goals:
            summary_parts.append("\n=== Goal Updates ===")
            for goal in goals[:3]:
                summary_parts.append(f"- {goal.content[:150]}...")
        
        # Key insights
        if insights:
            summary_parts.append("\n=== Key Insights ===")
            for insight in insights[:3]:
                summary_parts.append(f"- {insight.content}")
        
        # User preferences
        if preferences:
            summary_parts.append("\n=== User Preferences ===")
            for pref in preferences[:5]:
                summary_parts.append(f"- {pref.content[:100]}...")
        
        summary = "\n".join(summary_parts)
        
        # Truncate if too long
        if len(summary) > max_context_length:
            summary = summary[:max_context_length] + "..."
        
        return summary
    
    def find_patterns(self, user_id: str, pattern_type: str = "goal_completion") -> List[Dict[str, Any]]:
        """Analyze memory to find behavioral patterns"""
        memories = self.vector_store.get_user_context(user_id, context_window=200)
        
        patterns = []
        
        if pattern_type == "goal_completion":
            # Analyze goal completion patterns
            goal_memories = [m for m in memories if m.type == "goal_update"]
            
            completion_times = []
            for memory in goal_memories:
                if memory.metadata.get("update_type") == "completed":
                    # Calculate time to completion (simplified)
                    completion_times.append(memory.created_at)
            
            if len(completion_times) >= 2:
                patterns.append({
                    "type": "goal_completion_frequency",
                    "description": f"User typically completes goals every {len(completion_times)} interactions",
                    "data": completion_times
                })
        
        elif pattern_type == "engagement":
            # Analyze conversation engagement patterns
            conv_memories = [m for m in memories if m.type == "conversation"]
            
            daily_conversations = {}
            for memory in conv_memories:
                date = memory.created_at.date()
                daily_conversations[date] = daily_conversations.get(date, 0) + 1
            
            if daily_conversations:
                avg_daily = sum(daily_conversations.values()) / len(daily_conversations)
                patterns.append({
                    "type": "daily_engagement",
                    "description": f"User averages {avg_daily:.1f} conversations per day",
                    "data": daily_conversations
                })
        
        return patterns
    
    def cleanup_old_memories(self, user_id: str, retention_days: int = 365):
        """Clean up old, low-importance memories"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        user_memories = self.vector_store.get_user_context(user_id, context_window=1000)
        
        deleted_count = 0
        for memory in user_memories:
            # Keep high-importance memories and recent memories
            if (memory.created_at < cutoff_date and 
                memory.importance < 0.7 and 
                memory.type not in ["goal_update", "insight"]):
                
                self.vector_store.delete_memory(memory.id, user_id)
                deleted_count += 1
        
        return deleted_count