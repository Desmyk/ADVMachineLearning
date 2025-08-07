# AutoMentor: An Agentic AI Career Coaching System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-green.svg)](#testing)

## 🎯 Overview

AutoMentor is an autonomous AI-powered career coaching assistant that proactively helps users plan, develop, and achieve their career goals using advanced AI techniques such as autonomous goal setting, long-term memory, multi-step reasoning, and tool integration.

### Key Features

- **🎯 Collaborative Goal Setting**: SMART goal creation with interactive refinement
- **🧠 Long-term Memory**: Vector-based memory system for context retention
- **📊 Multi-step Planning**: Intelligent task breakdown and timeline generation
- **🔍 Job Search Integration**: Automated job matching and application tracking
- **📄 Resume Generation**: AI-powered resume creation and optimization
- **📅 Smart Scheduling**: Automated calendar management for career activities
- **📈 Progress Reflection**: Periodic evaluation and plan adjustment
- **💬 Conversational Interface**: Natural language interaction via Streamlit

## 🏗️ Architecture

```
automentor/
├── core/                    # Core AI agent components
│   ├── agent/              # Main agent orchestrator
│   ├── memory/             # Vector memory system
│   ├── planning/           # Goal and task planning
│   └── reflection/         # Progress evaluation
├── tools/                  # External tool integrations
│   ├── job_search/         # Job search APIs
│   ├── resume/             # Resume generator
│   └── calendar/           # Scheduling system
├── frontend/               # Streamlit web interface
├── tests/                  # Comprehensive test suite
└── docs/                   # Documentation
```

### Technical Stack

- **LLM**: GPT-4 Turbo (via OpenAI API)
- **Memory**: FAISS vector store with sentence transformers
- **Backend**: Python with FastAPI architecture
- **Frontend**: Streamlit for interactive UI
- **Planning**: Custom multi-step reasoning engine
- **Tools**: Job APIs, resume generation, calendar integration

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (for production use)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/automentor.git
   cd automentor
   ```

2. **Create virtual environment**
   ```bash
   python -m venv automentor_env
   source automentor_env/bin/activate  # On Windows: automentor_env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```

5. **Run the application**
   ```bash
   streamlit run frontend/app.py
   ```

6. **Access the demo**
   Open your browser to `http://localhost:8501` and click "🚀 Start Demo"

## 💡 Usage Examples

### Setting Career Goals

```python
from core.planning.goal_manager import GoalManager
from core.memory import VectorMemoryStore, MemoryManager

# Initialize system
vector_store = VectorMemoryStore()
memory_manager = MemoryManager(vector_store)
goal_manager = GoalManager(memory_manager)

# Create collaborative goal
user_id = "user_001"
goal_description = "I want to become a frontend developer in 6 months"

goal_draft = goal_manager.create_collaborative_goal(
    user_id=user_id,
    initial_goal_description=goal_description
)

# Refine with SMART questions
smart_answers = {
    "specific": "Learn React, build 3 portfolio projects, apply to 10 companies",
    "measurable": "Complete certification, deploy projects, get job offer",
    "achievable": "Study 15 hours/week, use existing programming knowledge",
    "relevant": "Aligns with career transition goals",
    "time_bound": "6 months from today"
}

final_goal = goal_manager.finalize_goal(user_id, goal_draft, smart_answers)
```

### Creating Action Plans

```python
from core.planning.task_planner import TaskPlanner, PlanningStrategy

# Initialize planner
task_planner = TaskPlanner(memory_manager)

# Create comprehensive plan
plan = task_planner.create_comprehensive_plan(
    user_id=user_id,
    goal=final_goal,
    strategy=PlanningStrategy.MILESTONE
)

print(f"Generated {plan['total_tasks']} tasks")
print(f"Estimated duration: {plan['estimated_duration']}")
```

### Tracking Progress

```python
from core.reflection.progress_evaluator import ProgressEvaluator, ReflectionType

# Initialize evaluator
evaluator = ProgressEvaluator(memory_manager)

# Conduct weekly reflection
report = evaluator.conduct_reflection(
    user_id=user_id,
    goals=[final_goal],
    reflection_type=ReflectionType.WEEKLY
)

print(f"Overall progress: {report.overall_progress}")
print(f"Generated {len(report.insights)} insights")
print(f"Recommendations: {len(report.recommendations)}")
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Vector Store Configuration
VECTOR_STORE_PATH=./data/vector_store
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Job Search APIs
RAPIDAPI_KEY=your_rapidapi_key_for_job_search

# Application Settings
DEBUG=true
HOST=localhost
PORT=8000

# Agent Configuration
MAX_PLANNING_STEPS=10
MEMORY_RETENTION_DAYS=365
GOAL_CHECK_FREQUENCY_DAYS=7
```

### Memory Configuration

The vector memory system can be configured for different use cases:

```python
# High-performance setup
vector_store = VectorMemoryStore(
    model_name="sentence-transformers/all-mpnet-base-v2",
    store_path="./data/high_perf_store"
)

# Lightweight setup
vector_store = VectorMemoryStore(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    store_path="./data/lite_store"
)
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Exclude slow tests

# Run with coverage
pytest --cov=core --cov-report=html
```

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_memory_system.py    # Memory system tests
├── test_goal_planning.py    # Goal and planning tests
├── test_agent_integration.py # Integration tests
└── test_tools.py           # Tool integration tests
```

### Writing Tests

```python
def test_goal_creation(goal_manager, sample_user):
    """Test goal creation functionality"""
    goal_data = goal_manager.create_collaborative_goal(
        user_id=sample_user.id,
        initial_goal_description="Learn Python"
    )
    
    assert "smart_status" in goal_data
    assert len(goal_data["questions"]) > 0
```

## 📊 Core Components

### Memory System

The memory system provides long-term context retention:

- **Vector Store**: FAISS-based similarity search
- **Memory Manager**: High-level memory operations
- **Context Building**: Intelligent context summarization

### Goal Management

SMART goal creation and tracking:

- **Collaborative Creation**: Interactive goal refinement
- **Progress Tracking**: Automated progress monitoring
- **Analytics**: Goal performance metrics

### Task Planning

Multi-step reasoning for task breakdown:

- **Planning Strategies**: Linear, parallel, milestone-based
- **Complexity Analysis**: Automatic difficulty assessment
- **Resource Planning**: Tool and time allocation

### Agent Orchestrator

Central coordination of all systems:

- **Autonomous Actions**: Proactive check-ins and suggestions
- **Tool Integration**: Seamless tool usage
- **Context Management**: Intelligent context switching

## 🔌 Tool Integration

### Job Search

```python
from tools.job_search.job_api import JobSearchAPI, JobSearchFilters

job_api = JobSearchAPI(rapidapi_key="your_key")

filters = JobSearchFilters(
    keywords=["React", "Frontend"],
    location="San Francisco",
    remote_ok=True
)

jobs = job_api.search_jobs(filters, max_results=10)
```

### Resume Generation

```python
from tools.resume.resume_generator import ResumeGenerator

resume_gen = ResumeGenerator()

resume_buffer = resume_gen.generate_resume(
    user=user,
    target_job=target_job,
    template_name="technical",
    format_type="pdf"
)
```

### Calendar Scheduling

```python
from tools.calendar.scheduler import CareerScheduler

scheduler = CareerScheduler()

events = scheduler.schedule_goal_milestones(
    user_id=user.id,
    goal=goal,
    tasks=tasks
)
```

## 📈 Evaluation Metrics

### Functionality Metrics

- **Goal Completion Rate**: Percentage of goals achieved
- **Planning Accuracy**: Actual vs. estimated timelines
- **User Engagement**: Frequency of interactions

### Agentic Behavior Metrics

- **Autonomous Actions**: Number of proactive suggestions
- **Context Retention**: Memory recall accuracy
- **Tool Usage**: Frequency and success of tool invocations

### User Satisfaction Metrics

- **Goal Achievement**: Success in reaching career objectives
- **User Feedback**: Satisfaction ratings and testimonials
- **System Adoption**: Continued usage over time

## 🚦 Development Roadmap

### Phase 1: Core System ✅
- [x] Memory system implementation
- [x] Goal management framework
- [x] Task planning engine
- [x] Basic agent orchestration

### Phase 2: Tool Integration ✅
- [x] Job search API integration
- [x] Resume generation system
- [x] Calendar scheduling
- [x] Reflection and evaluation

### Phase 3: Enhanced Features 🔄
- [ ] Multi-agent architecture
- [ ] Real-time labor market analysis
- [ ] LinkedIn/GitHub integration
- [ ] Voice interaction support

### Phase 4: Production Ready 📋
- [ ] Scalable deployment
- [ ] Advanced security features
- [ ] API rate limiting
- [ ] Performance optimization

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Install development dependencies: `pip install -r requirements-dev.txt`
4. Make changes and add tests
5. Run tests: `pytest`
6. Submit a pull request

### Code Standards

- Follow PEP 8 style guidelines
- Add type hints for all functions
- Write comprehensive docstrings
- Maintain test coverage above 80%

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for providing the GPT-4 API
- HuggingFace for sentence transformers
- The open-source community for various tools and libraries

## 📞 Support

- **Documentation**: [Full Documentation](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-username/automentor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/automentor/discussions)

## 🔗 Links

- [Live Demo](https://automentor-demo.streamlit.app)
- [Technical Paper](docs/technical_paper.pdf)
- [Video Walkthrough](https://youtube.com/watch?v=demo)
- [Project Presentation](docs/presentation.pdf)

---

**AutoMentor** - Empowering careers through intelligent AI coaching 🚀