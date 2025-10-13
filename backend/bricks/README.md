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

## Available Samplers and Schedulers

### Samplers (40+ algorithms)

ComfyUI supports a wide range of sampling algorithms. For better UX, we categorize them:

**📌 Recommended Samplers** (most commonly used):
- `euler` - Simple and fast Euler method
- `euler_ancestral` - Euler with ancestral sampling (adds variation)
- `heun` - Heun's method (slower but higher quality)
- `dpm_2` - 2nd order DPM
- `dpm_2_ancestral` - DPM with ancestral sampling
- `dpmpp_2m` - DPM++ 2M (fast, good quality)
- `dpmpp_2m_sde` - DPM++ 2M SDE (high quality, **default**)
- `dpmpp_2m_sde_gpu` - GPU-optimized version
- `dpmpp_3m_sde` - DPM++ 3M SDE (even higher quality)
- `dpmpp_sde` - DPM++ SDE variant
- `ddim` - Classic DDIM sampler
- `uni_pc` - UniPC sampler (good quality/speed balance)
- `lcm` - Latent Consistency Model (very fast)

**🔬 All Available Samplers** (full list in `comfy_constants.py`):

*Basic K-diffusion:*
`euler`, `euler_cfg_pp`, `euler_ancestral`, `euler_ancestral_cfg_pp`, `heun`, `heunpp2`

*DPM Family:*
`dpm_2`, `dpm_2_ancestral`, `dpm_fast`, `dpm_adaptive`

*DPM++ Family:*
`dpmpp_2s_ancestral`, `dpmpp_2s_ancestral_cfg_pp`, `dpmpp_sde`, `dpmpp_sde_gpu`, `dpmpp_2m`, `dpmpp_2m_cfg_pp`, `dpmpp_2m_sde`, `dpmpp_2m_sde_gpu`, `dpmpp_3m_sde`, `dpmpp_3m_sde_gpu`

*Classic Samplers:*
`lms`, `ddpm`, `ddim`

*Advanced:*
`ipndm`, `ipndm_v`, `deis`, `uni_pc`, `uni_pc_bh2`, `lcm`

*Resolution Samplers:*
`res_multistep`, `res_multistep_cfg_pp`, `res_multistep_ancestral`, `res_multistep_ancestral_cfg_pp`

*Experimental:*
`gradient_estimation`, `gradient_estimation_cfg_pp`, `er_sde`, `seeds_2`, `seeds_3`, `sa_solver`, `sa_solver_pece`

### Schedulers (9 types)

Schedulers control how noise is removed over the sampling steps:

- `normal` - Standard linear noise schedule
- `karras` - Karras schedule (popular for high quality, slower transitions)
- `exponential` - Exponential noise schedule
- `sgm_uniform` - SGM uniform schedule (**default**)
- `simple` - Simple linear scheduler
- `ddim_uniform` - DDIM uniform schedule (for DDIM sampler)
- `beta` - Beta distribution schedule (Implemented from https://arxiv.org/abs/2407.12173)
- `linear_quadratic` - Linear-quadratic (optimized for video models)
- `kl_optimal` - KL-optimal schedule (from Automatic1111)

### Sampler + Scheduler Combinations

Some samplers work better with specific schedulers:

- **euler** → `normal`, `karras`, `exponential`
- **euler_ancestral** → `normal`, `karras`, `exponential`
- **dpmpp_2m** → `karras`, `exponential`, `normal`
- **dpmpp_2m_sde** → `karras`, `exponential`
- **dpmpp_3m_sde** → `exponential`, `karras`
- **ddim** → `ddim_uniform`, `normal`
- **uni_pc** → `karras`, `normal`

**General recommendations:**
- For **quality**: Use `dpmpp_2m_sde` or `dpmpp_3m_sde` with `karras`
- For **speed**: Use `euler` with `normal`
- For **balance**: Use `dpmpp_2m` with `exponential`

### Constants Module

Import constants in your code:

```python
from bricks.comfy_constants import (
    SAMPLER_NAMES,           # All 40+ samplers
    SCHEDULER_NAMES,         # All 9 schedulers
    RECOMMENDED_SAMPLERS,    # Curated list of ~13 best samplers
    RECOMMENDED_SCHEDULERS   # Curated list of ~5 best schedulers
)
```

---

## Wan Video Generation Bricks 🎬 🆕

For Wan (万物) image-to-video generation, use the specialized `wan_bricks` module:

### wan_bricks Module

The `wan_bricks.py` module provides components for Wan video generation workflow:

- `load_clip_vision(clip_name)` - Load CLIP Vision model
- `clip_vision_encode(clip_vision, image, crop)` - Encode image with CLIP Vision
- `load_vae(vae_name)` - Load VAE model
- `load_clip(clip_name, clip_type, device)` - Load CLIP text encoder (supports GGUF)
- `wan_image_to_video(...)` - Prepare conditioning and latent for video generation

**Quick Example:**
```python
from bricks.wan_bricks import (
    load_clip, load_clip_vision, clip_vision_encode,
    load_vae, wan_image_to_video
)
from bricks.comfy_bricks import clip_encode

# Load models
clip = load_clip("umt5_xxl.safetensors", clip_type="wan")
clip_vision = load_clip_vision("clip_vision_g.safetensors")
vae = load_vae("wan_2.1_vae.safetensors")

# Encode text
positive = clip_encode(clip, "a cat walking in garden")
negative = clip_encode(clip, "blurry, low quality")

# Encode reference image (optional)
clip_vision_output = clip_vision_encode(clip_vision, image)

# Setup video generation
positive, negative, latent = wan_image_to_video(
    positive, negative, vae,
    width=832, height=480, length=81,
    clip_vision_output=clip_vision_output,
    start_image=first_frame
)

# Use with sampler and decode...
```

**Documentation:**
- [Wan Bricks README](./README_WAN.md) - Detailed Wan bricks documentation
- [Wan Components Summary](./WAN_COMPONENTS_SUMMARY.md) - Quick reference table
- [Wan Workflow Diagram](./WAN_WORKFLOW_DIAGRAM.md) - Visual workflow guide
- [Test Script](./test_wan_bricks.py) - Test and example script

---

## See Also

- [Plugin System](../plugins/README.md) - How to create generator plugins
- [SDXL Plugin](../plugins/sdxl/loader.py) - Example of using bricks
- [ComfyUI Integration](../COMFYUI_INTEGRATION.md) - Full ComfyUI setup guide
- [Sampler Constants](./comfy_constants.py) - Full list of samplers and schedulers
- [Generation Parameters](./README_PARAMS.md) - How to save/load generation params

