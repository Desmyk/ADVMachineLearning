# Mental Health AI Assistant 🧠💚

A comprehensive full-stack web application designed to provide empathetic mental health support through AI-powered conversations, mood tracking, journaling, and curated resources.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)
![AI](https://img.shields.io/badge/AI-DialoGPT-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📌 Project Overview

The Mental Health AI Assistant combines machine learning (NLP), web development, and data-driven insights to support mental well-being through:

- **🗣 AI Chat Support**: GPT-based conversational AI using DialoGPT-medium for empathetic responses
- **😊 Sentiment Detection**: VADER sentiment analysis to understand emotional tone
- **📊 Mood Tracker**: Daily mood logging with trend visualization
- **📓 Journaling**: AI-generated writing prompts for self-reflection
- **🔐 User Authentication**: Secure registration and login system
- **📚 Resources Section**: Curated mental health resources and guides

## 🚀 Features

### Core Features
- **Empathetic AI Conversations**: Context-aware responses tailored to emotional state
- **Real-time Sentiment Analysis**: Automatic mood detection from messages
- **Comprehensive Mood Tracking**: Visual trends and patterns analysis
- **Intelligent Journal Prompts**: AI-generated prompts based on mood and context
- **Personalized Dashboard**: Insights, analytics, and progress tracking
- **Resource Recommendations**: Curated content based on user needs

### Technical Features
- **RESTful API**: Clean, documented endpoints
- **JWT Authentication**: Secure token-based authentication
- **SQLite Database**: Lightweight, embedded database
- **CORS Support**: Cross-origin resource sharing enabled
- **Error Handling**: Comprehensive error management
- **Data Privacy**: Secure storage of sensitive information

## 🛠 Tech Stack

### Backend
- **Framework**: Flask (Python)
- **Database**: SQLAlchemy with SQLite
- **Authentication**: Flask-JWT-Extended
- **AI/ML**: Transformers, PyTorch, VADER Sentiment
- **API**: RESTful with JSON responses

### AI/ML Components
- **Conversational AI**: Microsoft DialoGPT-medium
- **Sentiment Analysis**: VADER (Valence Aware Dictionary and sEntiment Reasoner)
- **Text Processing**: Transformers library
- **Mood Analysis**: Custom algorithms for trend detection

## 📦 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd mental-health-assistant
```

### Step 2: Set Up the Backend
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Create a `.env` file in the backend directory:
```bash
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
DATABASE_URL=sqlite:///mental_health_app.db
FLASK_ENV=development
```

### Step 4: Initialize the Database
```bash
python app.py
```
This will create the database and seed it with initial resources.

### Step 5: Start the Backend Server
```bash
python app.py
```
The API will be available at `http://localhost:5000`

## 🔗 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `GET /api/auth/profile` - Get user profile
- `PUT /api/auth/profile` - Update user profile

### Chat & AI
- `POST /api/chat/send` - Send message to AI
- `GET /api/chat/sessions` - Get chat sessions
- `POST /api/chat/new-session` - Start new chat session
- `GET /api/chat/sentiment-trends` - Get sentiment analysis

### Mood Tracking
- `POST /api/mood/log` - Log mood entry
- `GET /api/mood/entries` - Get mood entries
- `GET /api/mood/trends` - Get mood trends and analytics
- `GET /api/mood/weekly-summary` - Get weekly mood summary

### Journaling
- `POST /api/journal/entries` - Create journal entry
- `GET /api/journal/entries` - Get journal entries
- `POST /api/journal/prompts/generate` - Generate AI prompt
- `GET /api/journal/statistics` - Get journaling statistics

### Resources
- `GET /api/resources/` - Get curated resources
- `GET /api/resources/featured` - Get featured resources
- `GET /api/resources/recommendations` - Get personalized recommendations

### Dashboard
- `GET /api/dashboard/overview` - Get dashboard overview
- `GET /api/dashboard/insights` - Get AI-powered insights
- `GET /api/dashboard/goals` - Get progress goals

## 📊 Database Schema

### Core Models
- **User**: Authentication and profile information
- **Mood**: Daily mood tracking (1-5 scale)
- **ChatMessage**: AI conversations with sentiment analysis
- **JournalEntry**: Personal journal entries with prompts
- **Resource**: Curated mental health resources

### Key Relationships
- Users have many Moods, ChatMessages, and JournalEntries
- Each ChatMessage includes sentiment analysis
- JournalEntries can track mood before/after writing
- Resources are categorized and tagged for recommendations

## 🤖 AI Components

### Conversational AI (DialoGPT)
- **Model**: Microsoft DialoGPT-medium
- **Features**: Context-aware responses, empathetic language
- **Customization**: Mental health-focused prompting and response framing

### Sentiment Analysis (VADER)
- **Engine**: VADER Sentiment Intensity Analyzer
- **Enhancements**: Mental health keyword weighting
- **Output**: Compound score, individual sentiment scores, confidence levels

### Journal Prompt Generation
- **Categories**: Gratitude, Self-reflection, Mindfulness, Goals, Relationships
- **Personalization**: Based on mood, recent entries, and user preferences
- **Seasonal Variation**: Time-aware prompt selection

## 📈 Usage Examples

### Register a New User
```python
import requests

response = requests.post('http://localhost:5000/api/auth/register', json={
    'username': 'john_doe',
    'email': 'john@example.com',
    'password': 'secure_password',
    'first_name': 'John',
    'last_name': 'Doe'
})
```

### Log a Mood Entry
```python
headers = {'Authorization': f'Bearer {access_token}'}
response = requests.post('http://localhost:5000/api/mood/log', 
    json={'score': 4, 'notes': 'Feeling good today!'}, 
    headers=headers
)
```

### Send a Chat Message
```python
response = requests.post('http://localhost:5000/api/chat/send',
    json={'message': 'I had a stressful day at work'},
    headers=headers
)
```

## 🔒 Security Features

- **Password Hashing**: Bcrypt encryption for secure password storage
- **JWT Tokens**: Secure authentication with expiration
- **CORS Protection**: Configured origins and methods
- **Input Validation**: Comprehensive request validation
- **Error Handling**: Secure error messages without data leakage

## 📱 Frontend Integration

The backend API is designed to work with any frontend framework. Recommended setup:

### React/Next.js Example
```javascript
// API client setup
const API_BASE = 'http://localhost:5000/api';

const apiClient = {
  setAuthToken: (token) => {
    // Set authorization header
  },
  
  mood: {
    log: (moodData) => fetch(`${API_BASE}/mood/log`, {
      method: 'POST',
      body: JSON.stringify(moodData)
    })
  },
  
  chat: {
    send: (message) => fetch(`${API_BASE}/chat/send`, {
      method: 'POST',
      body: JSON.stringify({message})
    })
  }
};
```

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### API Testing with curl
```bash
# Health check
curl http://localhost:5000/

# Register user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"password","first_name":"Test","last_name":"User"}'
```

## 🚀 Deployment

### Environment Variables for Production
```bash
SECRET_KEY=your-production-secret-key
JWT_SECRET_KEY=your-production-jwt-secret
DATABASE_URL=postgresql://user:password@host:port/database
FLASK_ENV=production
```

### Using Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## 📈 Monitoring & Analytics

### Available Metrics
- User registration and activity rates
- Chat message volume and sentiment trends
- Mood tracking consistency and patterns
- Journal writing frequency and word counts
- Resource usage and effectiveness

### Health Monitoring
- `GET /` - Basic health check
- `GET /api/health` - Detailed API health status

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add docstrings to all functions and classes
- Include unit tests for new features
- Update documentation for API changes

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Transformers Library**: Hugging Face for DialoGPT implementation
- **VADER Sentiment**: For sentiment analysis capabilities
- **Flask Community**: For the robust web framework
- **Mental Health Resources**: Various organizations providing educational content

## ⚠️ Important Notes

### Medical Disclaimer
This application is designed for supportive purposes only and should not replace professional medical advice, diagnosis, or treatment. If you're experiencing severe mental health issues, please consult with qualified healthcare professionals.

### Privacy & Data
- All user data is stored securely and privately
- No personal information is shared with third parties
- Users can delete their accounts and data at any time

### AI Limitations
- The AI assistant provides supportive conversation but is not a replacement for human therapy
- Responses are generated based on patterns in training data
- Users should verify important information with qualified sources

## 📞 Support

For questions, issues, or support:
- Create an issue in the GitHub repository
- Check the documentation for common solutions
- Review the API documentation for integration help

---

**Built with ❤️ for mental health and wellbeing**