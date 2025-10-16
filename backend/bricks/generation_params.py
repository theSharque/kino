"""
Utilities for working with generation parameters
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any


async def save_generation_params(
    output_path: str = None,
    plugin_name: str = None,
    plugin_version: str = None,
    task_id: int = None,
    timestamp: str = None,
    parameters: Dict[str, Any] = None,
    project_id: Optional[int] = None,
    frame_id: Optional[int] = None
) -> str:
    """
    Save generation parameters to JSON file next to the generated image

    Args:
        output_path: Path to the generated image file (.png) (for new generation)
        plugin_name: Name of the generator plugin used
        plugin_version: Version of the plugin
        task_id: Task ID that generated this frame (for new generation)
        timestamp: Generation timestamp (for new generation)
        parameters: Dictionary of generation parameters
        project_id: Optional project ID (for new generation)
        frame_id: Frame ID for regeneration (alternative to output_path)

    Returns:
        Path to the saved JSON file

    Example:
        # New generation
        save_generation_params(
            output_path="/path/to/frame_001.png",
            plugin_name="sdxl",
            plugin_version="1.0.0",
            task_id=42,
            timestamp="20251013_150530",
            parameters={
                'prompt': 'A beautiful landscape',
                'width': 1024,
                'height': 1024,
                'steps': 32
            },
            project_id=1
        )
        # Creates: /path/to/frame_001.json

        # Regeneration
        save_generation_params(
            frame_id=18,
            plugin_name="sdxl",
            plugin_version="1.0.0",
            parameters={
                'prompt': 'A beautiful landscape',
                'width': 1024,
                'height': 1024,
                'steps': 32
            }
        )
        # Updates existing frame's JSON file
    """
    if frame_id:
        # Regeneration mode: get frame path from database
        from database import get_db
        from services.frame_service import FrameService
        db = get_db()
        frame_service = FrameService(db)
        frame = await frame_service.get_frame_by_id(frame_id)
        if not frame:
            raise ValueError(f"Frame {frame_id} not found")
        img_path = Path(frame.path)
    else:
        # New generation mode: use provided output_path
        if not output_path:
            raise ValueError("Either output_path or frame_id must be provided")
        img_path = Path(output_path)

    # Create JSON path (same name, different extension)
    json_path = img_path.with_suffix('.json')

    # Prepare generation data
    generation_data = {
        'plugin': plugin_name,
        'plugin_version': plugin_version,
        'parameters': parameters,
        'output': {
            'filename': img_path.name,
            'path': str(img_path)
        }
    }

    # Add optional fields based on mode
    if frame_id:
        # Regeneration mode
        generation_data['frame_id'] = frame_id
        generation_data['timestamp'] = timestamp or "regenerated"
    else:
        # New generation mode
        generation_data['timestamp'] = timestamp
        generation_data['task_id'] = task_id
        if project_id is not None:
            generation_data['project_id'] = project_id

    # Save to JSON file
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(generation_data, f, indent=2, ensure_ascii=False)

    return str(json_path)


def load_generation_params(image_path: str) -> Optional[Dict[str, Any]]:
    """
    Load generation parameters from JSON file associated with an image

    Args:
        image_path: Path to the image file (.png)

    Returns:
        Dictionary with generation parameters, or None if JSON file not found

    Example:
        params = load_generation_params("/path/to/frame_001.png")
        if params:
            print(f"Prompt: {params['parameters']['prompt']}")
            print(f"Steps: {params['parameters']['steps']}")
    """
    # Convert to Path and change extension
    json_path = Path(image_path).with_suffix('.json')

    # Check if JSON file exists
    if not json_path.exists():
        return None

    # Load and return JSON data
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading generation params from {json_path}: {e}")
        return None


def get_params_path(image_path: str) -> str:
    """
    Get the path to the JSON parameters file for a given image

    Args:
        image_path: Path to the image file

    Returns:
        Path to the corresponding JSON file (may not exist yet)
    """
    return str(Path(image_path).with_suffix('.json'))


def params_exist(image_path: str) -> bool:
    """
    Check if generation parameters JSON file exists for an image

    Args:
        image_path: Path to the image file

    Returns:
        True if JSON file exists, False otherwise
    """
    return Path(image_path).with_suffix('.json').exists()

