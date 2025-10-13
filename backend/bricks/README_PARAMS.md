# Generation Parameters Storage

This document describes how generation parameters are stored and used in Kino.

## Overview

When a frame is generated, all generation parameters are automatically saved to a JSON file alongside the image. This allows:
- **Reproducibility**: Regenerate the same image with identical parameters
- **Variations**: Create variations by modifying specific parameters
- **History tracking**: Know exactly how each frame was created
- **Debugging**: Troubleshoot generation issues

## File Structure

For each generated image, two files are created:

```
/data/frames/
├── task_42_20251013_150530.png   # Generated image
└── task_42_20251013_150530.json  # Generation parameters
```

The JSON file has the same base name as the image, just with `.json` extension.

## JSON Format

```json
{
  "plugin": "sdxl",
  "plugin_version": "1.0.0",
  "timestamp": "20251013_150530",
  "task_id": 42,
  "parameters": {
    "prompt": "A beautiful landscape with mountains and lake",
    "negative_prompt": "blurry, low quality",
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
```

## API Reference

### `save_generation_params()`

Saves generation parameters to a JSON file.

```python
from bricks.generation_params import save_generation_params

json_path = save_generation_params(
    output_path="/path/to/image.png",
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
# Returns: "/path/to/image.json"
```

### `load_generation_params()`

Loads generation parameters from a JSON file.

```python
from bricks.generation_params import load_generation_params

params = load_generation_params("/path/to/image.png")
if params:
    print(f"Plugin: {params['plugin']}")
    print(f"Prompt: {params['parameters']['prompt']}")
    print(f"Steps: {params['parameters']['steps']}")
```

Returns `None` if the JSON file doesn't exist.

### `params_exist()`

Checks if parameters file exists for an image.

```python
from bricks.generation_params import params_exist

if params_exist("/path/to/image.png"):
    print("Parameters available!")
```

### `get_params_path()`

Gets the path to the parameters JSON file.

```python
from bricks.generation_params import get_params_path

json_path = get_params_path("/path/to/image.png")
# Returns: "/path/to/image.json"
```

## Usage in Plugins

### Saving Parameters (SDXL Example)

```python
from bricks.generation_params import save_generation_params

# After saving the image
save_generation_params(
    output_path=output_path_str,
    plugin_name='sdxl',
    plugin_version='1.0.0',
    task_id=task_id,
    timestamp=timestamp,
    parameters={
        'prompt': prompt,
        'negative_prompt': negative_prompt,
        'width': width,
        'height': height,
        'steps': steps,
        'cfg_scale': cfg_scale,
        'sampler': sampler,
        'model_name': model_name,
        'loras': loras
    },
    project_id=project_id
)
```

### Loading Parameters for Regeneration

```python
from bricks.generation_params import load_generation_params

# Load parameters from existing frame
params = load_generation_params("/path/to/frame.png")

if params and params['plugin'] == 'sdxl':
    # Use the same parameters
    original = params['parameters']

    # Option 1: Exact reproduction
    new_params = original.copy()

    # Option 2: Create variation (change one parameter)
    new_params = original.copy()
    new_params['cfg_scale'] = 5.0  # Different CFG

    # Generate with new/modified parameters
    await plugin.generate(task_id, new_params, progress_callback)
```

## Best Practices

1. **Always save parameters** when generating frames
2. **Include all generation parameters** - even defaults
3. **Save plugin version** to track compatibility
4. **Use meaningful timestamps** for file naming
5. **Validate parameters** before regeneration

## Future Enhancements

- [x] ✅ Add seed parameter for exact reproducibility (IMPLEMENTED)
- [ ] Include system info (GPU type, driver version)
- [ ] Store image hash for verification
- [ ] Add tags/metadata for better organization
- [ ] Support parameter presets/templates
- [ ] Batch regeneration from JSON files

## File Location

- **Source**: `/backend/bricks/generation_params.py`
- **Used by**: All generator plugins (SDXL, etc.)
- **Saved to**: `/backend/data/frames/*.json`

