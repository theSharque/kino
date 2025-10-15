# Preview Generation System

## Overview

The preview generation system provides real-time visual feedback during image generation. Instead of waiting for the entire generation to complete, users can see progressive previews that update at each sampling step.

## Architecture

### Components

1. **`preview_bricks.py`** - Core preview generation module
   - `PreviewGenerator` - Generates preview images from latent tensors
   - `create_preview_callback()` - Creates callback for ComfyUI sampling
   - `save_preview_image()` - Saves preview to disk

2. **`comfy_bricks.py`** (updated)
   - `common_ksampler()` now accepts `callback` parameter
   - Passes callback to ComfyUI's sample function

3. **SDXL Plugin** (updated)
   - Creates frame entry at start of generation
   - Updates frame with preview during sampling
   - Replaces preview with final image on completion

4. **Frame Service** (updated)
   - `update_frame_path()` - Updates frame path for previews

## How It Works

### 1. Latent Preview Generation

ComfyUI uses two methods to generate previews from latent space:

**TAESD (Tiny AutoEncoder)**
- Fast decoder specifically trained for previews
- Better quality but requires model file
- Located in `models/vae_approx/`

**Latent2RGB**
- Simple matrix multiplication
- Always available (fallback method)
- Lower quality but very fast

### 2. Generation Flow

```
1. Start generation
   ↓
2. Create frame entry in database with preview path
   ↓
3. Load checkpoint and encode prompts
   ↓
4. Run KSampler with preview callback
   ↓
5. At each sampling step:
   - Generate preview from current latent
   - Save preview image to disk
   - Frame entry points to preview file
   ↓
6. Decode final VAE
   ↓
7. Save final image (replaces preview file)
   ↓
8. Update frame entry with final path
   ↓
9. Delete preview file (if different from final)
```

### 3. File Naming Convention

**Preview file:**
```
task_{task_id}_{timestamp}_preview.png
```

**Final file:**
```
task_{task_id}_{timestamp}.png
```

The system automatically replaces the preview with the final image by:
1. Saving final image to non-preview path
2. Deleting the `_preview.png` file
3. Updating database with final path

## Usage in Plugins

### Basic Integration

```python
from bricks.preview_bricks import create_preview_callback, save_preview_image
from bricks import comfy_bricks
from services.frame_service import FrameService
from models.frame import FrameCreate

# In plugin's generate() method:

# 1. Create frame entry
frame_create = FrameCreate(
    path=preview_path,  # Path to preview file
    generator='sdxl',
    project_id=project_id
)
created_frame = await frame_service.create_frame(frame_create)
frame_id = created_frame.id

# 2. Define preview callback
def on_preview(step, total_steps, preview_image):
    """Called at each sampling step"""
    # Save preview
    save_preview_image(preview_image, preview_path)
    # Update progress, notify via WebSocket, etc.
    print(f"Preview updated: step {step+1}/{total_steps}")

# 3. Create ComfyUI callback
sampling_callback = create_preview_callback(model, on_preview)

# 4. Run sampler with callback
sample, seed = comfy_bricks.common_ksampler(
    model, latent, positive, negative,
    steps, cfg_scale,
    sampler_name=sampler,
    scheduler=scheduler,
    seed=seed,
    callback=sampling_callback  # Pass callback here
)

# 5. After VAE decode, replace preview with final
final_path = preview_path.replace('_preview.png', '.png')
save_final_image(image, final_path)

# 6. Update frame path
await frame_service.update_frame_path(frame_id, final_path)

# 7. Delete preview file
if os.path.exists(preview_path):
    os.remove(preview_path)
```

## Benefits

1. **Real-time Feedback** - Users see generation progress visually
2. **Better UX** - No "black box" waiting period
3. **Early Stopping** - Users can stop generation if preview looks wrong
4. **Debugging** - Can see if generation is going off-track
5. **Engagement** - More interactive experience

## Performance Impact

**Minimal overhead:**
- Preview generation: ~5-10ms per step
- File I/O: ~10-20ms per save
- Total: ~15-30ms overhead per step

For a 32-step generation, total overhead is ~0.5-1 second, which is negligible compared to the generation time (30-60+ seconds).

## WebSocket Integration

The frontend can receive real-time preview updates via WebSocket. The frame service broadcasts updates when preview images are saved, allowing the UI to reload the image immediately.

See `docs/WEBSOCKET_EVENTS.md` for details on frame update events.

## Troubleshooting

### Preview not generating

**Problem:** No preview images appear during generation

**Solutions:**
1. Check if TAESD model is available in `models/vae_approx/`
2. Verify `latent_format.latent_rgb_factors` exists (fallback)
3. Check console for preview generation errors

### Preview file not deleted

**Problem:** `_preview.png` files remain after generation

**Solutions:**
1. Check file permissions on frames directory
2. Verify final image path is different from preview path
3. Check for errors in cleanup code

### Memory usage

**Problem:** High memory usage during generation

**Solutions:**
1. Preview images use CPU memory (moved from GPU)
2. Each preview is ~100KB for 512x512
3. Only one preview exists at a time (overwritten)

## Future Enhancements

- [ ] Configurable preview update frequency (every N steps)
- [ ] WebSocket streaming of preview images (base64)
- [ ] Preview quality settings
- [ ] Preview caching for batch generations
- [ ] Video preview mode (animated GIF of progress)

## References

- ComfyUI latent_preview.py
- TAESD paper: https://arxiv.org/abs/2111.05849
- Latent space visualization techniques

