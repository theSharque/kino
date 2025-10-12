# SDXL Plugin

Stable Diffusion XL image generation plugin using ComfyUI backend.

## Description

This plugin generates images using SDXL models through the ComfyUI framework. It supports text-to-image generation with full control over sampling parameters.

## Requirements

- SDXL model checkpoint placed in `models_storage/StableDiffusion/` directory
- ComfyUI dependencies (already included in `comfy/` directory)
- Sufficient GPU memory for SDXL inference

## Parameters

### Required Parameters

- **prompt** (string): Text prompt for image generation
  - Example: `"A beautiful landscape with mountains and lake"`

- **model_name** (string): Model checkpoint filename
  - Must be located in `models_storage/StableDiffusion/` folder
  - Example: `"sd_xl_base_1.0.safetensors"`

### Optional Parameters

- **negative_prompt** (string): Negative prompt to avoid certain elements
  - Default: `""`
  - Example: `"blurry, low quality, distorted"`

- **width** (integer): Image width in pixels (should be multiple of 8)
  - Default: `1024`
  - Range: 512-2048

- **height** (integer): Image height in pixels (should be multiple of 8)
  - Default: `1024`
  - Range: 512-2048

- **steps** (integer): Number of inference steps
  - Default: `30`
  - Range: 1-150

- **cfg_scale** (float): CFG (Classifier Free Guidance) scale
  - Default: `7.5`
  - Range: 1.0-20.0

- **sampler** (string): Sampling algorithm
  - Default: `"dpmpp_2m_sde"`
  - Options: `euler`, `euler_a`, `dpmpp_2m`, `dpmpp_2m_sde`, `dpmpp_2m_karras`, `dpmpp_sde`, `ddim`, `uni_pc`

- **project_id** (integer): Project ID to associate the generated frame with
  - Optional field for linking to a specific project

## Usage Example

### Create Task via API

```bash
curl -X POST http://localhost:8000/api/v1/generator/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Generate SDXL Image",
    "type": "sdxl",
    "data": {
      "prompt": "A serene mountain landscape at sunset",
      "negative_prompt": "blurry, low quality",
      "model_name": "sd_xl_base_1.0.safetensors",
      "width": 1024,
      "height": 1024,
      "steps": 30,
      "cfg_scale": 7.5,
      "sampler": "dpmpp_2m_sde"
    }
  }'
```

### Start Generation

```bash
curl -X POST http://localhost:8000/api/v1/generator/tasks/{task_id}/generate
```

### Check Progress

```bash
curl http://localhost:8000/api/v1/generator/tasks/{task_id}/progress
```

### Stop Generation

```bash
curl -X POST http://localhost:8000/api/v1/generator/tasks/{task_id}/stop
```

## Output

Generated images are saved to `data/frames/` directory with the naming pattern:
```
task_{task_id}_{timestamp}.png
```

The task result will contain:
```json
{
  "output_path": "/path/to/image.png",
  "filename": "task_1_20250101_120000.png",
  "prompt": "...",
  "negative_prompt": "...",
  "width": 1024,
  "height": 1024,
  "steps": 30,
  "cfg_scale": 7.5,
  "sampler": "dpmpp_2m_sde",
  "model_name": "sd_xl_base_1.0.safetensors",
  "project_id": null
}
```

## Implementation Details

The plugin follows this workflow:

1. **Load Checkpoint** (5% progress): Loads the SDXL model from checkpoint file
   - Model is cached and only reloaded if checkpoint changes
   - Checkpoint must exist in `models_storage/StableDiffusion/`

2. **Encode Prompts** (15% progress): Encodes positive and negative prompts using CLIP

3. **Generate Latent** (20% progress): Creates empty latent image tensor

4. **Run Sampler** (25-85% progress): Executes KSampler with specified parameters

5. **Decode VAE** (90% progress): Decodes latent to pixel space using VAE

6. **Save Frame** (95% progress): Saves the generated image as PNG

7. **Complete** (100% progress): Returns result with file path and metadata

## Error Handling

The plugin will return errors for:
- Missing required parameters (`prompt`, `model_name`)
- Model checkpoint not found
- Checkpoint loading failures
- CLIP encoding errors
- Sampling errors
- VAE decoding errors
- File save errors

## Notes

- The plugin supports stopping generation at any point
- Progress is reported throughout the generation process
- Model is kept in memory between generations for faster subsequent runs
- Images are saved with compression level 4 (good balance between size and quality)

