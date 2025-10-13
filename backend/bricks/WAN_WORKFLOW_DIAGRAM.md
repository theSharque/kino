# Wan Video Generation Workflow Diagram

## Data Flow Visualization

```
┌─────────────────────────────────────────────────────────────────────┐
│                        WAN VIDEO GENERATION                         │
│                           WORKFLOW                                  │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐
│  STEP 1:     │
│  Load Models │
└──────────────┘
        │
        ├─────► load_clip("umt5_xxl.safetensors", clip_type="wan")
        │              │
        │              └─────► [clip] CLIP Text Encoder
        │
        ├─────► load_clip_vision("clip_vision_g.safetensors")
        │              │
        │              └─────► [clip_vision] CLIP Vision Model
        │
        └─────► load_vae("wan_2.1_vae.safetensors")
                       │
                       └─────► [vae] VAE Model

┌──────────────┐
│  STEP 2:     │
│  Text Encode │
└──────────────┘
        │
        ├─────► clip_encode(clip, "positive prompt")
        │              │
        │              └─────► [positive] Conditioning Tensor
        │
        └─────► clip_encode(clip, "negative prompt")
                       │
                       └─────► [negative] Conditioning Tensor

┌──────────────┐
│  STEP 3:     │
│ Vision Encode│ (optional)
└──────────────┘
        │
        └─────► clip_vision_encode(clip_vision, image, crop="center")
                       │
                       └─────► [clip_vision_output] Vision Embedding

┌──────────────┐
│  STEP 4:     │
│  Setup Video │
└──────────────┘
        │
        └─────► wan_image_to_video(
                    positive, negative, vae,
                    width=832, height=480, length=81,
                    clip_vision_output=..., start_image=...
                )
                       │
                       ├─────► [positive] Modified Conditioning
                       ├─────► [negative] Modified Conditioning
                       └─────► [latent] Empty Latent Dict
                                   {"samples": Tensor[1,16,21,60,104]}

┌──────────────┐
│  STEP 5:     │
│  Sample      │
└──────────────┘
        │
        └─────► common_ksampler(
                    model, latent, positive, negative,
                    steps=20, cfg=7.0, sampler_name="euler"
                )
                       │
                       └─────► [samples] Generated Latent
                                   {"samples": Tensor[1,16,21,60,104]}

┌──────────────┐
│  STEP 6:     │
│  Decode      │
└──────────────┘
        │
        └─────► vae_decode(vae, samples)
                       │
                       └─────► [video_frames] Image Tensor
                                   Tensor[81, 480, 832, 3]
                                   (frames, height, width, channels)
```

---

## Component Relationships

```
                    ┌─────────────┐
                    │   Models    │
                    │  Directory  │
                    └─────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │   CLIP   │    │   CLIP   │    │   VAE    │
    │   Text   │    │  Vision  │    │  Encoder │
    └──────────┘    └──────────┘    └──────────┘
           │               │               │
           ▼               ▼               │
    ┌──────────┐    ┌──────────┐          │
    │ Positive │    │  Vision  │          │
    │   Cond.  │    │  Output  │          │
    └──────────┘    └──────────┘          │
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ Negative │    │   Wan    │────►│  Image   │
    │   Cond.  │───►│ I2V Node │    │  Encode  │
    └──────────┘    └──────────┘    └──────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Latent    │
                    │   Tensor    │
                    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Sampler    │
                    │  (KSampler) │
                    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Generated   │
                    │   Latent    │
                    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    VAE      │
                    │   Decode    │
                    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Video     │
                    │   Frames    │
                    └─────────────┘
```

---

## Tensor Shapes Through Pipeline

```
Input Image (optional)
    └─► [1, H, W, 3] ────────┐
                              │
                              ▼
                       CLIP Vision Encode
                              │
                              ▼
                    Vision Embedding
                       [1, N, 1280]
                              │
                              ▼
Text Prompts                  │
    ├─► "positive" ───► CLIP Text ───► Positive Cond.
    │                                   [1, 77, 1280]
    │                                          │
    └─► "negative" ───► CLIP Text ───► Negative Cond.
                                        [1, 77, 1280]
                                               │
                        ┌──────────────────────┴─────────┐
                        │                                │
                        ▼                                ▼
Start Image (optional)  │                                │
    └─► [N, H, W, 3] ───┤                                │
                        │                                │
                        ▼                                ▼
                  VAE Encode                      Wan I2V Setup
                        │                                │
                        ▼                                ▼
                Concat Latent                  Empty Latent + Conditioning
                [1, 16, T, H/8, W/8]            [1, 16, T, H/8, W/8]
                        │                                │
                        └────────────┬───────────────────┘
                                     │
                                     ▼
                              Modified Conditioning
                                     │
                                     ▼
                                 Sampler
                                     │
                                     ▼
                            Generated Latent
                            [1, 16, T, H/8, W/8]
                                     │
                                     ▼
                                VAE Decode
                                     │
                                     ▼
                              Video Frames
                              [F, H, W, 3]

Legend:
  T = ((length-1)//4)+1  (temporal dimension)
  F = length             (frame count)
  H = height             (e.g., 480)
  W = width              (e.g., 832)
  N = number of frames in start image
```

---

## Parameter Flow

```
                        ┌─────────────────┐
                        │ Input Parameters│
                        └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │  width   │ │  height  │ │  length  │
              │   832    │ │   480    │ │    81    │
              └──────────┘ └──────────┘ └──────────┘
                    │            │            │
                    └────────────┼────────────┘
                                 ▼
                        ┌─────────────────┐
                        │  Latent Shape   │
                        │ Calculation     │
                        └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
              ┌──────────┐ ┌──────────┐ ┌──────────┐
              │channels  │ │ temporal │ │ spatial  │
              │   = 16   │ │ = (81-1) │ │ = 480/8  │
              │          │ │   //4+1  │ │   = 60   │
              │          │ │   = 21   │ │   832/8  │
              │          │ │          │ │   = 104  │
              └──────────┘ └──────────┘ └──────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Final Shape:   │
                        │ [1,16,21,60,104]│
                        └─────────────────┘
```

---

## Conditioning Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     CONDITIONING SETUP                      │
└─────────────────────────────────────────────────────────────┘

Initial State:
    Positive: [1, 77, 1280]  ← from CLIP text encoder
    Negative: [1, 77, 1280]  ← from CLIP text encoder

Add CLIP Vision (optional):
    Positive: + {"clip_vision_output": [1, N, 1280]}
    Negative: + {"clip_vision_output": [1, N, 1280]}

Add Start Image (optional):
    Encoded Latent: [1, 16, T, H/8, W/8]
    Mask: [1, 1, T, H/8, W/8]  ← 0 where we keep image, 1 where we denoise

    Positive: + {"concat_latent_image": latent, "concat_mask": mask}
    Negative: + {"concat_latent_image": latent, "concat_mask": mask}

Final Conditioning:
    ┌────────────────────────────────────────────┐
    │ Positive:                                  │
    │   - text_embedding: [1, 77, 1280]         │
    │   - clip_vision_output: [1, N, 1280]      │
    │   - concat_latent_image: [1,16,T,H/8,W/8] │
    │   - concat_mask: [1,1,T,H/8,W/8]          │
    └────────────────────────────────────────────┘
    ┌────────────────────────────────────────────┐
    │ Negative: (same structure)                 │
    └────────────────────────────────────────────┘
```

---

## File Structure

```
backend/
├── bricks/
│   ├── comfy_bricks.py          ← Core ComfyUI utilities
│   ├── comfy_constants.py       ← Sampler/scheduler constants
│   ├── generation_params.py     ← Generation params utilities
│   │
│   ├── wan_bricks.py            ← NEW: Wan utilities
│   ├── README_WAN.md            ← NEW: Detailed documentation
│   ├── WAN_COMPONENTS_SUMMARY.md ← NEW: Quick reference
│   ├── WAN_WORKFLOW_DIAGRAM.md  ← NEW: This file
│   └── test_wan_bricks.py       ← NEW: Test script
│
├── ComfyUI/                     ← Full ComfyUI installation
│   ├── nodes.py                 ← Source for loaders
│   ├── comfy_extras/
│   │   └── nodes_wan.py         ← Source for WanImageToVideo
│   └── ...
│
└── models_storage/              ← Model files
    ├── clip_vision/
    ├── text_encoders/
    ├── vae/
    └── ...
```

---

## Usage Example (Numbered Steps)

```python
# 1️⃣ Import functions
from bricks.wan_bricks import (
    load_clip, load_clip_vision, clip_vision_encode,
    load_vae, wan_image_to_video
)
from bricks.comfy_bricks import clip_encode, common_ksampler, vae_decode

# 2️⃣ Load models
clip = load_clip("umt5_xxl.safetensors", clip_type="wan")
clip_vision = load_clip_vision("clip_vision_g.safetensors")
vae = load_vae("wan_2.1_vae.safetensors")
# model = ... load Wan diffusion model

# 3️⃣ Prepare text conditioning
positive = clip_encode(clip, "a cat walking in garden, high quality")
negative = clip_encode(clip, "blurry, low quality")

# 4️⃣ (Optional) Prepare image conditioning
clip_vision_output = clip_vision_encode(clip_vision, reference_image)

# 5️⃣ Setup video generation
positive, negative, latent = wan_image_to_video(
    positive=positive,
    negative=negative,
    vae=vae,
    width=832,
    height=480,
    length=81,
    clip_vision_output=clip_vision_output,
    start_image=first_frame
)

# 6️⃣ Sample (generate latent)
samples, seed = common_ksampler(
    model=model,
    latent=latent,
    positive=positive,
    negative=negative,
    steps=20,
    cfg=7.0,
    sampler_name="euler",
    scheduler="simple"
)

# 7️⃣ Decode to video frames
video_frames = vae_decode(vae, samples)
# Result: Tensor[81, 480, 832, 3]
```

---

## Notes

- **Temporal Compression**: Wan VAE compresses time by 4x
  - 81 frames → 21 temporal latent steps
  - Formula: `T = ((length - 1) // 4) + 1`

- **Spatial Compression**: Like SD, 8x compression
  - 480×832 → 60×104 latent spatial dims
  - Formula: `H_latent = height // 8`, `W_latent = width // 8`

- **Channels**: Wan uses 16 latent channels (SD uses 4)

- **Valid Frame Lengths**: Must satisfy `length % 4 == 1`
  - Valid: 17, 33, 49, 81, 97, 113, ...
  - Invalid: 20, 50, 80, 100, ...

