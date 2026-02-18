import os

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'gemini-assistant-secret-key'
    SESSION_TYPE = 'filesystem'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Gemini API Key
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or "AIzaSyBM5yF7Zah91NTZk8erjuLmlWyq7BvtXlw"
    
    # Voice Settings
    WAKE_WORD = "broklin"
    LISTEN_LANG = 'hi-IN'
    SPEAK_LANG = 'hi'
