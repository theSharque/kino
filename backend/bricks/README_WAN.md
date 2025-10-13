# Wan Bricks Documentation

Utility functions for Wan (万物 / Wanwu) video generation workflow.

## Overview

Wan bricks provide building blocks for image-to-video generation using the Wan model family from Hugging Face. These functions wrap ComfyUI nodes to create a simplified API for:

- Loading CLIP Vision models for image understanding
- Encoding images with CLIP Vision
- Loading VAE models for latent encoding/decoding
- Loading CLIP text encoders (including GGUF format)
- Preparing conditioning and latents for Wan video generation

## Components

### 1. CLIP Vision Loader

```python
def load_clip_vision(clip_name: str)
```

Load CLIP Vision model for image encoding.

**Parameters:**
- `clip_name` (str): Name of the CLIP Vision model file from `models/clip_vision/` folder

**Returns:**
- `clip_vision`: Loaded CLIP Vision model

**Example:**
```python
clip_vision = load_clip_vision("clip_vision_g.safetensors")
```

**Source:** Based on `CLIPVisionLoader` from ComfyUI `nodes.py`

---

### 2. CLIP Vision Encode

```python
def clip_vision_encode(clip_vision, image, crop="center")
```

Encode image using CLIP Vision model to get visual embeddings.

**Parameters:**
- `clip_vision`: CLIP Vision model from `load_clip_vision()`
- `image`: Input image tensor (torch.Tensor)
- `crop` (str): Crop method - `"center"` or `"none"` (default: `"center"`)

**Returns:**
- `output`: CLIP Vision output embedding (CLIP_VISION_OUTPUT type)

**Example:**
```python
clip_vision_output = clip_vision_encode(clip_vision, image, crop="center")
```

**Source:** Based on `CLIPVisionEncode` from ComfyUI `nodes.py`

---

### 3. VAE Loader

```python
def load_vae(vae_name: str)
```

Load VAE model for encoding/decoding images to/from latent space.

**Parameters:**
- `vae_name` (str): Name of the VAE model file from `models/vae/` folder
  - Can be a `.safetensors` file
  - Or special names: `"pixel_space"`, `"taesd"`, `"taesdxl"`, `"taesd3"`, `"taef1"`

**Returns:**
- `vae`: Loaded VAE model

**Example:**
```python
vae = load_vae("wan_2.1_vae.safetensors")
```

**Source:** Based on `VAELoader` from ComfyUI `nodes.py`

---

### 4. CLIP Loader (Text Encoder)

```python
def load_clip(clip_name: str, clip_type: str = "wan", device: str = "default")
```

Load CLIP text encoder model. Supports GGUF format for quantized models.

**Parameters:**
- `clip_name` (str): Name of the CLIP model file from `models/text_encoders/` folder
- `clip_type` (str): Type of CLIP model (default: `"wan"`)
  - Available types: `"stable_diffusion"`, `"stable_cascade"`, `"sd3"`, `"stable_audio"`,
    `"mochi"`, `"ltxv"`, `"pixart"`, `"cosmos"`, `"lumina2"`, `"wan"`, `"hidream"`,
    `"chroma"`, `"ace"`, `"omnigen2"`, `"qwen_image"`, `"hunyuan_image"`
- `device` (str): Device to load on - `"default"` or `"cpu"`

**Returns:**
- `clip`: Loaded CLIP text encoder model

**Example:**
```python
# Load standard CLIP for Wan
clip = load_clip("umt5_xxl.safetensors", clip_type="wan")

# Load GGUF quantized model
clip = load_clip("umt5_xxl_q8_0.gguf", clip_type="wan")
```

**Source:** Based on `CLIPLoader` from ComfyUI `nodes.py`

---

### 5. Wan Image to Video

```python
def wan_image_to_video(
    positive,
    negative,
    vae,
    width: int = 832,
    height: int = 480,
    length: int = 81,
    batch_size: int = 1,
    clip_vision_output=None,
    start_image=None
)
```

Prepare conditioning and latent tensors for Wan image-to-video generation.

**Parameters:**
- `positive`: Positive conditioning from CLIP text encode
- `negative`: Negative conditioning from CLIP text encode
- `vae`: VAE model for encoding images
- `width` (int): Video width in pixels (default: 832)
- `height` (int): Video height in pixels (default: 480)
- `length` (int): Video length in frames (default: 81)
- `batch_size` (int): Batch size (default: 1)
- `clip_vision_output` (optional): CLIP Vision encoding of reference image
- `start_image` (optional): Starting image tensor for video generation

**Returns:**
- Tuple of `(positive, negative, latent)`:
  - `positive`: Modified positive conditioning with video setup
  - `negative`: Modified negative conditioning with video setup
  - `latent`: Empty latent tensor dict with key `"samples"` for video generation

**Example:**
```python
positive, negative, latent = wan_image_to_video(
    positive=positive_cond,
    negative=negative_cond,
    vae=vae,
    width=832,
    height=480,
    length=81,
    clip_vision_output=clip_vision_output,
    start_image=first_frame
)
```

**Source:** Based on `WanImageToVideo` from ComfyUI `comfy_extras/nodes_wan.py`

---

## Typical Workflow

Here's a complete example of using Wan bricks for image-to-video generation:

```python
from bricks.wan_bricks import (
    load_clip,
    load_clip_vision,
    clip_vision_encode,
    load_vae,
    wan_image_to_video
)
from bricks.comfy_bricks import clip_encode

# 1. Load models
clip = load_clip("umt5_xxl.safetensors", clip_type="wan")
clip_vision = load_clip_vision("clip_vision_g.safetensors")
vae = load_vae("wan_2.1_vae.safetensors")

# 2. Encode text prompts
positive = clip_encode(clip, "a cat walking in the garden, high quality")
negative = clip_encode(clip, "blurry, low quality, distorted")

# 3. Encode reference image (optional)
# image is a torch.Tensor of shape [B, H, W, C]
clip_vision_output = clip_vision_encode(clip_vision, image, crop="center")

# 4. Prepare video generation
positive, negative, latent = wan_image_to_video(
    positive=positive,
    negative=negative,
    vae=vae,
    width=832,
    height=480,
    length=81,  # Number of frames
    clip_vision_output=clip_vision_output,
    start_image=image  # First frame
)

# 5. Now use common_ksampler or other sampling functions with:
#    model, positive, negative, latent
```

## Model Requirements

For Wan video generation, you need:

1. **CLIP Text Encoder**: `umt5_xxl` for Wan models
   - Location: `models/text_encoders/`
   - Supports GGUF quantized versions

2. **CLIP Vision** (optional): For image conditioning
   - Location: `models/clip_vision/`
   - Example: `clip_vision_g.safetensors`

3. **VAE**: Wan-specific VAE
   - Location: `models/vae/`
   - Example: `wan_2.1_vae.safetensors`

4. **Diffusion Model**: Wan checkpoint
   - Location: `models/checkpoints/` or `models/diffusion_models/`
   - Example: Wan 2.1 or Wan 2.2 models

## Architecture Details

### Latent Structure

Wan uses a special latent structure:
- **Channels**: 16 (vs 4 for standard SD)
- **Temporal dimension**: `((length - 1) // 4) + 1`
- **Spatial dimensions**: `height // 8` x `width // 8`
- **Shape**: `[batch, 16, temporal, height//8, width//8]`

### Conditioning

Wan accepts several conditioning inputs:
- **Text**: Standard CLIP text embeddings
- **CLIP Vision**: Image embeddings from CLIP Vision encoder
- **Concat Latent**: Encoded start/control images
- **Concat Mask**: Mask indicating which parts to denoise

### Frame Length

Video length must satisfy: `length % 4 == 1` (e.g., 81, 49, 33, 17 frames)

This is due to the temporal compression factor of 4 in the VAE.

## See Also

- `comfy_bricks.py` - Core ComfyUI utilities (checkpoint loading, sampling, etc.)
- `comfy_constants.py` - Sampler and scheduler constants
- ComfyUI documentation for more details on model formats

## References

- ComfyUI: https://github.com/comfyanonymous/ComfyUI
- Wan models: https://huggingface.co/Wan

