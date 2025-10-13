# GGUF Bricks Documentation

Utility functions for loading quantized models in GGUF format.

## Overview

GGUF (GPT-Generated Unified Format) is a quantization format that allows:
- **Smaller model size**: 4-8x smaller than float16
- **Faster loading**: Less data to read from disk
- **Lower VRAM usage**: Models stay quantized in VRAM
- **Good quality**: Especially Q5-Q8 quantization levels

GGUF bricks provide functions for loading:
1. **Diffusion Models (UNET)** - Flux, Wan, SD3, SDXL, etc.
2. **CLIP Text Encoders** - T5, LLaMA, Qwen2VL, etc.

Based on: [ComfyUI-GGUF](https://github.com/city96/ComfyUI-GGUF)

---

## Requirements

### ComfyUI-GGUF Installation

The GGUF bricks require the ComfyUI-GGUF custom node to be installed:

```bash
cd /qs/kino/backend/ComfyUI/custom_nodes
git clone https://github.com/city96/ComfyUI-GGUF.git
cd ComfyUI-GGUF
pip install -r requirements.txt
```

---

## Functions

### 1. Load UNET (Diffusion Model) GGUF

```python
load_unet_gguf(
    unet_name: str,
    dequant_dtype: str = "default",
    patch_dtype: str = "default",
    patch_on_device: bool = False
) → model
```

Load diffusion model in GGUF format.

**Supported Models:**
- Flux, Wan, SD3, SDXL, SD1
- Aura, HiDream, Cosmos, LTXV
- HyVid, Lumina2, Qwen-Image

**Parameters:**
- `unet_name` (str): GGUF model filename from `models/diffusion_models/` or `models/unet/`
- `dequant_dtype` (str): Dequantization data type:
  - `"default"` - Keep quantized (saves VRAM)
  - `"target"` - Dequantize to target dtype
  - `"float32"`, `"float16"`, `"bfloat16"` - Specific dtype
- `patch_dtype` (str): Data type for patches (LoRA, etc.)
- `patch_on_device` (bool): Patch on device vs offload (default: False = offload)

**Returns:**
- `model`: GGUF model wrapped in GGUFModelPatcher

**Example:**
```python
from bricks.gguf_bricks import load_unet_gguf

# Load quantized Flux model
model = load_unet_gguf("flux1-dev-Q4_K_S.gguf")

# Load Wan with float16 dequantization
model = load_unet_gguf(
    "wan-2.1-Q8_0.gguf",
    dequant_dtype="float16"
)
```

---

### 2. Load CLIP GGUF

```python
load_clip_gguf(
    clip_name: str,
    clip_type: str = "stable_diffusion"
) → clip
```

Load CLIP text encoder in GGUF format.

**Supported Encoders:**
- T5 (all variants)
- LLaMA
- Qwen2VL
- Standard CLIP

**Parameters:**
- `clip_name` (str): GGUF CLIP filename from `models/text_encoders/` or `models/clip/`
  - Can also be non-GGUF (will load normally)
- `clip_type` (str): Model type - one of:
  - `"stable_diffusion"`, `"sd3"`, `"flux"`, `"wan"`
  - `"sdxl"`, `"stable_cascade"`, `"stable_audio"`
  - `"mochi"`, `"ltxv"`, `"pixart"`, `"cosmos"`
  - `"lumina2"`, `"hidream"`, `"chroma"`, `"ace"`
  - `"omnigen2"`, `"qwen_image"`, `"hunyuan_image"`

**Returns:**
- `clip`: CLIP model wrapped in GGUFModelPatcher

**Example:**
```python
from bricks.gguf_bricks import load_clip_gguf

# Load quantized T5 for Wan
clip = load_clip_gguf("umt5-xxl-Q8_0.gguf", clip_type="wan")

# Load quantized T5 for SD3
clip = load_clip_gguf("t5xxl-Q4_K_M.gguf", clip_type="sd3")

# Mix GGUF and non-GGUF
clip = load_clip_gguf("clip-l.safetensors", clip_type="flux")
```

---

### 3. Load Dual CLIP GGUF

```python
load_dual_clip_gguf(
    clip_name1: str,
    clip_name2: str,
    clip_type: str = "sdxl"
) → clip
```

Load two CLIP text encoders (for SDXL, SD3, Flux, etc.)

**Parameters:**
- `clip_name1` (str): First CLIP file (e.g., "clip-l.gguf")
- `clip_name2` (str): Second CLIP file (e.g., "t5xxl.gguf")
- `clip_type` (str): Dual CLIP type:
  - `"sdxl"` - SDXL (clip-l + clip-g)
  - `"sd3"` - SD3 (clip-l + clip-g / clip-l + t5 / clip-g + t5)
  - `"flux"` - Flux (clip-l + t5)
  - `"hunyuan_video"`, `"hidream"`, `"hunyuan_image"`

**Returns:**
- `clip`: Dual CLIP model

**Example:**
```python
from bricks.gguf_bricks import load_dual_clip_gguf

# Load SDXL dual CLIP
clip = load_dual_clip_gguf(
    "clip-l-Q8_0.gguf",
    "clip-g-Q8_0.gguf",
    clip_type="sdxl"
)

# Load Flux (mix GGUF + safetensors)
clip = load_dual_clip_gguf(
    "clip-l.safetensors",
    "t5xxl-Q4_K_M.gguf",
    clip_type="flux"
)
```

---

### 4. Load Triple CLIP GGUF

```python
load_triple_clip_gguf(
    clip_name1: str,
    clip_name2: str,
    clip_name3: str,
    clip_type: str = "sd3"
) → clip
```

Load three CLIP text encoders (for SD3 with all encoders).

**Parameters:**
- `clip_name1`, `clip_name2`, `clip_name3`: Three CLIP files
- `clip_type` (str): Usually `"sd3"`

**Example:**
```python
from bricks.gguf_bricks import load_triple_clip_gguf

# Load SD3 triple CLIP
clip = load_triple_clip_gguf(
    "clip-l-Q8_0.gguf",
    "clip-g-Q8_0.gguf",
    "t5xxl-Q4_K_M.gguf",
    clip_type="sd3"
)
```

---

### 5. Get GGUF Info

```python
get_gguf_info() → dict
```

Get information about GGUF support and available quantization types.

**Returns:**
- `dict`: Information about GGUF availability, quant types, and supported models

**Example:**
```python
from bricks.gguf_bricks import get_gguf_info

info = get_gguf_info()
print(f"GGUF available: {info['available']}")
print(f"Quant types: {info['quantization_types']}")
```

---

## Quantization Types

GGUF supports various quantization levels:

| Type | Size | Quality | Use Case |
|------|------|---------|----------|
| **Q4_K_S** | 4-bit | Good | ⭐ Recommended for most cases |
| **Q4_K_M** | 4-bit | Better | Good balance |
| **Q5_K_M** | 5-bit | High | ⭐ Recommended for quality |
| **Q6_K** | 6-bit | Very High | High quality, still compact |
| **Q8_0** | 8-bit | Excellent | ⭐ Best quality |
| **F16** | float16 | Perfect | No quantization |
| Q4_0 | 4-bit | Low | Smallest, lowest quality |
| Q5_K_S | 5-bit | Good | Smaller variant |

**Recommendations:**
- **Best balance**: Q4_K_S or Q5_K_M
- **Best quality**: Q8_0
- **Smallest size**: Q4_K_S
- **Text encoders**: Q8_0 for best results, Q4_K_M for size savings

---

## Complete Example (Wan Video Generation)

```python
from bricks.gguf_bricks import load_clip_gguf, load_unet_gguf
from bricks.wan_bricks import (
    load_clip_vision, clip_vision_encode,
    load_vae, wan_image_to_video
)
from bricks.comfy_bricks import clip_encode, common_ksampler, vae_decode

# 1. Load models with GGUF
clip = load_clip_gguf("umt5-xxl-Q8_0.gguf", clip_type="wan")
model = load_unet_gguf("wan-2.1-Q4_K_S.gguf")

# 2. Load non-GGUF models
clip_vision = load_clip_vision("clip_vision_g.safetensors")
vae = load_vae("wan_2.1_vae.safetensors")

# 3. Encode text
positive = clip_encode(clip, "a cat walking in garden")
negative = clip_encode(clip, "blurry, low quality")

# 4. Encode reference image (optional)
clip_vision_output = clip_vision_encode(clip_vision, image)

# 5. Setup video generation
positive, negative, latent = wan_image_to_video(
    positive, negative, vae,
    width=832, height=480, length=81,
    clip_vision_output=clip_vision_output,
    start_image=first_frame
)

# 6. Sample
samples, seed = common_ksampler(
    model, latent, positive, negative,
    steps=20, cfg=7.0
)

# 7. Decode
video = vae_decode(vae, samples)
```

---

## VRAM Savings

Example VRAM usage for Flux Dev:

| Format | Size | VRAM (float16) | VRAM (Quantized) |
|--------|------|----------------|------------------|
| F16 | 24 GB | ~24 GB | ~24 GB |
| Q8_0 | 12 GB | ~12 GB | ~12 GB |
| Q5_K_M | 8 GB | ~8 GB | ~8 GB |
| Q4_K_S | 6 GB | ~6 GB | ~6 GB |

**Note:** Actual VRAM usage depends on:
- Dequantization settings
- LoRA patches
- Batch size
- Resolution

---

## Model File Locations

GGUF models should be placed in standard ComfyUI model folders:

```
models_storage/
├── diffusion_models/        or    ├── unet/
│   ├── flux1-dev-Q4_K_S.gguf      │   └── wan-2.1-Q8_0.gguf
│   └── sd3-Q5_K_M.gguf            │
│                                  │
├── text_encoders/            or    ├── clip/
│   ├── t5xxl-Q4_K_M.gguf          │   ├── clip-l-Q8_0.gguf
│   ├── umt5-xxl-Q8_0.gguf         │   └── clip-g.safetensors
│   └── llama-3.1-Q6_K.gguf        │
│                                  │
└── clip_vision/                   │
    └── clip_vision_g.safetensors  │
```

---

## Finding GGUF Models

GGUF models for Flux, Wan, SD3, etc. can be found on:

**Hugging Face:**
- https://huggingface.co/city96
- https://huggingface.co/models?search=gguf

**Search terms:**
- "flux gguf"
- "wan gguf"
- "sd3 gguf"
- "t5xxl gguf"

---

## Troubleshooting

### Import Error

```
ComfyUI-GGUF not available. GGUF loading will not work.
```

**Solution:**
```bash
cd /qs/kino/backend/ComfyUI/custom_nodes
git clone https://github.com/city96/ComfyUI-GGUF.git
cd ComfyUI-GGUF
pip install -r requirements.txt
```

### Model Not Found

```
ERROR: Could not detect model type
```

**Solution:**
- Make sure GGUF file is in correct folder
- Check file is valid GGUF format
- Try a different quantization level

### Out of Memory

**Solutions:**
1. Use lower quantization (Q4 instead of Q8)
2. Enable `patch_on_device=False` (default)
3. Use lower resolution
4. Reduce batch size

---

## Limitations

1. **VAE**: GGUF VAE is rarely used (not implemented in these bricks)
2. **LoRA**: Some LoRA patches may not work perfectly with quantized models
3. **Precision**: Very low quant levels (Q4_0) may reduce quality

---

## See Also

- [GGUF Format Specification](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md)
- [ComfyUI-GGUF Documentation](https://github.com/city96/ComfyUI-GGUF)
- [Wan Bricks](./README_WAN.md) - For Wan video generation
- [Comfy Bricks](./README.md) - Core utilities

