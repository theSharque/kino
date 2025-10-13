# ComfyUI Integration in Kino

This document describes how full ComfyUI is integrated into the Kino backend.

## Directory Structure

```
backend/
├── ComfyUI/              # Full ComfyUI installation
│   ├── comfy/           # Core ComfyUI library
│   ├── comfy_api/       # API modules
│   ├── comfy_extras/    # Extra nodes and features
│   ├── custom_nodes/    # Custom node system
│   ├── models/          # Model storage (symlinked to ../models_storage/)
│   ├── main.py          # ComfyUI server (not used by Kino)
│   └── ...              # Other ComfyUI files
│
└── bricks/              # Kino's ComfyUI connector layer
    ├── comfy_bricks.py  # Wrapper functions using ComfyUI
    └── ...
```

## Integration Approach

### Why Bricks Layer?

Instead of using ComfyUI directly, Kino uses a "bricks" abstraction layer:

1. **Simplified Interface** - Clean, minimal functions
2. **Stability** - Insulates from ComfyUI API changes
3. **Testing** - Easier to test and mock
4. **Documentation** - Single source of truth for usage
5. **Flexibility** - Can swap ComfyUI version without changing plugins

### How It Works

**1. sys.path Configuration**

The bricks module automatically adds ComfyUI to Python path:

```python
# In comfy_bricks.py
import sys
from pathlib import Path

comfyui_path = Path(__file__).parent.parent / "ComfyUI"
if str(comfyui_path) not in sys.path:
    sys.path.insert(0, str(comfyui_path))

# Now ComfyUI internal imports work:
from comfy.sample import sample
from comfy.sd import load_checkpoint_guess_config
```

**2. Wrapper Functions**

Each brick wraps a ComfyUI operation:

```python
def load_checkpoint_plugin(ckpt_path):
    """Load checkpoint using full ComfyUI"""
    from comfy.sd import load_checkpoint_guess_config
    return load_checkpoint_guess_config(
        ckpt_path, 
        output_vae=True, 
        output_clip=True, 
        output_clipvision=True
    )
```

**3. Plugin Usage**

Plugins use bricks, not ComfyUI directly:

```python
# In SDXL plugin
import bricks.comfy_bricks as comfy_bricks

# Load checkpoint via brick
model, clip, vae, _ = comfy_bricks.load_checkpoint_plugin(ckpt_path)
```

## Migration from Old comfy/ to ComfyUI/

### What Changed

**Before:**
- Old stripped-down `comfy/` directory
- Direct imports: `from comfy.sample import ...`

**After:**
- Full `ComfyUI/` installation
- sys.path setup in bricks
- Imports still use: `from comfy.sample import ...` (works via sys.path)

### Changes Required in Bricks

**comfy_bricks.py:**
```python
# Added at the top:
import sys
from pathlib import Path

comfyui_path = Path(__file__).parent.parent / "ComfyUI"
if str(comfyui_path) not in sys.path:
    sys.path.insert(0, str(comfyui_path))

# Then imports work as before:
from comfy.sample import sample  # Actually loads from ComfyUI/comfy/sample.py
```

**No changes needed in:**
- Plugins (sdxl, example) - use bricks interface
- Services - don't import ComfyUI directly
- Handlers - don't import ComfyUI directly

## Benefits of Full ComfyUI

### Features Now Available

1. **Latest Algorithms** - All newest samplers and schedulers
2. **Custom Nodes** - Can use ComfyUI custom nodes
3. **Model Support** - Latest model architectures (Flux, Aura, etc.)
4. **Updates** - Can update to newer ComfyUI versions
5. **Community** - Access to ComfyUI ecosystem

### Available Samplers

40+ sampling algorithms from ComfyUI:
- K-diffusion: euler, heun, euler_ancestral, etc.
- DPM/DPM++: dpmpp_2m, dpmpp_2m_sde, dpmpp_3m_sde, etc.
- Advanced: uni_pc, lcm, ipndm, deis, etc.

### Available Schedulers

9 noise schedules:
- simple, normal, sgm_uniform (default)
- karras, exponential, ddim_uniform
- beta, linear_quadratic, kl_optimal

## Testing

### Quick Test

```bash
cd backend/bricks
source ../venv/bin/activate
python test_comfy_integration.py
```

### Expected Output

```
✅ All tests passed!
💡 ComfyUI Integration Status:
   - Imports: Working ✅
   - sys.path: Configured ✅
   - Latent generation: Working ✅
   - Constants: Available ✅
```

### Test Individual Functions

```python
import bricks.comfy_bricks as cb

# Test latent generation
latent = cb.generate_latent_image(512, 512)
print(latent['samples'].shape)  # torch.Size([1, 4, 64, 64])

# Test constants
from bricks.comfy_constants import SAMPLER_NAMES
print(f"Total samplers: {len(SAMPLER_NAMES)}")  # 40
```

## Upgrading ComfyUI

To upgrade to a newer ComfyUI version:

1. **Backup current:**
   ```bash
   mv ComfyUI ComfyUI_backup
   ```

2. **Install new version:**
   ```bash
   git clone https://github.com/comfyanonymous/ComfyUI.git
   ```

3. **Test bricks:**
   ```bash
   cd bricks
   python test_comfy_integration.py
   ```

4. **Update constants if needed:**
   - Check `ComfyUI/comfy/samplers.py` for new samplers/schedulers
   - Update `bricks/comfy_constants.py` if new algorithms added

5. **Test generation:**
   - Run SDXL plugin test
   - Verify image generation works

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'comfy'`

**Solution:** Ensure sys.path is configured in comfy_bricks.py:
```python
comfyui_path = Path(__file__).parent.parent / "ComfyUI"
sys.path.insert(0, str(comfyui_path))
```

### Missing Dependencies

**Problem:** `ModuleNotFoundError: No module named 'torchsde'` (or other module)

**Solution:** Install ComfyUI dependencies:
```bash
pip install -r ComfyUI/requirements.txt
```

Or update `backend/requirements.txt` with needed dependencies.

### Version Mismatch

**Problem:** ComfyUI API changed, bricks don't work

**Solution:** 
1. Check ComfyUI changelog
2. Update brick functions to match new API
3. Keep bricks interface stable for plugins

## Future Enhancements

- [ ] Use ComfyUI's custom nodes system
- [ ] Integrate ComfyUI workflow execution
- [ ] Expose more ComfyUI features via bricks
- [ ] Add ComfyUI model manager integration
- [ ] Support ComfyUI's API server features

## References

- **ComfyUI GitHub:** https://github.com/comfyanonymous/ComfyUI
- **Bricks Documentation:** `/backend/bricks/README.md`
- **SDXL Plugin:** `/backend/plugins/sdxl/loader.py`
- **Constants:** `/backend/bricks/comfy_constants.py`

