import os
from pathlib import Path

from dotenv import load_dotenv


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load variables from .env
load_dotenv(PROJECT_ROOT / ".env")


# API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Embedding model
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)


# Important project directories
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge-base"
DATA_DIR = PROJECT_ROOT / "data"
EVALUATION_DIR = PROJECT_ROOT / "evaluation"

# Local vector database
CHROMA_DIR = PROJECT_ROOT / "chroma_db"


def validate_config() -> None:
    """Validate configuration required to run the application."""

    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is not set. "
            "Create a .env file and add your API key."
        )