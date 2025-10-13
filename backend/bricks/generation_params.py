"""
Utilities for working with generation parameters
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any


def save_generation_params(
    output_path: str,
    plugin_name: str,
    plugin_version: str,
    task_id: int,
    timestamp: str,
    parameters: Dict[str, Any],
    project_id: Optional[int] = None
) -> str:
    """
    Save generation parameters to JSON file next to the generated image

    Args:
        output_path: Path to the generated image file (.png)
        plugin_name: Name of the generator plugin used
        plugin_version: Version of the plugin
        task_id: Task ID that generated this frame
        timestamp: Generation timestamp
        parameters: Dictionary of generation parameters
        project_id: Optional project ID

    Returns:
        Path to the saved JSON file

    Example:
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
    """
    # Convert output path to Path object
    img_path = Path(output_path)

    # Create JSON path (same name, different extension)
    json_path = img_path.with_suffix('.json')

    # Prepare generation data
    generation_data = {
        'plugin': plugin_name,
        'plugin_version': plugin_version,
        'timestamp': timestamp,
        'task_id': task_id,
        'parameters': parameters,
        'output': {
            'filename': img_path.name,
            'path': str(output_path)
        }
    }

    # Add project_id if provided
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

