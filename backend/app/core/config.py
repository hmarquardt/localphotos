from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # Database URL loaded from .env
    DATABASE_URL: str

    # JWT Settings
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Google OAuth Settings
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback" # Default for local dev
    SESSION_SECRET_KEY: str = "a_very_secret_key_change_this_in_production" # Add a default or load from .env
    FRONTEND_URL: str = "http://localhost:8080" # Default frontend URL for redirects

    # AWS S3 Settings (loaded from .env)
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    S3_BUCKET_NAME: str
    AWS_REGION: str
    # AWS_SECRET_ACCESS_KEY: str = ""
    # S3_BUCKET_NAME: str = ""

    class Config:
        # Specify the .env file relative to the project root (where this script might be run from)
        # Adjust the path if necessary based on your execution context
        env_file = ".env" # Assumes .env is in the 'backend' directory
        env_file_encoding = 'utf-8'

# Create a single instance of the settings to be imported elsewhere
settings = Settings()