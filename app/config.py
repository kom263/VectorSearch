"""Application configuration loaded from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./hiring_pipeline.db")
ROLES_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "roles")
