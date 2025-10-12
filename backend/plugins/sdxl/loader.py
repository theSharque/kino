"""
SDXL (Stable Diffusion XL) plugin loader
"""
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from pathlib import Path
from PIL import Image
import numpy as np
import torch

from ..base_plugin import BasePlugin, PluginResult
import bricks.comfy_bricks as comfy_bricks
from config import Config


class SDXLPlugin(BasePlugin):
    """
    Stable Diffusion XL generator plugin

    This plugin generates images using SDXL model via ComfyUI backend.
    """

    def __init__(self):
        super().__init__()
        self.model = None
        self.clip = None
        self.vae = None
        self.loaded_checkpoint = None

    async def generate(
        self,
        task_id: int,
        data: Dict[str, Any],
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> PluginResult:
        """
        Generate image using SDXL

        Expected data parameters:
        - prompt: str (required) - Text prompt for generation
        - negative_prompt: str (optional) - Negative prompt
        - width: int (optional, default: 1024) - Image width
        - height: int (optional, default: 1024) - Image height
        - steps: int (optional, default: 30) - Number of inference steps
        - cfg_scale: float (optional, default: 7.5) - CFG scale
        - model_name: str (required) - Model checkpoint filename in StableDiffusion folder
        - sampler: str (optional, default: "dpmpp_2m_sde") - Sampler name
        - project_id: int (optional) - Project ID to save frame to
        """
        try:
            self.is_running = True
            self.should_stop = False
            self.progress = 0.0

            # Extract and validate parameters
            prompt = data.get('prompt')
            if not prompt:
                return PluginResult(
                    success=False,
                    data={},
                    error="Parameter 'prompt' is required"
                )

            model_name = data.get('model_name')
            if not model_name:
                return PluginResult(
                    success=False,
                    data={},
                    error="Parameter 'model_name' is required"
                )

            negative_prompt = data.get('negative_prompt', '')
            width = data.get('width', 1024)
            height = data.get('height', 1024)
            steps = data.get('steps', 30)
            cfg_scale = data.get('cfg_scale', 7.5)
            sampler = data.get('sampler', 'dpmpp_2m_sde')
            project_id = data.get('project_id', None)

            # Check for stop request
            if self.should_stop:
                return PluginResult(success=False, data={}, error="Generation stopped")

            # Step 1: Load checkpoint (5%)
            await self.update_progress(5.0, progress_callback)
            ckpt_path = os.path.join(Config.MODELS_DIR, "StableDiffusion", model_name)

            if not os.path.exists(ckpt_path):
                return PluginResult(
                    success=False,
                    data={},
                    error=f"Model checkpoint not found: {ckpt_path}"
                )

            # Load checkpoint (only if not already loaded or different checkpoint)
            if self.loaded_checkpoint != ckpt_path:
                try:
                    (self.model, self.clip, self.vae, _) = comfy_bricks.load_checkpoint_plugin(ckpt_path)
                    self.loaded_checkpoint = ckpt_path
                except Exception as e:
                    return PluginResult(
                        success=False,
                        data={},
                        error=f"Failed to load checkpoint: {str(e)}"
                    )

            if self.should_stop:
                return PluginResult(success=False, data={}, error="Generation stopped")

            # Step 2: Encode prompts (15%)
            await self.update_progress(15.0, progress_callback)
            try:
                positive = comfy_bricks.clip_encode(self.clip, prompt)
                negative = comfy_bricks.clip_encode(self.clip, negative_prompt)
            except Exception as e:
                return PluginResult(
                    success=False,
                    data={},
                    error=f"Failed to encode prompts: {str(e)}"
                )

            if self.should_stop:
                return PluginResult(success=False, data={}, error="Generation stopped")

            # Step 3: Generate latent image (20%)
            await self.update_progress(20.0, progress_callback)
            latent = comfy_bricks.generate_latent_image(width, height)

            if self.should_stop:
                return PluginResult(success=False, data={}, error="Generation stopped")

            # Step 4: Run KSampler (20% -> 85%)
            await self.update_progress(25.0, progress_callback)
            try:
                sample = comfy_bricks.common_ksampler(
                    self.model,
                    latent,
                    positive,
                    negative,
                    steps,
                    cfg_scale,
                    sampler_name=sampler
                )
            except Exception as e:
                return PluginResult(
                    success=False,
                    data={},
                    error=f"KSampler failed: {str(e)}"
                )

            # Simulate progress during sampling
            await self.update_progress(85.0, progress_callback)

            if self.should_stop:
                return PluginResult(success=False, data={}, error="Generation stopped")

            # Step 5: Decode VAE (90%)
            await self.update_progress(90.0, progress_callback)
            try:
                image = comfy_bricks.vae_decode(self.vae, sample)
            except Exception as e:
                return PluginResult(
                    success=False,
                    data={},
                    error=f"VAE decode failed: {str(e)}"
                )

            if self.should_stop:
                return PluginResult(success=False, data={}, error="Generation stopped")

            # Step 6: Save frame (95%)
            await self.update_progress(95.0, progress_callback)
            try:
                # Ensure frames directory exists
                frames_dir = Path(Config.FRAMES_DIR)
                frames_dir.mkdir(parents=True, exist_ok=True)

                # Generate unique filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"task_{task_id}_{timestamp}.png"
                output_path = frames_dir / filename

                # Save image
                for (batch_number, img_tensor) in enumerate(image):
                    i = 255. * img_tensor.cpu().detach().numpy()
                    img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
                    img.save(str(output_path), compress_level=4)

                output_path_str = str(output_path)

            except Exception as e:
                return PluginResult(
                    success=False,
                    data={},
                    error=f"Failed to save image: {str(e)}"
                )

            # Step 7: Complete (100%)
            await self.update_progress(100.0, progress_callback)

            result_data = {
                'output_path': output_path_str,
                'filename': filename,
                'prompt': prompt,
                'negative_prompt': negative_prompt,
                'width': width,
                'height': height,
                'steps': steps,
                'cfg_scale': cfg_scale,
                'sampler': sampler,
                'model_name': model_name,
                'project_id': project_id
            }

            self.is_running = False
            return PluginResult(
                success=True,
                data=result_data
            )

        except Exception as e:
            self.is_running = False
            return PluginResult(
                success=False,
                data={},
                error=f"SDXL generation error: {str(e)}"
            )

    async def stop(self):
        """Stop SDXL generation"""
        self.should_stop = True
        self.is_running = False

        # Add any cleanup code here if needed
        # For example, stop the model inference loop

    @classmethod
    def get_plugin_info(cls) -> Dict[str, Any]:
        """Get SDXL plugin information"""
        return {
            'name': 'sdxl',
            'version': '1.0.0',
            'description': 'Stable Diffusion XL image generator via ComfyUI backend',
            'author': 'Kino Team',
            'visible': True,  # Show in UI
            'model_type': 'diffusion',
            'parameters': {
                'prompt': {
                    'type': 'string',
                    'required': True,
                    'description': 'Text prompt for image generation',
                    'example': 'A beautiful landscape with mountains and lake'
                },
                'model_name': {
                    'type': 'model_selection',
                    'category': 'StableDiffusion',
                    'required': True,
                    'description': 'Model checkpoint filename (must be in models_storage/StableDiffusion/ folder)',
                    'example': 'sd_xl_base_1.0.safetensors'
                },
                'negative_prompt': {
                    'type': 'string',
                    'required': False,
                    'default': '',
                    'description': 'Negative prompt (what to avoid)',
                    'example': 'blurry, low quality, distorted'
                },
                'width': {
                    'type': 'integer',
                    'required': False,
                    'default': 1024,
                    'min': 512,
                    'max': 2048,
                    'description': 'Image width in pixels (should be multiple of 8)'
                },
                'height': {
                    'type': 'integer',
                    'required': False,
                    'default': 1024,
                    'min': 512,
                    'max': 2048,
                    'description': 'Image height in pixels (should be multiple of 8)'
                },
                'steps': {
                    'type': 'integer',
                    'required': False,
                    'default': 30,
                    'min': 1,
                    'max': 150,
                    'description': 'Number of inference steps'
                },
                'cfg_scale': {
                    'type': 'float',
                    'required': False,
                    'default': 7.5,
                    'min': 1.0,
                    'max': 20.0,
                    'description': 'CFG (Classifier Free Guidance) scale'
                },
                'sampler': {
                    'type': 'string',
                    'required': False,
                    'default': 'dpmpp_2m_sde',
                    'options': ['euler', 'euler_a', 'dpmpp_2m', 'dpmpp_2m_sde', 'dpmpp_2m_karras', 'dpmpp_sde', 'ddim', 'uni_pc'],
                    'description': 'Sampling algorithm'
                },
                'project_id': {
                    'type': 'integer',
                    'required': False,
                    'description': 'Project ID to associate generated frame with (optional)'
                }
            },
            'capabilities': {
                'supports_stop': True,
                'supports_progress': True,
                'supports_batch': False,
                'estimated_time_per_step': 0.5  # seconds
            }
        }

