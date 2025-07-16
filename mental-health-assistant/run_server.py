#!/usr/bin/env python3
"""
Mental Health AI Assistant Server Runner
Run this script to start the backend server with proper model initialization.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def setup_environment():
    """Set up the environment and verify dependencies."""
    print("🔧 Setting up Mental Health AI Assistant...")
    
    # Change to backend directory
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("❌ Virtual environment not activated!")
        print("Please run: source backend/venv/bin/activate")
        return False
    
    # Check if .env file exists
    if not Path(".env").exists():
        print("❌ .env file not found!")
        print("Creating .env file with default values...")
        with open(".env", "w") as f:
            f.write("""SECRET_KEY=your-secret-key-change-this-in-production
JWT_SECRET_KEY=your-jwt-secret-change-this-in-production
DATABASE_URL=sqlite:///mental_health_app.db
FLASK_ENV=development
FLASK_DEBUG=True
""")
        print("✅ .env file created!")
    
    return True

def download_models():
    """Download AI models if not already present."""
    print("🤖 Checking AI models...")
    
    try:
        import transformers
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        model_name = "microsoft/DialoGPT-medium"
        print(f"📥 Loading {model_name}...")
        
        # This will download the model if not present
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        
        print("✅ AI models ready!")
        return True
        
    except Exception as e:
        print(f"❌ Error loading models: {e}")
        print("This might take a few minutes on first run...")
        return False

def start_server():
    """Start the Flask development server."""
    print("🚀 Starting Flask server...")
    
    try:
        # Run the Flask app
        os.system("python app.py")
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

def main():
    print("=" * 50)
    print("🧠 Mental Health AI Assistant")
    print("=" * 50)
    
    if not setup_environment():
        return
    
    print("\n📋 Server will be available at:")
    print("   🌐 http://localhost:5000")
    print("   📚 API docs: http://localhost:5000/api/health")
    print("\n💡 Key endpoints:")
    print("   • POST /api/auth/register - Register user")
    print("   • POST /api/auth/login    - Login")
    print("   • POST /api/chat/send     - Chat with AI")
    print("   • POST /api/mood/log      - Log mood")
    print("   • GET  /api/resources/    - Get resources")
    
    print("\n⏳ Starting server (this may take a moment for AI model loading)...")
    
    # Download models in background if needed
    download_models()
    
    # Start the server
    start_server()

if __name__ == "__main__":
    main()