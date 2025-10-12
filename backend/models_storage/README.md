# Models Storage

This directory stores AI model files for the Kino project. Model files are **not tracked in git** due to their large size.

## Directory Structure

```
models_storage/
├── DiffusionModels/     # Diffusion model files
├── StableDiffusion/     # Stable Diffusion checkpoints
├── Lora/                # LoRA weight files
├── TextEncoders/        # Text encoder models (CLIP, T5, etc.)
├── ClipVision/          # CLIP Vision models
└── VAE/                 # VAE models
```

## Supported Model Formats

- `.safetensors` (recommended)
- `.ckpt`
- `.pt` / `.pth`
- `.bin`
- `.onnx`
- `.pb`
- `.h5`

## Adding Models

### For SDXL Plugin

Place your SDXL model checkpoint in the `StableDiffusion/` directory:

```bash
# Example: Copy SDXL model
cp ~/Downloads/sd_xl_base_1.0.safetensors models_storage/StableDiffusion/
```

Then use it in your task:
```json
{
  "type": "sdxl",
  "data": {
    "model_name": "sd_xl_base_1.0.safetensors",
    "prompt": "..."
  }
}
```

### Directory Usage Guide

- **DiffusionModels/** - General diffusion models (Flux, Cascade, etc.)
- **StableDiffusion/** - Stable Diffusion 1.5, 2.1, SDXL checkpoints
- **Lora/** - LoRA adapters and fine-tuned weights
- **TextEncoders/** - CLIP, T5, and other text encoders
- **ClipVision/** - CLIP Vision models for image conditioning
- **VAE/** - Standalone VAE models

## Git Tracking

- ✅ Directory structure is tracked (via `.gitkeep` files)
- ❌ Model files are **NOT** tracked (ignored by `.gitignore`)

This ensures:
- Repository stays lightweight
- Directory structure is preserved
- Each developer manages their own models

## Downloading Models

Popular sources:
- [Hugging Face](https://huggingface.co/models)
- [Civitai](https://civitai.com/)
- [Stability AI](https://stability.ai/)

Example commands:
```bash
# Using wget
wget -P models_storage/StableDiffusion/ https://huggingface.co/...

# Using git-lfs (for Hugging Face)
cd models_storage/StableDiffusion/
git lfs install
git clone https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0
```

## Disk Space

Typical model sizes:
- SDXL Base: ~6.5 GB
- SD 1.5: ~4 GB
- LoRA: 10-500 MB
- VAE: ~300 MB

**Recommendation:** Ensure at least 20-50 GB free space for model storage.

## Sharing Models in Team

Since models are not in git, team members need to:

1. Download models separately
2. Place them in the correct directories
3. Use consistent naming conventions

**Tip:** Create a shared document listing:
- Required models
- Download links
- MD5/SHA256 checksums for verification

