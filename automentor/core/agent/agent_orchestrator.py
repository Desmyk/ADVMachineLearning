import json
import uuid
import asyncio
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum

from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.agents import Tool, AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from ..memory import MemoryManager, VectorMemoryStore
from ..models import (
    User, Goal, Task, ConversationMessage, AgentAction, 
    GoalStatus, Priority, PlanningSession
)


class AgentState(str, Enum):
    """Current state of the agent"""
    IDLE = "idle"
    LISTENING = "listening"
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"


class AutoMentorAgent:
    """
    Main autonomous agent that orchestrates career coaching activities.
    Handles planning, decision-making, tool invocation, and autonomous actions.
    """
    
    def __init__(self, 
                 openai_api_key: str,
                 memory_manager: MemoryManager,
                 tools: Optional[List[Tool]] = None,
                 model_name: str = "gpt-4-turbo-preview"):
        
        self.memory_manager = memory_manager
        self.llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model_name=model_name,
            temperature=0.7
        )
        
        # Agent state
        self.state = AgentState.IDLE
        self.current_user_id: Optional[str] = None
        self.current_session_id: Optional[str] = None
        
        # Tools for agent capabilities
        self.tools = tools or []
        self.tool_map = {tool.name: tool for tool in self.tools}
        
        # Planning and execution
        self.planning_steps = []
        self.current_plan_step = 0
        self.max_planning_steps = 10
        
        # Autonomous behavior settings
        self.autonomous_mode = True
        self.check_in_frequency = timedelta(days=7)  # Weekly check-ins
        self.last_autonomous_action = {}  # user_id -> datetime
        
        self._setup_agent_prompts()
    
    def _setup_agent_prompts(self):
        """Set up the core agent prompts for different scenarios"""
        
        self.system_prompt = """You are AutoMentor, an autonomous AI career coach. Your role is to:

1. **GOAL-ORIENTED**: Help users set, plan, and achieve career goals using SMART criteria
2. **PROACTIVE**: Take initiative to check progress, suggest actions, and provide reminders
3. **MEMORY-AWARE**: Remember past conversations, goals, preferences, and context
4. **TOOL-USING**: Leverage available tools for job search, resume building, scheduling
5. **ADAPTIVE**: Adjust plans based on progress, feedback, and changing circumstances

Core Behaviors:
- Ask clarifying questions to understand user's career aspirations
- Break down large goals into actionable steps with timelines
- Provide personalized recommendations based on user's background
- Proactively check in on goal progress
- Suggest learning resources, networking opportunities, and job applications
- Celebrate achievements and help overcome obstacles

Remember: You are autonomous - take initiative, make suggestions, and drive conversations forward while being helpful and supportive."""

        self.planning_prompt = """Given the user's career goal and current context, create a detailed action plan.

User Context: {user_context}
Goal: {goal_description}
Timeline: {timeline}

Create a step-by-step plan that includes:
1. Immediate actions (this week)
2. Short-term milestones (1-2 months)
3. Medium-term objectives (3-6 months)
4. Resources needed (courses, tools, contacts)
5. Success metrics and checkpoints

Be specific, actionable, and realistic. Consider the user's current skills and constraints."""

        self.reflection_prompt = """Analyze the user's progress and current situation to provide insights and adjustments.

User Context: {user_context}
Goal Progress: {goal_progress}
Recent Activities: {recent_activities}
Time Since Last Check: {time_elapsed}

Provide:
1. Progress assessment (what's working, what's not)
2. Insights about patterns or obstacles
3. Plan adjustments if needed
4. Encouragement and next steps
5. Any proactive actions to take"""

        self.autonomous_action_prompt = """Determine if autonomous action is needed for this user.

User Context: {user_context}
Last Interaction: {last_interaction}
Active Goals: {active_goals}
Time Since Last Contact: {time_since_contact}

Consider if you should:
1. Send a progress check-in
2. Provide a reminder about upcoming deadlines
3. Share relevant job opportunities
4. Suggest learning resources
5. Celebrate recent achievements

If action is needed, specify the action type and content."""
    
    async def start_conversation(self, user_id: str, message: str) -> str:
        """Start or continue a conversation with a user"""
        self.current_user_id = user_id
        self.current_session_id = str(uuid.uuid4())
        self.state = AgentState.LISTENING
        
        # Store the user message
        user_msg = ConversationMessage(
            id=str(uuid.uuid4()),
            user_id=user_id,
            role="user",
            content=message
        )
        self.memory_manager.store_conversation(user_id, user_msg)
        
        # Get user context
        user_context = self.memory_manager.build_user_context_summary(user_id)
        
        # Generate response
        response = await self._generate_response(user_id, message, user_context)
        
        # Store assistant response
        assistant_msg = ConversationMessage(
            id=str(uuid.uuid4()),
            user_id=user_id,
            role="assistant",
            content=response
        )
        self.memory_manager.store_conversation(user_id, assistant_msg)
        
        # Check if autonomous action is needed
        await self._check_autonomous_actions(user_id)
        
        return response
    
    async def _generate_response(self, user_id: str, message: str, context: str) -> str:
        """Generate a response using the LLM with context"""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"User Context:\n{context}\n\nUser Message: {message}")
        ]
        
        # Add recent conversation history
        recent_conversations = self.memory_manager.get_conversation_history(user_id, limit=10)
        for conv in recent_conversations[-5:]:  # Last 5 exchanges
            if conv.metadata.get("role") == "user":
                messages.append(HumanMessage(content=conv.content.split("Content: ", 1)[1]))
            elif conv.metadata.get("role") == "assistant":
                messages.append(AIMessage(content=conv.content.split("Content: ", 1)[1]))
        
        response = await self.llm.agenerate([messages])
        return response.generations[0][0].text
    
    async def create_goal_plan(self, user_id: str, goal: Goal) -> Dict[str, Any]:
        """Create a detailed plan for achieving a goal"""
        self.state = AgentState.PLANNING
        
        user_context = self.memory_manager.build_user_context_summary(user_id)
        
        planning_input = {
            "user_context": user_context,
            "goal_description": f"{goal.title}: {goal.description}",
            "timeline": str(goal.time_bound)
        }
        
        prompt = self.planning_prompt.format(**planning_input)
        
        messages = [
            SystemMessage(content="You are a strategic career planning assistant."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.agenerate([messages])
        plan_content = response.generations[0][0].text
        
        # Store planning session
        planning_session = PlanningSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            goal_id=goal.id,
            session_type="initial_planning",
            inputs=planning_input,
            outputs={"plan": plan_content},
            reasoning=plan_content
        )
        
        # Store as memory
        self.memory_manager.store_insight(
            user_id=user_id,
            insight=f"Created detailed plan for goal: {goal.title}",
            source="planning_engine",
            related_items=[goal.id]
        )
        
        return {
            "session_id": planning_session.id,
            "plan": plan_content,
            "next_actions": self._extract_next_actions(plan_content)
        }
    
    def _extract_next_actions(self, plan_content: str) -> List[Dict[str, Any]]:
        """Extract actionable next steps from plan content"""
        # This is a simplified extraction - in production, you'd use more sophisticated NLP
        next_actions = []
        
        lines = plan_content.split('\n')
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['action:', '1.', 'step:', 'task:', 'todo:']):
                if len(line) > 10:  # Filter out very short lines
                    next_actions.append({
                        "action": line,
                        "priority": "medium",
                        "estimated_time": "1-2 hours"
                    })
        
        return next_actions[:5]  # Return top 5 actions
    
    async def reflect_on_progress(self, user_id: str, goal_id: Optional[str] = None) -> Dict[str, Any]:
        """Analyze user's progress and provide insights"""
        self.state = AgentState.REFLECTING
        
        user_context = self.memory_manager.build_user_context_summary(user_id)
        goal_history = self.memory_manager.get_goal_history(user_id, goal_id)
        recent_conversations = self.memory_manager.get_conversation_history(user_id, limit=10)
        
        # Calculate time since last interaction
        last_interaction = recent_conversations[0].created_at if recent_conversations else datetime.now()
        time_elapsed = datetime.now() - last_interaction
        
        reflection_input = {
            "user_context": user_context,
            "goal_progress": "\n".join([g.content for g in goal_history[:5]]),
            "recent_activities": "\n".join([c.content[:100] for c in recent_conversations[:3]]),
            "time_elapsed": str(time_elapsed.days) + " days"
        }
        
        prompt = self.reflection_prompt.format(**reflection_input)
        
        messages = [
            SystemMessage(content="You are analyzing user progress and providing insights."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.agenerate([messages])
        reflection_content = response.generations[0][0].text
        
        # Store reflection insights
        self.memory_manager.store_insight(
            user_id=user_id,
            insight=reflection_content,
            source="reflection_engine",
            related_items=[goal_id] if goal_id else []
        )
        
        return {
            "reflection": reflection_content,
            "patterns": self.memory_manager.find_patterns(user_id),
            "recommendations": self._extract_recommendations(reflection_content)
        }
    
    def _extract_recommendations(self, reflection_content: str) -> List[str]:
        """Extract actionable recommendations from reflection"""
        recommendations = []
        lines = reflection_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'try', 'consider']):
                if len(line) > 20:
                    recommendations.append(line)
        
        return recommendations[:3]
    
    async def _check_autonomous_actions(self, user_id: str):
        """Check if autonomous actions are needed for the user"""
        if not self.autonomous_mode:
            return
        
        # Check when we last took autonomous action
        last_action_time = self.last_autonomous_action.get(user_id, datetime.min)
        time_since_action = datetime.now() - last_action_time
        
        if time_since_action < self.check_in_frequency:
            return  # Too soon for another autonomous action
        
        user_context = self.memory_manager.build_user_context_summary(user_id)
        recent_conversations = self.memory_manager.get_conversation_history(user_id, limit=5)
        goal_history = self.memory_manager.get_goal_history(user_id)
        
        last_interaction = recent_conversations[0].created_at if recent_conversations else datetime.min
        time_since_contact = datetime.now() - last_interaction
        
        autonomous_input = {
            "user_context": user_context,
            "last_interaction": last_interaction.isoformat(),
            "active_goals": "\n".join([g.content for g in goal_history[:3]]),
            "time_since_contact": str(time_since_contact.days) + " days"
        }
        
        prompt = self.autonomous_action_prompt.format(**autonomous_input)
        
        messages = [
            SystemMessage(content="Determine if autonomous action is needed."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.agenerate([messages])
        action_analysis = response.generations[0][0].text
        
        # Simple check for action keywords (in production, use more sophisticated parsing)
        if any(keyword in action_analysis.lower() for keyword in ['yes', 'action needed', 'should', 'recommend']):
            await self._take_autonomous_action(user_id, action_analysis)
    
    async def _take_autonomous_action(self, user_id: str, action_description: str):
        """Take an autonomous action for the user"""
        action_id = str(uuid.uuid4())
        
        # Record the autonomous action
        autonomous_action = AgentAction(
            id=action_id,
            user_id=user_id,
            action_type="autonomous_check_in",
            description=action_description,
            success=True,
            metadata={"triggered_by": "time_based_check"}
        )
        
        # Store as memory
        self.memory_manager.store_insight(
            user_id=user_id,
            insight=f"Autonomous action taken: {action_description}",
            source="autonomous_agent"
        )
        
        # Update last action time
        self.last_autonomous_action[user_id] = datetime.now()
        
        # In a real system, this would trigger notifications, emails, etc.
        print(f"Autonomous action for user {user_id}: {action_description}")
    
    async def use_tool(self, tool_name: str, user_id: str, **kwargs) -> Any:
        """Use a specific tool"""
        if tool_name not in self.tool_map:
            raise ValueError(f"Tool {tool_name} not available")
        
        tool = self.tool_map[tool_name]
        
        try:
            result = await tool.arun(**kwargs) if hasattr(tool, 'arun') else tool.run(**kwargs)
            
            # Record tool usage
            self.memory_manager.store_insight(
                user_id=user_id,
                insight=f"Used tool {tool_name} with result: {str(result)[:200]}",
                source="tool_usage"
            )
            
            return result
        except Exception as e:
            # Record tool failure
            self.memory_manager.store_insight(
                user_id=user_id,
                insight=f"Tool {tool_name} failed: {str(e)}",
                source="tool_error"
            )
            raise e
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "state": self.state.value,
            "current_user": self.current_user_id,
            "session_id": self.current_session_id,
            "autonomous_mode": self.autonomous_mode,
            "available_tools": [tool.name for tool in self.tools],
            "last_autonomous_actions": {
                user_id: action_time.isoformat() 
                for user_id, action_time in self.last_autonomous_action.items()
            }
        }
    
    def set_autonomous_mode(self, enabled: bool):
        """Enable or disable autonomous behavior"""
        self.autonomous_mode = enabled
    
    def add_tool(self, tool: Tool):
        """Add a new tool to the agent's capabilities"""
        self.tools.append(tool)
        self.tool_map[tool.name] = tool