"""
Configuration settings for the application
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "Neuro-Vitals"
    VERSION: str = "1.0.0"
    
    # AI Model Configuration
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    MODEL_PROVIDER: str = "openai"  # "openai", "anthropic", or "mock"
    
    # Groq API (Risk Engine)
    GROQ_API_KEY: Optional[str] = None
    
    # Google Gemini (Outbreak Analysis)
    GOOGLE_API_KEY: Optional[str] = None
    
    # GitHub Models (Alternate Gemini Provider)
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_API_URL: str = "https://models.inference.ai.azure.com"
    
    # Google Fit API
    GOOGLE_FIT_CLIENT_ID: Optional[str] = None
    GOOGLE_FIT_CLIENT_SECRET: Optional[str] = None
    
    # Supabase Configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    
    # Database Configuration - ADD THESE LINES
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "neurovitals"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    
    # Feature Flags
    ENABLE_ADVERSARIAL: bool = True
    ENABLE_TRAJECTORY: bool = True
    ENABLE_COMMUNITY: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        # Optional: Add this to ignore any extra env vars not defined
        extra = "ignore"


settings = Settings()
import os
print(f"--- CONFIG PROBE ---")
print(f"PWD: {os.getcwd()}")
print(f"GROQ_KEY: {'[SET]' if settings.GROQ_API_KEY else '[MISSING]'}")
print(f"GITHUB_TOKEN: {'[SET]' if settings.GITHUB_TOKEN else '[MISSING]'}")
print(f"GOOGLE_KEY: {'[SET]' if settings.GOOGLE_API_KEY else '[MISSING]'}")
print(f"GITHUB_URL: {settings.GITHUB_API_URL}")
print(f"--------------------")
