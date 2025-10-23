import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Database Configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "dental_crm")
    
    # Service Configuration
    SERVICE_PORT = int(os.getenv("SERVICE_PORT", 8000))
    SERVICE_HOST = os.getenv("SERVICE_HOST", "0.0.0.0")
    
    # Backend URL
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000")
    
    # Email Configuration
    EMAIL_SENDER = os.getenv("EMAIL_SENDER", "your-email@gmail.com")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your-app-password")
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required in .env file")
        return True

config = Config()

