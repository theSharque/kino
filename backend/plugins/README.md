# Generator Plugins

This directory contains generator plugins for the Kino project. Each plugin is in its own directory and implements the `BasePlugin` interface.

## Plugin Structure

Each plugin must follow this structure:

```
plugins/
├── base_plugin.py          # Base plugin interface (don't modify)
├── plugin_loader.py        # Auto-loader (don't modify)
├── example/                # Example plugin directory
│   ├── __init__.py
│   └── loader.py          # Plugin implementation
└── sdxl/                   # SDXL plugin directory
    ├── __init__.py
    └── loader.py          # Plugin implementation
```

**Important:**
- Directory name = plugin name (used in API)
- Main file must be named `loader.py`
- Plugin class must inherit from `BasePlugin`

## Available Plugins

### 1. Example Plugin (`example/`)
A simple example plugin that demonstrates the plugin architecture.

**Usage:**
```json
{
  "type": "example",
  "data": {
    "prompt": "test prompt",
    "steps": 20
  }
}
```

### 2. SDXL Plugin (`sdxl/`)
Stable Diffusion XL image generator using ComfyUI backend.

**Status:** Fully implemented with ComfyUI integration

**Usage:**
```json
{
  "type": "sdxl",
  "data": {
    "prompt": "beautiful landscape",
    "model_name": "sd_xl_base_1.0.safetensors",
    "negative_prompt": "blurry, low quality",
    "width": 1024,
    "height": 1024,
    "steps": 30,
    "cfg_scale": 7.5,
    "sampler": "dpmpp_2m_sde"
  }
}
```

**Note:** Requires SDXL model checkpoint in `models_storage/StableDiffusion/` directory. See `sdxl/README.md` for detailed documentation.

## Creating a New Plugin

### Step 1: Create Plugin Directory

```bash
cd backend/plugins
mkdir my_plugin
```

### Step 2: Create `__init__.py`

```python
# plugins/my_plugin/__init__.py
"""
My plugin package
"""
```

### Step 3: Create `loader.py`

```python
# plugins/my_plugin/loader.py
import sys
import os
from typing import Dict, Any, Optional, Callable

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_plugin import BasePlugin, PluginResult


class MyPlugin(BasePlugin):
    """Your plugin description"""

    async def generate(
        self,
        task_id: int,
        data: Dict[str, Any],
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> PluginResult:
        """Main generation logic"""
        try:
            self.is_running = True
            self.should_stop = False
            self.progress = 0.0

            # Your code here
            # ...

            self.update_progress(50.0, progress_callback)

            # Check for stop
            if self.should_stop:
                return PluginResult(
                    success=False,
                    data={},
                    error="Stopped by user"
                )

            # Return result
            self.is_running = False
            return PluginResult(
                success=True,
                data={'output_path': '...', ...}
            )

        except Exception as e:
            self.is_running = False
            return PluginResult(
                success=False,
                data={},
                error=str(e)
            )

    async def stop(self):
        """Stop generation"""
        self.should_stop = True
        self.is_running = False

    @classmethod
    def get_plugin_info(cls) -> Dict[str, Any]:
        """Plugin metadata"""
        return {
            'name': 'my_plugin',
            'version': '1.0.0',
            'description': 'My custom generator',
            'author': 'Your Name',
            'parameters': {
                'param1': {
                    'type': 'string',
                    'required': True,
                    'description': 'First parameter'
                }
            }
        }
```

### Step 4: Restart Server

The plugin will be automatically loaded when the server starts!

```bash
cd backend
source venv/bin/activate
python main.py
```

### Step 5: Test Your Plugin

```bash
# Check if plugin is loaded
curl http://localhost:8000/api/v1/generator/plugins

# Create task
curl -X POST http://localhost:8000/api/v1/generator/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test",
    "type": "my_plugin",
    "data": {
      "param1": "value1"
    }
  }'

# Start generation
curl -X POST http://localhost:8000/api/v1/generator/tasks/1/generate
```

## Plugin Interface

### Required Methods

#### `async def generate(task_id, data, progress_callback) -> PluginResult`

Main generation logic. Must:
- Set `self.is_running = True` at start
- Check `self.should_stop` periodically
- Call `self.update_progress()` to report progress
- Return `PluginResult` with success status and data
- Set `self.is_running = False` when done

#### `async def stop()`

Stop the generation process. Must:
- Set `self.should_stop = True`
- Set `self.is_running = False`
- Clean up resources if needed

#### `@classmethod def get_plugin_info() -> Dict`

Return plugin metadata including name, version, and parameters.

### Progress Tracking

```python
# Report progress (0.0 to 100.0)
self.update_progress(25.0, progress_callback)
```

### Stopping Support

```python
# Check if user requested stop
if self.should_stop:
    return PluginResult(
        success=False,
        data={},
        error="Stopped by user"
    )
```

## Best Practices

1. **Plugin Directory Name**: Use lowercase with underscores (e.g., `stable_diffusion`, `comfy_ui`)
2. **Validate Input**: Check required parameters at the start
3. **Progress Updates**: Report progress at least every 5-10%
4. **Support Stopping**: Check `should_stop` frequently in loops
5. **Error Handling**: Use try/except and return proper error messages
6. **Resource Cleanup**: Release memory/models in `stop()` method
7. **Output Paths**: Save files to `/data/frames/` directory
8. **Result Data**: Include all relevant information (paths, parameters used, etc.)

## File Organization

You can organize your plugin with additional files:

```
plugins/my_plugin/
├── __init__.py
├── loader.py       # Main plugin class
├── model.py        # Model loading/inference
├── utils.py        # Helper functions
├── config.py       # Configuration
└── README.md       # Plugin-specific docs
```

Import them in `loader.py`:

```python
from .model import load_model, run_inference
from .utils import process_image
```

## Testing

```bash
# Test plugin loading
python -c "from plugins.plugin_loader import PluginRegistry; print(PluginRegistry.get_all_plugins())"

# Test via API
curl http://localhost:8000/api/v1/generator/plugins | python -m json.tool
```

## Troubleshooting

**Plugin not loading:**
- Check if `loader.py` exists in plugin directory
- Ensure class inherits from `BasePlugin`
- Check server logs for import errors

**Import errors:**
- Use the path setup code at the top of `loader.py`
- Make sure `__init__.py` exists in plugin directory

**Plugin class not found:**
- Ensure your class name ends with "Plugin" (recommended)
- Class must directly or indirectly inherit from `BasePlugin`
