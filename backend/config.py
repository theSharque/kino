"""
Configuration file for the Kino backend
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Models storage directory
MODELS_DIR = BASE_DIR / "models_storage"

# Data directory
DATA_DIR = BASE_DIR / "data"

# Projects directory (for frames organized by project)
PROJECTS_DIR = DATA_DIR / "projects"

# Frames directory (flat structure)
FRAMES_DIR = DATA_DIR / "frames"


class Config:
    """Configuration class"""
    MODELS_DIR = MODELS_DIR  # Keep as Path for directory operations
    MODELS_STORAGE_DIR = MODELS_DIR  # Alias for backward compatibility
    DATA_DIR = DATA_DIR  # Keep as Path
    PROJECTS_DIR = PROJECTS_DIR  # Keep as Path
    FRAMES_DIR = FRAMES_DIR  # Keep as Path

    # Ensure directories exist
    @staticmethod
    def init_directories():
        """Create necessary directories if they don't exist"""
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        FRAMES_DIR.mkdir(parents=True, exist_ok=True)


# Initialize directories on import
Config.init_directories()

