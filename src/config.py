"""
Configuration Management
Centralized configuration for the AI interview system
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from project root
# This handles the case where the script is run from the src/ directory
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)

# Also try loading from current directory as fallback
load_dotenv()


class Config:
    """Application configuration"""
    
    # Google AI Configuration
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    USE_VERTEX_AI: bool = os.getenv("USE_VERTEX_AI", "false").lower() == "true"
    GOOGLE_CLOUD_PROJECT: Optional[str] = os.getenv("GOOGLE_CLOUD_PROJECT")
    GOOGLE_CLOUD_LOCATION: str = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    
    print(GOOGLE_API_KEY)
    # LiveKit Configuration
    LIVEKIT_URL: str = os.getenv("LIVEKIT_URL", "")
    LIVEKIT_API_KEY: str = os.getenv("LIVEKIT_API_KEY", "")
    LIVEKIT_API_SECRET: str = os.getenv("LIVEKIT_API_SECRET", "")

    print(LIVEKIT_URL)
    
    # Recording Configuration
    USE_CLOUD_STORAGE: bool = os.getenv("USE_CLOUD_STORAGE", "false").lower() == "true"
    
    # AWS Configuration
    AWS_ACCESS_KEY: str = os.getenv("AWS_ACCESS_KEY", "")
    AWS_SECRET_KEY: str = os.getenv("AWS_SECRET_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_BUCKET: str = os.getenv("AWS_BUCKET", "interview-recordings")
    
    # GCS Configuration
    GCS_BUCKET: Optional[str] = os.getenv("GCS_BUCKET")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # Application Settings
    INTERVIEW_DURATION_MINUTES: int = int(os.getenv("INTERVIEW_DURATION_MINUTES", "30"))
    MAX_CONCURRENT_INTERVIEWS: int = int(os.getenv("MAX_CONCURRENT_INTERVIEWS", "5"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Database Configuration
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # Monitoring
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
    
    # Directories
    RECORDINGS_DIR: str = "recordings"
    TRANSCRIPTS_DIR: str = "transcripts"
    EVALUATIONS_DIR: str = "evaluations"
    
    # Gemini Model Settings
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    GEMINI_VOICE: str = "Puck"  # Available: Puck, Charon, Kore, Fenrir, Aoede
    GEMINI_TEMPERATURE: float = 0.7
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate that all required configuration is present
        
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError if required configuration is missing
        """
        required_fields = [
            ("GOOGLE_API_KEY", cls.GOOGLE_API_KEY),
            ("LIVEKIT_URL", cls.LIVEKIT_URL),
            ("LIVEKIT_API_KEY", cls.LIVEKIT_API_KEY),
            ("LIVEKIT_API_SECRET", cls.LIVEKIT_API_SECRET),
        ]
        
        missing_fields = [
            field_name for field_name, field_value in required_fields
            if not field_value
        ]
        
        if missing_fields:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing_fields)}\n"
                f"Please set these in your .env file or environment variables."
            )
            
        # Validate cloud storage configuration if enabled
        if cls.USE_CLOUD_STORAGE:
            if not (cls.AWS_ACCESS_KEY and cls.AWS_SECRET_KEY):
                if not cls.GCS_BUCKET:
                    raise ValueError(
                        "Cloud storage enabled but no storage credentials found. "
                        "Set AWS credentials or GCS_BUCKET."
                    )
                    
        return True
        
    @classmethod
    def get_storage_config(cls) -> dict:
        """Get storage configuration based on settings"""
        if cls.USE_CLOUD_STORAGE:
            if cls.AWS_ACCESS_KEY and cls.AWS_SECRET_KEY:
                return {
                    "type": "s3",
                    "access_key": cls.AWS_ACCESS_KEY,
                    "secret_key": cls.AWS_SECRET_KEY,
                    "region": cls.AWS_REGION,
                    "bucket": cls.AWS_BUCKET,
                }
            elif cls.GCS_BUCKET:
                return {
                    "type": "gcs",
                    "bucket": cls.GCS_BUCKET,
                    "credentials": cls.GOOGLE_APPLICATION_CREDENTIALS,
                }
        
        return {
            "type": "local",
            "directory": cls.RECORDINGS_DIR,
        }


# Create config instance
config = Config()


def setup_logging():
    """Configure logging for the application"""
    import logging
    
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set specific log levels for noisy libraries
    logging.getLogger("livekit").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)


def setup_directories():
    """Create necessary directories if they don't exist"""
    import os
    
    directories = [
        config.RECORDINGS_DIR,
        config.TRANSCRIPTS_DIR,
        config.EVALUATIONS_DIR,
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


# Initialize on import
try:
    config.validate()
    setup_directories()
except ValueError as e:
    print(f"Configuration Error: {e}")
    print("Please check your .env file and ensure all required variables are set.")