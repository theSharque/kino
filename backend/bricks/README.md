# ComfyUI Bricks

Bricks are lightweight wrapper functions that provide a simplified interface to ComfyUI backend functionality. Each brick encapsulates a specific operation (loading models, encoding prompts, sampling, etc.) and can be combined like building blocks to create generation workflows.

## Available Bricks

### 1. `load_checkpoint_plugin(ckpt_path)`

Loads a Stable Diffusion checkpoint.

**Parameters:**
- `ckpt_path` (str): Path to checkpoint file (.safetensors or .ckpt)

**Returns:**
- Tuple: `(model, clip, vae, clipvision)`

**Example:**
```python
model, clip, vae, _ = comfy_bricks.load_checkpoint_plugin(
    "/path/to/sd_xl_base_1.0.safetensors"
)
```

---

### 2. `clip_encode(clip, text)`

Encodes text prompt using CLIP.

**Parameters:**
- `clip`: CLIP model from checkpoint loader
- `text` (str): Text prompt to encode

**Returns:**
- Conditioning: Encoded prompt for sampling

**Example:**
```python
positive = comfy_bricks.clip_encode(clip, "A beautiful landscape")
negative = comfy_bricks.clip_encode(clip, "blurry, low quality")
```

---

### 3. `generate_latent_image(width, height)`

Creates an empty latent tensor for image generation.

**Parameters:**
- `width` (int): Image width in pixels (must be divisible by 8)
- `height` (int): Image height in pixels (must be divisible by 8)

**Returns:**
- Dict: `{"samples": latent_tensor}`

**Example:**
```python
latent = comfy_bricks.generate_latent_image(1024, 1024)
```

---

### 4. `common_ksampler(model, latent, positive, negative, steps, cfg, ...)`  🆕 **UPDATED**

Runs the sampling process to generate images.

**Parameters:**
- `model`: Model from checkpoint loader or modified by LoRA
- `latent`: Empty latent from `generate_latent_image()`
- `positive`: Positive conditioning from `clip_encode()`
- `negative`: Negative conditioning from `clip_encode()`
- `steps` (int): Number of inference steps
- `cfg` (float): CFG scale
- `sampler_name` (str, optional): Sampler algorithm (default: "dpmpp_2m_sde")
- `scheduler` (str, optional): Scheduler type (default: "sgm_uniform")
- `denoise` (float, optional): Denoise strength (default: 1.0)
- `seed` (int, optional): **🆕 NEW!** Random seed for reproducibility (default: None = random)

**Returns:**
- **Tuple:** `(output_dict, used_seed)` 🆕 **CHANGED!** Now returns both output and seed
  - `output_dict`: `{"samples": sampled_latent}`
  - `used_seed`: Integer seed that was used (either provided or randomly generated)

**Example:**
```python
# With random seed (seed will be auto-generated)
sample, seed = comfy_bricks.common_ksampler(
    model, latent, positive, negative,
    steps=30, cfg=7.5,
    sampler_name="dpmpp_2m_sde"
)
print(f"Used seed: {seed}")  # Save this for reproducibility!

# With specific seed for exact reproduction
sample, seed = comfy_bricks.common_ksampler(
    model, latent, positive, negative,
    steps=30, cfg=7.5,
    sampler_name="dpmpp_2m_sde",
    seed=123456789  # Same seed = same image
)
```

---

### 5. `vae_decode(vae, samples)`

Decodes latent samples into RGB images.

**Parameters:**
- `vae`: VAE from checkpoint loader
- `samples`: Sampled latent from `common_ksampler()`

**Returns:**
- Tensor: RGB images (shape: [batch, height, width, 3])

**Example:**
```python
images = comfy_bricks.vae_decode(vae, sample)
```

---

### 6. `load_lora(lora_path, model, clip, strength_model=1.0, strength_clip=1.0)` 🆕

Loads and applies LoRA to model and CLIP.

**Parameters:**
- `lora_path` (str): Path to LoRA file (.safetensors)
- `model`: Model from checkpoint loader
- `clip`: CLIP from checkpoint loader
- `strength_model` (float, optional): LoRA strength for model (0.0-1.0, default: 1.0)
- `strength_clip` (float, optional): LoRA strength for CLIP (0.0-1.0, default: 1.0)

**Returns:**
- Tuple: `(modified_model, modified_clip)`

**Example:**
```python
# Load checkpoint
model, clip, vae, _ = comfy_bricks.load_checkpoint_plugin(ckpt_path)

# Apply LoRA
model, clip = comfy_bricks.load_lora(
    lora_path="/path/to/my_style.safetensors",
    model=model,
    clip=clip,
    strength_model=0.8,  # 80% LoRA strength for model
    strength_clip=1.0    # 100% LoRA strength for CLIP
)

# Use modified model and clip for generation...
```

---

## Complete Workflow Example

Here's a complete example combining multiple bricks for SDXL generation with LoRA:

```python
import bricks.comfy_bricks as comfy_bricks

# 1. Load checkpoint
model, clip, vae, _ = comfy_bricks.load_checkpoint_plugin(
    "/models/sd_xl_base_1.0.safetensors"
)

# 2. (Optional) Apply LoRA
model, clip = comfy_bricks.load_lora(
    lora_path="/models/lora/my_style.safetensors",
    model=model,
    clip=clip,
    strength_model=0.8,
    strength_clip=1.0
)

# 3. Encode prompts
positive = comfy_bricks.clip_encode(clip, "A beautiful sunset over mountains")
negative = comfy_bricks.clip_encode(clip, "blurry, low quality")

# 4. Create empty latent
latent = comfy_bricks.generate_latent_image(1024, 1024)

# 5. Run sampling
sample = comfy_bricks.common_ksampler(
    model=model,
    latent=latent,
    positive=positive,
    negative=negative,
    steps=30,
    cfg=7.5,
    sampler_name="dpmpp_2m_sde"
)

# 6. Decode to image
images = comfy_bricks.vae_decode(vae, sample)

# 7. Save frame (see frames_routine.py)
# save_frame(project_name, frame_id, images)
```

---

## Design Principles

1. **Simple Interface**: Each brick has a clear, minimal interface
2. **No State**: Bricks are stateless functions (except model caching in plugins)
3. **Composable**: Bricks can be combined in different orders
4. **Error Handling**: Caller is responsible for error handling
5. **ComfyUI Native**: Direct use of ComfyUI internals for best performance

---

## Adding New Bricks

When adding new bricks:

1. Keep function signatures simple
2. Add comprehensive docstrings
3. Return ComfyUI native types (don't convert)
4. Use type hints for parameters
5. Document the function in this README
6. Create test script to verify functionality

---

## See Also

- [Plugin System](../plugins/README.md) - How to create generator plugins
- [SDXL Plugin](../plugins/sdxl/loader.py) - Example of using bricks
- [ComfyUI Documentation](../comfy/README.md) - ComfyUI backend info

