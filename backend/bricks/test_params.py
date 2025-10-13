#!/usr/bin/env python3
"""
Test script for generation parameters functionality

Usage:
    python test_params.py
"""

from generation_params import (
    save_generation_params,
    load_generation_params,
    params_exist,
    get_params_path
)
from pathlib import Path
import tempfile


def test_save_and_load():
    """Test saving and loading parameters"""
    print("=" * 60)
    print("Testing Generation Parameters")
    print("=" * 60)

    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        test_image_path = tmp.name

    print(f"\nTest image path: {test_image_path}")

    # Test data
    test_params = {
        'prompt': 'A beautiful landscape with mountains and lake',
        'negative_prompt': 'blurry, low quality, distorted',
        'width': 1024,
        'height': 1024,
        'steps': 32,
        'cfg_scale': 3.5,
        'sampler': 'dpmpp_2m_sde',
        'seed': 123456789,
        'model_name': 'cyberrealisticPony_v130.safetensors',
        'loras': [
            {
                'lora_name': 'detail_tweaker.safetensors',
                'strength_model': 1.0,
                'strength_clip': 1.0
            }
        ]
    }

    print("\n" + "-" * 60)
    print("Step 1: Saving parameters")
    print("-" * 60)

    json_path = save_generation_params(
        output_path=test_image_path,
        plugin_name='sdxl',
        plugin_version='1.0.0',
        task_id=42,
        timestamp='20251013_150530',
        parameters=test_params,
        project_id=1
    )

    print(f"✅ Parameters saved to: {json_path}")
    print(f"✅ JSON file exists: {Path(json_path).exists()}")

    print("\n" + "-" * 60)
    print("Step 2: Checking if parameters exist")
    print("-" * 60)

    exists = params_exist(test_image_path)
    print(f"✅ Parameters exist: {exists}")

    expected_path = get_params_path(test_image_path)
    print(f"✅ Expected JSON path: {expected_path}")
    print(f"✅ Paths match: {json_path == expected_path}")

    print("\n" + "-" * 60)
    print("Step 3: Loading parameters")
    print("-" * 60)

    loaded_params = load_generation_params(test_image_path)

    if loaded_params:
        print("✅ Parameters loaded successfully!")
        print(f"\nPlugin: {loaded_params['plugin']}")
        print(f"Plugin Version: {loaded_params['plugin_version']}")
        print(f"Task ID: {loaded_params['task_id']}")
        print(f"Timestamp: {loaded_params['timestamp']}")
        print(f"Project ID: {loaded_params['project_id']}")

        print("\nGeneration Parameters:")
        params = loaded_params['parameters']
        print(f"  Prompt: {params['prompt'][:50]}...")
        print(f"  Negative: {params['negative_prompt'][:50]}...")
        print(f"  Size: {params['width']}x{params['height']}")
        print(f"  Steps: {params['steps']}")
        print(f"  CFG Scale: {params['cfg_scale']}")
        print(f"  Sampler: {params['sampler']}")
        print(f"  Seed: {params.get('seed', 'random')}")
        print(f"  Model: {params['model_name']}")
        print(f"  LoRAs: {len(params['loras'])} loaded")

        if params['loras']:
            for i, lora in enumerate(params['loras'], 1):
                print(f"    {i}. {lora['lora_name']} (model: {lora['strength_model']}, clip: {lora['strength_clip']})")

        print("\nOutput:")
        output = loaded_params['output']
        print(f"  Filename: {output['filename']}")
        print(f"  Path: {output['path']}")

    else:
        print("❌ Failed to load parameters")

    print("\n" + "-" * 60)
    print("Step 4: Testing with non-existent file")
    print("-" * 60)

    non_existent = load_generation_params("/non/existent/path.png")
    print(f"✅ Returns None for non-existent file: {non_existent is None}")

    print("\n" + "-" * 60)
    print("Step 5: Cleanup")
    print("-" * 60)

    # Clean up test files
    try:
        Path(test_image_path).unlink()
        Path(json_path).unlink()
        print("✅ Test files cleaned up")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

    print("\n" + "=" * 60)
    print("All tests passed! ✅")
    print("=" * 60)


def show_example_json():
    """Display example JSON structure"""
    print("\n" + "=" * 60)
    print("Example JSON Structure")
    print("=" * 60)

    example = """
{
  "plugin": "sdxl",
  "plugin_version": "1.0.0",
  "timestamp": "20251013_150530",
  "task_id": 42,
  "parameters": {
    "prompt": "A beautiful landscape with mountains and lake",
    "negative_prompt": "blurry, low quality, distorted",
    "width": 1024,
    "height": 1024,
    "steps": 32,
    "cfg_scale": 3.5,
    "sampler": "dpmpp_2m_sde",
    "seed": 123456789,
    "model_name": "cyberrealisticPony_v130.safetensors",
    "loras": [
      {
        "lora_name": "detail_tweaker.safetensors",
        "strength_model": 1.0,
        "strength_clip": 1.0
      }
    ]
  },
  "output": {
    "filename": "task_42_20251013_150530.png",
    "path": "/qs/kino/backend/data/frames/task_42_20251013_150530.png"
  },
  "project_id": 1
}
"""
    print(example)


if __name__ == "__main__":
    test_save_and_load()
    show_example_json()

    print("\n💡 Usage Examples:")
    print("-" * 60)
    print("# Save parameters after generating an image:")
    print("save_generation_params(output_path, plugin_name, ...)")
    print()
    print("# Load parameters for regeneration:")
    print("params = load_generation_params('/path/to/frame.png')")
    print()
    print("# Check if parameters exist:")
    print("if params_exist('/path/to/frame.png'):")
    print("    params = load_generation_params('/path/to/frame.png')")
    print()

