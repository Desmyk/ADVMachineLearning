# 🧠 Mental Health AI Assistant - Setup Guide

## Quick Start (You're almost there!)

Your project is **98% ready**! Here's what you need to do:

### 1. Start the Backend Server

```bash
# Make sure you're in the project root and virtual environment is activated
cd /workspace/mental-health-assistant
source backend/venv/bin/activate

# Run the enhanced server script
python run_server.py
```

**Note:** The first run will download AI models (~1-2GB), which may take 5-10 minutes depending on your internet connection.

### 2. Test the API

Open a new terminal and test:
```bash
curl http://localhost:5000/api/health
```

### 3. Use the Frontend

Open the frontend in your browser:
```bash
# Serve the frontend (simple method)
cd frontend
python -m http.server 8000

# Then open: http://localhost:8000
```

## What's Available Now

### ✅ **Backend Features Ready:**
- 🤖 **AI Chat** - DialoGPT-powered conversations
- 😊 **Sentiment Analysis** - VADER sentiment analysis
- 📊 **Mood Tracking** - Log and analyze mood patterns
- 📓 **Journaling** - AI-generated prompts
- 🔐 **Authentication** - JWT-based user system
- 📚 **Resources** - Curated mental health resources
- 🏥 **Dashboard** - Analytics and insights

### ✅ **Frontend Test Interface:**
- Interactive web interface at `http://localhost:8000`
- Test all API endpoints
- Register users, login, chat with AI
- Log moods and get resources

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/auth/register` | Register user |
| POST | `/api/auth/login` | Login user |
| POST | `/api/chat/send` | Chat with AI |
| POST | `/api/mood/log` | Log mood entry |
| GET | `/api/mood/trends` | Get mood analytics |
| POST | `/api/journal/entries` | Create journal entry |
| GET | `/api/resources/` | Get mental health resources |
| GET | `/api/dashboard/overview` | Get dashboard data |

## Development Workflow

### Running Both Frontend and Backend:

**Terminal 1 (Backend):**
```bash
cd /workspace/mental-health-assistant
source backend/venv/bin/activate
python run_server.py
```

**Terminal 2 (Frontend):**
```bash
cd /workspace/mental-health-assistant/frontend
python -m http.server 8000
```

### Testing Workflow:
1. Start backend server (Terminal 1)
2. Start frontend server (Terminal 2)
3. Open http://localhost:8000 in browser
4. Use the test interface to:
   - Register a new user
   - Login with credentials
   - Chat with the AI
   - Log mood entries
   - View resources

## Next Steps for Production

### Security (Required for production):
- Change default secret keys in `.env`
- Use environment variables for sensitive data
- Set up proper HTTPS
- Implement rate limiting

### Enhanced Frontend:
- Build a React/Vue.js application
- Add real-time chat interface
- Implement mood visualization charts
- Add mobile responsiveness

### Database:
- Migrate from SQLite to PostgreSQL/MySQL for production
- Implement database migrations
- Add backup strategies

## Troubleshooting

### Common Issues:

**AI Models downloading slowly:**
- First run downloads ~1-2GB of models
- Subsequent runs are much faster
- Ensure stable internet connection

**Port already in use:**
```bash
# Check what's using port 5000
lsof -i :5000
# Kill the process if needed
kill -9 <PID>
```

**Virtual environment issues:**
```bash
# Recreate virtual environment
cd backend
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Project Structure

```
mental-health-assistant/
├── backend/                 # Flask API server
│   ├── app.py              # Main application
│   ├── config.py           # Configuration
│   ├── requirements.txt    # Python dependencies
│   ├── .env               # Environment variables
│   ├── models/            # Database models
│   ├── routes/            # API routes
│   ├── services/          # Business logic
│   └── venv/              # Virtual environment
├── frontend/              # Web interface
│   └── index.html         # Test frontend
├── run_server.py          # Enhanced server runner
└── SETUP.md              # This file
```

## Support

For issues or questions:
1. Check the backend logs when running `python run_server.py`
2. Verify all dependencies are installed
3. Ensure ports 5000 and 8000 are available
4. Check that the virtual environment is activated

## Success Indicators

✅ Backend server starts without errors  
✅ AI models load successfully  
✅ Frontend loads at http://localhost:8000  
✅ API health check returns success  
✅ User registration works  
✅ AI chat responds to messages  

**You're ready to build amazing mental health support tools! 🚀**