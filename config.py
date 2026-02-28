import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'gemini-assistant-secret-key'
    SESSION_TYPE = None # Use default client-side sessions for Vercel
    # Detect if running in Vercel / AWS Lambda Serverless environment
    if os.environ.get('VERCEL') or os.environ.get('VERCEL_URL') or os.environ.get('VERCEL_REGION') or os.environ.get('AWS_EXECUTION_ENV'):
        SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/database.db'
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Gemini API Key
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
    # Voice Settings
    WAKE_WORD = "broklin"
    LISTEN_LANG = 'hi-IN'
    SPEAK_LANG = 'hi'
