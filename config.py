import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'gemini-assistant-secret-key'
    SESSION_TYPE = None # Use default client-side sessions for Vercel
    if os.environ.get('VERCEL_ENV'):
        SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/database.db'
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Gemini API Key
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or "AIzaSyBM5yF7Zah91NTZk8erjuLmlWyq7BvtXlw"
    
    # Voice Settings
    WAKE_WORD = "broklin"
    LISTEN_LANG = 'hi-IN'
    SPEAK_LANG = 'hi'
