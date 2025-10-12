"""
Model management service
Provides access to available AI models in models_storage directory
"""
import os
from typing import List, Dict, Optional
from pathlib import Path
from config import Config


class ModelService:
    """Service for managing AI models"""

    # Supported model file extensions
    MODEL_EXTENSIONS = ['.safetensors', '.ckpt', '.pth', '.pt', '.bin']

    @staticmethod
    def get_model_categories() -> List[str]:
        """
        Get list of available model categories (subdirectories in models_storage)

        Returns:
            List of category names
        """
        categories = []
        models_dir = Config.MODELS_STORAGE_DIR

        if not models_dir.exists():
            return categories

        for item in models_dir.iterdir():
            if item.is_dir():
                categories.append(item.name)

        return sorted(categories)

    @staticmethod
    def get_models_by_category(category: str) -> List[Dict[str, str]]:
        """
        Get list of models in a specific category

        Args:
            category: Category name (subdirectory name)

        Returns:
            List of model info dictionaries with 'filename' and 'display_name'
        """
        models = []
        category_dir = Config.MODELS_STORAGE_DIR / category

        if not category_dir.exists() or not category_dir.is_dir():
            return models

        for file_path in category_dir.iterdir():
            if file_path.is_file() and file_path.suffix in ModelService.MODEL_EXTENSIONS:
                # For now, display_name is same as filename
                # TODO: Add logic to extract readable names from model metadata
                models.append({
                    'filename': file_path.name,
                    'display_name': file_path.stem,  # Filename without extension
                    'path': str(file_path),
                    'size': file_path.stat().st_size,
                    'extension': file_path.suffix
                })

        # Sort by filename
        models.sort(key=lambda x: x['filename'])

        return models

    @staticmethod
    def model_exists(category: str, filename: str) -> bool:
        """
        Check if a model file exists

        Args:
            category: Category name
            filename: Model filename

        Returns:
            True if model exists, False otherwise
        """
        model_path = Config.MODELS_STORAGE_DIR / category / filename
        return model_path.exists() and model_path.is_file()

    @staticmethod
    def get_model_info(category: str, filename: str) -> Optional[Dict[str, str]]:
        """
        Get information about a specific model

        Args:
            category: Category name
            filename: Model filename

        Returns:
            Model info dictionary or None if not found
        """
        model_path = Config.MODELS_STORAGE_DIR / category / filename

        if not model_path.exists() or not model_path.is_file():
            return None

        return {
            'filename': model_path.name,
            'display_name': model_path.stem,
            'path': str(model_path),
            'size': model_path.stat().st_size,
            'extension': model_path.suffix,
            'category': category
        }

