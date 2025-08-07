import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.memory import VectorMemoryStore, MemoryManager
from core.models import MemoryEntry, User, Goal, ConversationMessage, GoalStatus, Priority


class TestVectorMemoryStore:
    """Test cases for VectorMemoryStore"""
    
    @pytest.fixture
    def temp_store_path(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def memory_store(self, temp_store_path):
        """Create VectorMemoryStore instance for testing"""
        with patch('core.memory.vector_store.SentenceTransformer') as mock_transformer:
            # Mock the sentence transformer
            mock_model = Mock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_model.encode.return_value = [[0.1] * 384]  # Mock embedding
            mock_transformer.return_value = mock_model
            
            store = VectorMemoryStore(
                model_name="mock-model",
                store_path=temp_store_path
            )
            yield store
    
    def test_add_memory(self, memory_store):
        """Test adding a memory to the store"""
        user_id = "test_user_001"
        content = "User wants to become a frontend developer"
        
        memory_id = memory_store.add_memory(
            user_id=user_id,
            content=content,
            memory_type="conversation",
            importance=0.8
        )
        
        assert memory_id is not None
        assert user_id in memory_store.user_memories
        assert memory_id in memory_store.user_memories[user_id]
        
        # Verify memory content
        memory = memory_store.get_memory_by_id(memory_id)
        assert memory is not None
        assert memory.content == content
        assert memory.user_id == user_id
        assert memory.importance == 0.8
    
    def test_search_memories(self, memory_store):
        """Test searching for memories"""
        user_id = "test_user_001"
        
        # Add test memories
        memory_store.add_memory(user_id, "Learning React", "conversation")
        memory_store.add_memory(user_id, "Job search strategy", "conversation")
        memory_store.add_memory(user_id, "Frontend development goals", "goal_update")
        
        # Search for memories
        results = memory_store.search_memories(
            user_id=user_id,
            query="React development",
            top_k=2
        )
        
        assert len(results) >= 1
        assert all(result.user_id == user_id for result in results)
    
    def test_get_user_context(self, memory_store):
        """Test getting user context"""
        user_id = "test_user_001"
        
        # Add multiple memories
        for i in range(5):
            memory_store.add_memory(
                user_id=user_id,
                content=f"Memory {i}",
                memory_type="conversation",
                importance=0.5 + i * 0.1
            )
        
        context = memory_store.get_user_context(user_id, context_window=3)
        
        assert len(context) <= 3
        assert all(memory.user_id == user_id for memory in context)
    
    def test_update_memory_importance(self, memory_store):
        """Test updating memory importance"""
        user_id = "test_user_001"
        content = "Important career insight"
        
        memory_id = memory_store.add_memory(user_id, content, importance=0.5)
        
        # Update importance
        memory_store.update_memory_importance(memory_id, 0.9)
        
        memory = memory_store.get_memory_by_id(memory_id)
        assert memory.importance == 0.9
    
    def test_get_memory_stats(self, memory_store):
        """Test memory statistics"""
        user_id = "test_user_001"
        
        # Add memories of different types
        memory_store.add_memory(user_id, "Conversation 1", "conversation")
        memory_store.add_memory(user_id, "Goal update", "goal_update")
        memory_store.add_memory(user_id, "Insight", "insight")
        
        stats = memory_store.get_memory_stats(user_id)
        
        assert stats["total_memories"] == 3
        assert "conversation" in stats["memory_types"]
        assert "goal_update" in stats["memory_types"]
        assert "insight" in stats["memory_types"]
        assert stats["average_importance"] > 0


class TestMemoryManager:
    """Test cases for MemoryManager"""
    
    @pytest.fixture
    def memory_manager(self):
        """Create MemoryManager for testing"""
        with patch('core.memory.vector_store.SentenceTransformer'):
            vector_store = Mock(spec=VectorMemoryStore)
            vector_store.add_memory.return_value = "mock_memory_id"
            vector_store.search_memories.return_value = []
            vector_store.get_user_context.return_value = []
            
            manager = MemoryManager(vector_store)
            yield manager
    
    def test_store_conversation(self, memory_manager):
        """Test storing conversation messages"""
        user_id = "test_user_001"
        message = ConversationMessage(
            id="msg_001",
            user_id=user_id,
            role="user",
            content="I want to learn React"
        )
        
        memory_id = memory_manager.store_conversation(user_id, message)
        
        assert memory_id == "mock_memory_id"
        memory_manager.vector_store.add_memory.assert_called_once()
    
    def test_store_goal_update(self, memory_manager):
        """Test storing goal updates"""
        user_id = "test_user_001"
        goal = Goal(
            id="goal_001",
            user_id=user_id,
            title="Learn React",
            description="Master React development",
            specific="Learn React fundamentals",
            measurable="Complete 3 projects",
            achievable="Dedicate 10 hours per week",
            relevant="For frontend career",
            time_bound=datetime.now().date() + timedelta(days=90),
            progress=25.0
        )
        
        memory_id = memory_manager.store_goal_update(
            user_id=user_id,
            goal=goal,
            update_type="progress_update"
        )
        
        assert memory_id == "mock_memory_id"
        memory_manager.vector_store.add_memory.assert_called_once()
    
    def test_store_insight(self, memory_manager):
        """Test storing insights"""
        user_id = "test_user_001"
        insight = "User shows consistent learning patterns"
        
        memory_id = memory_manager.store_insight(
            user_id=user_id,
            insight=insight,
            source="agent_analysis"
        )
        
        assert memory_id == "mock_memory_id"
        memory_manager.vector_store.add_memory.assert_called_once()
    
    def test_store_user_preference(self, memory_manager):
        """Test storing user preferences"""
        user_id = "test_user_001"
        
        memory_id = memory_manager.store_user_preference(
            user_id=user_id,
            preference_type="learning_style",
            preference_value="visual",
            context="Prefers video tutorials over text"
        )
        
        assert memory_id == "mock_memory_id"
        memory_manager.vector_store.add_memory.assert_called_once()
    
    def test_get_relevant_context(self, memory_manager):
        """Test getting relevant context"""
        user_id = "test_user_001"
        query = "React learning"
        
        # Mock return value
        mock_memory = Mock(spec=MemoryEntry)
        memory_manager.vector_store.search_memories.return_value = [mock_memory]
        
        context = memory_manager.get_relevant_context(user_id, query)
        
        assert len(context) == 1
        assert context[0] == mock_memory
        memory_manager.vector_store.search_memories.assert_called_once_with(
            user_id=user_id,
            query=query,
            top_k=10,
            memory_types=None
        )
    
    def test_build_user_context_summary(self, memory_manager):
        """Test building user context summary"""
        user_id = "test_user_001"
        
        # Mock memories
        mock_memories = [
            Mock(spec=MemoryEntry, type="conversation", content="Role: user\nContent: I want to learn React"),
            Mock(spec=MemoryEntry, type="goal_update", content="Goal Update - created\nGoal: Learn React"),
            Mock(spec=MemoryEntry, type="insight", content="User shows consistent engagement"),
        ]
        memory_manager.vector_store.get_user_context.return_value = mock_memories
        
        summary = memory_manager.build_user_context_summary(user_id)
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "Recent Conversations" in summary or "Goal Updates" in summary


class TestMemoryIntegration:
    """Integration tests for memory system"""
    
    @pytest.fixture
    def temp_store_path(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def memory_system(self, temp_store_path):
        """Create complete memory system for integration testing"""
        with patch('core.memory.vector_store.SentenceTransformer') as mock_transformer:
            # Mock the sentence transformer
            mock_model = Mock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_model.encode.return_value = [[0.1] * 384]
            mock_transformer.return_value = mock_model
            
            vector_store = VectorMemoryStore(store_path=temp_store_path)
            memory_manager = MemoryManager(vector_store)
            
            yield memory_manager
    
    def test_full_conversation_workflow(self, memory_system):
        """Test complete conversation memory workflow"""
        user_id = "test_user_001"
        
        # Simulate conversation
        messages = [
            ConversationMessage(
                id="msg_001", user_id=user_id, role="user",
                content="I want to become a frontend developer"
            ),
            ConversationMessage(
                id="msg_002", user_id=user_id, role="assistant",
                content="Great! Let's start by learning React. What's your timeline?"
            ),
            ConversationMessage(
                id="msg_003", user_id=user_id, role="user",
                content="I want to be job-ready in 6 months"
            )
        ]
        
        # Store all messages
        for message in messages:
            memory_system.store_conversation(user_id, message)
        
        # Test retrieval
        context = memory_system.get_conversation_history(user_id, limit=5)
        assert len(context) == 3
        
        # Test search
        results = memory_system.get_relevant_context(user_id, "frontend developer")
        assert len(results) > 0
    
    def test_goal_lifecycle_memory(self, memory_system):
        """Test goal lifecycle memory tracking"""
        user_id = "test_user_001"
        
        # Create goal
        goal = Goal(
            id="goal_001",
            user_id=user_id,
            title="Learn React Development",
            description="Master React for frontend development",
            specific="Learn React fundamentals and build 3 projects",
            measurable="Complete course and portfolio projects",
            achievable="Study 10 hours per week",
            relevant="For frontend developer career",
            time_bound=datetime.now().date() + timedelta(days=90),
            status=GoalStatus.PLANNING,
            progress=0.0
        )
        
        # Store goal creation
        memory_system.store_goal_update(user_id, goal, "created")
        
        # Update progress multiple times
        for progress in [25, 50, 75, 100]:
            goal.progress = progress
            if progress == 100:
                goal.status = GoalStatus.COMPLETED
            else:
                goal.status = GoalStatus.ACTIVE
            
            memory_system.store_goal_update(
                user_id, goal, "progress_update",
                previous_state={"progress": progress - 25}
            )
        
        # Test goal history retrieval
        goal_history = memory_system.get_goal_history(user_id, goal.id)
        assert len(goal_history) >= 5  # Creation + 4 updates
        
        # Test insights storage
        memory_system.store_insight(
            user_id=user_id,
            insight="User completed React goal ahead of schedule",
            source="progress_analysis",
            related_items=[goal.id]
        )
        
        insights = memory_system.get_user_insights(user_id)
        assert len(insights) >= 1