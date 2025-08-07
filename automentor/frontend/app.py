import streamlit as st
import sys
import os
import json
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import User, Goal, GoalStatus, Priority, SkillLevel
from core.memory import VectorMemoryStore, MemoryManager
from core.agent.agent_orchestrator import AutoMentorAgent
from core.planning.goal_manager import GoalManager
from core.planning.task_planner import TaskPlanner
from tools.job_search.job_api import JobSearchAPI, JobSearchFilters
from tools.resume.resume_generator import ResumeGenerator
from tools.calendar.scheduler import CareerScheduler

# Page configuration
st.set_page_config(
    page_title="AutoMentor - AI Career Coach",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'memory_manager' not in st.session_state:
    st.session_state.memory_manager = None
if 'goal_manager' not in st.session_state:
    st.session_state.goal_manager = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1E88E5;
        margin-bottom: 2rem;
    }
    .goal-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1E88E5;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
    }
    .user-message {
        background-color: #e8f5e8;
        margin-left: 2rem;
    }
    .assistant-message {
        background-color: #f0f0f0;
        margin-right: 2rem;
    }
</style>
""", unsafe_allow_html=True)

def initialize_system():
    """Initialize the AutoMentor system components"""
    if st.session_state.memory_manager is None:
        # Initialize memory system
        vector_store = VectorMemoryStore()
        st.session_state.memory_manager = MemoryManager(vector_store)
        
        # Initialize goal manager
        st.session_state.goal_manager = GoalManager(st.session_state.memory_manager)
        
        # Initialize other components (mock OPENAI key for demo)
        st.session_state.agent = AutoMentorAgent(
            openai_api_key="demo_key",  # Would use real key in production
            memory_manager=st.session_state.memory_manager
        )

def create_demo_user():
    """Create a demo user for testing"""
    demo_user = User(
        id="demo_user_001",
        name="Alex Developer",
        email="alex@example.com",
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
    return demo_user

def sidebar_navigation():
    """Create sidebar navigation"""
    st.sidebar.title("🎯 AutoMentor")
    st.sidebar.markdown("*Your AI Career Coach*")
    
    # User profile section
    st.sidebar.subheader("👤 Profile")
    if st.session_state.user:
        st.sidebar.write(f"**{st.session_state.user.name}**")
        st.sidebar.write(f"📧 {st.session_state.user.email}")
        st.sidebar.write(f"💼 {st.session_state.user.current_role}")
        st.sidebar.write(f"📍 {st.session_state.user.location}")
    else:
        if st.sidebar.button("🚀 Start Demo"):
            st.session_state.user = create_demo_user()
            st.rerun()
    
    st.sidebar.divider()
    
    # Navigation menu
    page = st.sidebar.selectbox(
        "Navigate to:",
        ["💬 Chat", "🎯 Goals", "📊 Dashboard", "🔍 Job Search", "📄 Resume", "📅 Calendar"]
    )
    
    return page

def chat_page():
    """Chat interface page"""
    st.markdown('<h1 class="main-header">💬 Chat with AutoMentor</h1>', unsafe_allow_html=True)
    
    if not st.session_state.user:
        st.warning("Please start the demo from the sidebar to begin chatting!")
        return
    
    # Chat container
    chat_container = st.container()
    
    # Display chat history
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>', 
                          unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message assistant-message"><strong>AutoMentor:</strong> {message["content"]}</div>', 
                          unsafe_allow_html=True)
    
    # Chat input
    user_input = st.chat_input("Ask AutoMentor about your career goals...")
    
    if user_input:
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Generate mock response (would use real agent in production)
        response = generate_mock_response(user_input)
        
        # Add agent response to history
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        st.rerun()

def generate_mock_response(user_input: str) -> str:
    """Generate mock agent response"""
    input_lower = user_input.lower()
    
    if any(word in input_lower for word in ["goal", "want", "become", "achieve"]):
        return """I'd love to help you set and achieve your career goals! 

Based on your profile, I can see you're a Junior Developer with 2 years of experience. Here are some potential goals we could work on:

🎯 **Short-term (3-6 months):**
- Master React for frontend development
- Build a portfolio of 3-5 projects
- Improve problem-solving skills

🎯 **Medium-term (6-12 months):**
- Advance to Mid-level Developer role
- Learn a new technology stack
- Contribute to open source projects

🎯 **Long-term (1-2 years):**
- Senior Developer position
- Specialize in a particular domain
- Lead technical projects

Would you like to set a specific SMART goal? I can help you break it down into actionable steps!"""

    elif any(word in input_lower for word in ["job", "position", "role", "career"]):
        return """Let me help you explore career opportunities! 

Based on your skills in Python, JavaScript, and SQL, here are some relevant paths:

💼 **Immediate Opportunities:**
- Full-stack Developer positions
- Frontend Developer (React-focused)
- Backend Developer (Python)
- Junior Data Analyst roles

📈 **Growth Trajectories:**
- Senior Developer → Tech Lead → Engineering Manager
- Specialist → Senior Specialist → Principal Engineer
- Full-stack → Product Engineer → Product Manager

I can help you:
✅ Search for relevant job openings
✅ Tailor your resume for specific roles
✅ Prepare for technical interviews
✅ Plan your skill development

What type of role interests you most?"""

    elif any(word in input_lower for word in ["learn", "study", "skill", "improve"]):
        return """Great question about skill development! 

Based on your current skills and interests, here are my recommendations:

🎓 **Priority Skills to Develop:**
1. **React** (you marked as beginner) - High demand for frontend roles
2. **Node.js** - Complete your full-stack capabilities  
3. **Database Design** - Complement your SQL skills
4. **System Design** - Essential for senior roles

📚 **Learning Path:**
- **Week 1-4:** React fundamentals and hooks
- **Week 5-8:** Build 2 React projects
- **Week 9-12:** Node.js and API development
- **Week 13-16:** Full-stack project combining all skills

🛠 **Resources I recommend:**
- FreeCodeCamp React course
- The Odin Project full-stack path
- LeetCode for problem-solving
- GitHub for portfolio projects

Would you like me to create a detailed learning schedule and track your progress?"""

    else:
        return """Hello! I'm AutoMentor, your AI career coach. I'm here to help you:

🎯 Set and achieve career goals
📈 Plan your professional development  
🔍 Find relevant job opportunities
📄 Improve your resume and applications
📅 Schedule learning and networking activities
💡 Provide personalized career advice

What would you like to work on today? You can ask me about:
- Setting career goals
- Job search strategies  
- Skill development plans
- Interview preparation
- Career transitions

How can I help you advance your career?"""

def goals_page():
    """Goals management page"""
    st.markdown('<h1 class="main-header">🎯 Your Career Goals</h1>', unsafe_allow_html=True)
    
    if not st.session_state.user:
        st.warning("Please start the demo from the sidebar!")
        return
    
    # Tabs for different goal views
    tab1, tab2, tab3 = st.tabs(["📋 Current Goals", "➕ Create Goal", "📊 Analytics"])
    
    with tab1:
        st.subheader("Your Active Goals")
        
        # Mock goals for demo
        mock_goals = [
            {
                "title": "Learn React Development",
                "description": "Master React fundamentals and build 3 projects",
                "deadline": date.today() + timedelta(days=90),
                "progress": 35,
                "status": "Active",
                "priority": "High"
            },
            {
                "title": "Get Frontend Developer Job",
                "description": "Secure a frontend developer position at a tech company",
                "deadline": date.today() + timedelta(days=180),
                "progress": 15,
                "status": "Planning",
                "priority": "High"
            }
        ]
        
        for goal in mock_goals:
            with st.container():
                st.markdown('<div class="goal-card">', unsafe_allow_html=True)
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{goal['title']}**")
                    st.write(goal['description'])
                    st.write(f"📅 Due: {goal['deadline']}")
                
                with col2:
                    st.metric("Progress", f"{goal['progress']}%")
                    st.progress(goal['progress'] / 100)
                
                with col3:
                    st.write(f"**Status:** {goal['status']}")
                    st.write(f"**Priority:** {goal['priority']}")
                    if st.button("View Details", key=f"view_{goal['title']}"):
                        st.info("Goal details would show planning breakdown, tasks, and timeline")
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.subheader("Create New SMART Goal")
        
        with st.form("goal_creation"):
            goal_title = st.text_input("Goal Title", placeholder="e.g., Learn Python Programming")
            goal_description = st.text_area("Goal Description", 
                                           placeholder="Describe what you want to achieve...")
            
            col1, col2 = st.columns(2)
            with col1:
                goal_deadline = st.date_input("Target Completion Date", 
                                            value=date.today() + timedelta(days=90))
                priority = st.selectbox("Priority", ["Low", "Medium", "High"])
            
            with col2:
                category = st.selectbox("Category", 
                                      ["Skill Development", "Job Search", "Networking", "Project"])
                difficulty = st.selectbox("Difficulty", ["Beginner", "Intermediate", "Advanced"])
            
            submitted = st.form_submit_button("Create Goal")
            
            if submitted and goal_title:
                st.success(f"Goal '{goal_title}' created successfully!")
                st.info("AutoMentor will now create a detailed action plan with tasks, timeline, and milestones.")
    
    with tab3:
        st.subheader("Goal Analytics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Goals", "2")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Completed", "0")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("In Progress", "2")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Avg Progress", "25%")
            st.markdown('</div>', unsafe_allow_html=True)

def dashboard_page():
    """Main dashboard page"""
    st.markdown('<h1 class="main-header">📊 Career Dashboard</h1>', unsafe_allow_html=True)
    
    if not st.session_state.user:
        st.warning("Please start the demo from the sidebar!")
        return
    
    # Overview metrics
    st.subheader("📈 Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Active Goals", "2", delta="1")
    with col2:
        st.metric("Completed Tasks", "8", delta="3")
    with col3:
        st.metric("Job Applications", "5", delta="2")
    with col4:
        st.metric("Learning Hours", "24", delta="6")
    
    st.divider()
    
    # Recent activity and upcoming events
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Recent Activity")
        activities = [
            "✅ Completed React Tutorial - Chapter 3",
            "📄 Updated resume with new skills",
            "🔍 Applied to Frontend Developer position at TechCorp",
            "📚 Studied JavaScript ES6 features",
            "💼 Networked with 3 professionals on LinkedIn"
        ]
        
        for activity in activities:
            st.write(activity)
    
    with col2:
        st.subheader("📅 Upcoming Events")
        events = [
            {"title": "React Study Session", "date": "Tomorrow, 7:00 PM", "type": "learning"},
            {"title": "Technical Interview Prep", "date": "Thursday, 6:00 PM", "type": "interview"},
            {"title": "Goal Progress Review", "date": "Friday, 5:00 PM", "type": "review"},
            {"title": "Job Application Deadline", "date": "Monday, 11:59 PM", "type": "deadline"}
        ]
        
        for event in events:
            icon = {"learning": "📚", "interview": "💼", "review": "🎯", "deadline": "⏰"}.get(event["type"], "📅")
            st.write(f"{icon} **{event['title']}**")
            st.write(f"   {event['date']}")

def job_search_page():
    """Job search interface"""
    st.markdown('<h1 class="main-header">🔍 Job Search</h1>', unsafe_allow_html=True)
    
    if not st.session_state.user:
        st.warning("Please start the demo from the sidebar!")
        return
    
    # Search filters
    st.subheader("Search Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        keywords = st.text_input("Keywords", value="React Developer")
        location = st.text_input("Location", value="San Francisco, CA")
    
    with col2:
        job_type = st.selectbox("Job Type", ["All", "Full-time", "Part-time", "Contract", "Remote"])
        experience_level = st.selectbox("Experience Level", ["All", "Entry", "Mid", "Senior"])
    
    with col3:
        remote_ok = st.checkbox("Include Remote", value=True)
        posted_within = st.selectbox("Posted Within", ["1 day", "3 days", "1 week", "2 weeks", "1 month"])
    
    if st.button("🔍 Search Jobs"):
        st.subheader("Job Results")
        
        # Mock job results
        jobs = [
            {
                "title": "Frontend React Developer",
                "company": "TechStart Inc",
                "location": "San Francisco, CA",
                "salary": "$90,000 - $120,000",
                "type": "Full-time",
                "posted": "2 days ago",
                "match": 95,
                "description": "Join our team building modern web applications with React and TypeScript..."
            },
            {
                "title": "Junior Full Stack Developer",
                "company": "DevCorp Solutions",
                "location": "Remote",
                "salary": "$75,000 - $95,000",
                "type": "Full-time",
                "posted": "1 day ago",
                "match": 88,
                "description": "Looking for a passionate developer to work on our SaaS platform..."
            },
            {
                "title": "React Developer Intern",
                "company": "Innovation Labs",
                "location": "San Francisco, CA",
                "salary": "$25 - $35/hour",
                "type": "Internship",
                "posted": "3 days ago",
                "match": 75,
                "description": "Summer internship opportunity for aspiring frontend developers..."
            }
        ]
        
        for job in jobs:
            with st.expander(f"{job['title']} at {job['company']} - {job['match']}% match"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Company:** {job['company']}")
                    st.write(f"**Location:** {job['location']}")
                    st.write(f"**Salary:** {job['salary']}")
                    st.write(f"**Type:** {job['type']}")
                    st.write(f"**Posted:** {job['posted']}")
                    st.write(f"**Description:** {job['description']}")
                
                with col2:
                    st.metric("Match Score", f"{job['match']}%")
                    st.button("💾 Save Job", key=f"save_{job['title']}")
                    st.button("📄 Apply Now", key=f"apply_{job['title']}")

def resume_page():
    """Resume management page"""
    st.markdown('<h1 class="main-header">📄 Resume Builder</h1>', unsafe_allow_html=True)
    
    if not st.session_state.user:
        st.warning("Please start the demo from the sidebar!")
        return
    
    tab1, tab2, tab3 = st.tabs(["📝 Generate Resume", "💡 Suggestions", "📊 Analysis"])
    
    with tab1:
        st.subheader("Generate Tailored Resume")
        
        col1, col2 = st.columns(2)
        
        with col1:
            template = st.selectbox("Template", ["Modern Professional", "Technical", "Creative"])
            format_type = st.selectbox("Format", ["PDF", "DOCX"])
            
        with col2:
            target_job = st.text_input("Target Job Title (optional)", 
                                     placeholder="e.g., Frontend Developer")
            keywords = st.text_input("Keywords to emphasize", 
                                    placeholder="React, JavaScript, Python")
        
        if st.button("🎯 Generate Resume"):
            with st.spinner("Generating your tailored resume..."):
                st.success("Resume generated successfully!")
                st.info("Your resume has been optimized based on your profile and target role.")
                
                # Mock download button
                st.download_button(
                    label="📥 Download Resume",
                    data="Mock resume content",
                    file_name=f"resume_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
    
    with tab2:
        st.subheader("Resume Improvement Suggestions")
        
        suggestions = [
            "✅ Add quantifiable achievements (e.g., 'Improved app performance by 30%')",
            "✅ Include more technical keywords relevant to your target role",
            "✅ Add links to your GitHub profile and portfolio projects",
            "⚠️ Consider adding a professional summary section",
            "⚠️ Include relevant certifications or online courses completed",
            "💡 Highlight your open source contributions",
            "💡 Add specific technologies used in each project"
        ]
        
        for suggestion in suggestions:
            st.write(suggestion)
    
    with tab3:
        st.subheader("Resume Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("ATS Score", "78/100", delta="5")
            st.metric("Keyword Match", "65%", delta="10%")
            st.metric("Sections Complete", "6/8", delta="1")
        
        with col2:
            st.write("**Strengths:**")
            st.write("• Strong technical skills section")
            st.write("• Clear project descriptions")
            st.write("• Good formatting and readability")
            
            st.write("**Areas for Improvement:**")
            st.write("• Add more quantified achievements")
            st.write("• Include professional summary")
            st.write("• Add relevant certifications")

def calendar_page():
    """Calendar and scheduling page"""
    st.markdown('<h1 class="main-header">📅 Career Calendar</h1>', unsafe_allow_html=True)
    
    if not st.session_state.user:
        st.warning("Please start the demo from the sidebar!")
        return
    
    tab1, tab2, tab3 = st.tabs(["📅 Upcoming Events", "➕ Schedule Activity", "📊 Calendar Analytics"])
    
    with tab1:
        st.subheader("Upcoming Events")
        
        events = [
            {
                "title": "React Learning Session",
                "date": "Tomorrow",
                "time": "7:00 PM - 9:00 PM",
                "type": "Learning",
                "priority": "High",
                "description": "Chapter 4: State Management and Hooks"
            },
            {
                "title": "Weekly Goal Review",
                "date": "Friday",
                "time": "5:00 PM - 5:30 PM", 
                "type": "Review",
                "priority": "Medium",
                "description": "Review progress on React learning goal"
            },
            {
                "title": "Technical Interview Prep",
                "date": "Next Monday",
                "time": "6:00 PM - 8:00 PM",
                "type": "Interview Prep",
                "priority": "High",
                "description": "Practice coding problems and system design"
            }
        ]
        
        for event in events:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{event['title']}**")
                    st.write(f"📅 {event['date']} • {event['time']}")
                    st.write(event['description'])
                
                with col2:
                    st.write(f"**Type:** {event['type']}")
                    st.write(f"**Priority:** {event['priority']}")
                
                with col3:
                    st.button("✏️ Edit", key=f"edit_{event['title']}")
                    st.button("❌ Cancel", key=f"cancel_{event['title']}")
                
                st.divider()
    
    with tab2:
        st.subheader("Schedule New Activity")
        
        activity_type = st.selectbox("Activity Type", 
                                   ["Learning Session", "Goal Review", "Interview Prep", 
                                    "Networking", "Job Application", "Custom"])
        
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Event Title")
            description = st.text_area("Description")
            
        with col2:
            event_date = st.date_input("Date")
            start_time = st.time_input("Start Time")
            duration = st.selectbox("Duration", ["30 min", "1 hour", "1.5 hours", "2 hours", "3 hours"])
        
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        
        if st.button("📅 Schedule Activity"):
            st.success(f"Scheduled '{title}' for {event_date} at {start_time}")
    
    with tab3:
        st.subheader("Calendar Analytics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Events This Week", "5")
            st.metric("Learning Hours", "8")
        
        with col2:
            st.metric("Goal Reviews", "2")
            st.metric("Interview Prep", "3 hours")
        
        with col3:
            st.metric("Applications Due", "2")
            st.metric("Networking Events", "1")

def main():
    """Main application function"""
    initialize_system()
    
    # Get current page from sidebar
    current_page = sidebar_navigation()
    
    # Route to appropriate page
    if current_page == "💬 Chat":
        chat_page()
    elif current_page == "🎯 Goals":
        goals_page()
    elif current_page == "📊 Dashboard":
        dashboard_page()
    elif current_page == "🔍 Job Search":
        job_search_page()
    elif current_page == "📄 Resume":
        resume_page()
    elif current_page == "📅 Calendar":
        calendar_page()

if __name__ == "__main__":
    main()