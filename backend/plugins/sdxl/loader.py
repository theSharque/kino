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
from bricks.generation_params import save_generation_params
from bricks.comfy_constants import SAMPLER_NAMES, SCHEDULER_NAMES, RECOMMENDED_SAMPLERS, RECOMMENDED_SCHEDULERS
from bricks.preview_bricks import create_preview_callback, save_preview_image
from config import Config
from database import get_db
from services.frame_service import FrameService
from models.frame import FrameCreate


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
        self.current_frame_id = None
        self.preview_path = None
        self.db = None
        self.frame_service = None

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
        - steps: int (optional, default: 32) - Number of inference steps
        - cfg_scale: float (optional, default: 3.5) - CFG scale
        - model_name: str (required) - Model checkpoint filename in StableDiffusion folder
        - sampler: str (optional, default: "dpmpp_2m_sde") - Sampler name
        - scheduler: str (optional, default: "sgm_uniform") - Scheduler type
        - seed: int (optional, default: None) - Random seed (None = auto-generate)
        - loras: list (optional) - List of LoRA configurations with lora_name, strength_model, strength_clip
        - project_id: int (optional) - Project ID (automatically added by frontend)
        """
        try:
            self.is_running = True
            self.should_stop = False
            self.progress = 0.0

            # Check if this is a regeneration request
            regenerate_frame_id = data.get('frame_id', None)
            print(f"DEBUG: data = {data}")
            print(f"DEBUG: regenerate_frame_id = {regenerate_frame_id}")

            # Extract and validate parameters
            prompt = data.get('prompt')
            model_name = data.get('model_name')

            # Validate required parameters before initializing DB
            if not prompt:
                return PluginResult(
                    success=False,
                    data={},
                    error="Parameter 'prompt' is required"
                )

            if not model_name:
                return PluginResult(
                    success=False,
                    data={},
                    error="Parameter 'model_name' is required"
                )

            negative_prompt = data.get('negative_prompt', '')
            width = data.get('width', 1024)
            height = data.get('height', 1024)
            steps = data.get('steps', 32)
            cfg_scale = data.get('cfg_scale', 3.5)
            sampler = data.get('sampler', 'dpmpp_2m_sde')
            scheduler = data.get('scheduler', 'sgm_uniform')
            seed = data.get('seed', None)  # None = random seed
            project_id = data.get('project_id', None)
            loras = data.get('loras', [])  # List of LoRA configurations

            # Initialize frame service for preview updates using global DB
            self.db = get_db()
            self.frame_service = FrameService(self.db)

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

            # Handle frame creation or regeneration
            if project_id:
                try:
                    if regenerate_frame_id:
                        # Regeneration mode: use existing frame
                        existing_frame = await self.frame_service.get_frame_by_id(regenerate_frame_id)
                        if not existing_frame:
                            return PluginResult(
                                success=False,
                                data={},
                                error=f"Frame {regenerate_frame_id} not found for regeneration"
                            )

                        # Delete old image file
                        old_image_path = Path(existing_frame.path)
                        if old_image_path.exists():
                            try:
                                old_image_path.unlink()
                                print(f"Deleted old image: {old_image_path}")
                            except Exception as e:
                                print(f"Warning: Failed to delete old image {old_image_path}: {e}")

                        # Update generation parameters JSON with new seed
                        try:
                            from bricks.generation_params import save_generation_params
                            updated_params = {
                                'prompt': prompt,
                                'negative_prompt': negative_prompt,
                                'width': width,
                                'height': height,
                                'steps': steps,
                                'cfg_scale': cfg_scale,
                                'model_name': model_name,
                                'sampler': sampler,
                                'scheduler': scheduler,
                                'seed': seed,
                                'loras': loras,
                                'generator': 'sdxl'
                            }
                            save_generation_params(regenerate_frame_id, updated_params)
                            print(f"Updated generation parameters for frame {regenerate_frame_id}")
                        except Exception as e:
                            print(f"Warning: Failed to update generation parameters: {e}")

                        # Use existing frame's path for preview updates
                        self.current_frame_id = regenerate_frame_id
                        self.preview_path = existing_frame.path
                        print(f"Regenerating frame {self.current_frame_id} at path: {self.preview_path}")

                    # Note: Frame creation for new generation happens later, before KSampler

                except Exception as e:
                    print(f"Warning: Failed to handle frame: {e}")
                    # Continue without frame updates

            if self.should_stop:
                await self.db.close()
                return PluginResult(success=False, data={}, error="Generation stopped")

            # Step 1.5: Apply LoRAs if specified (10%)
            if loras and len(loras) > 0:
                await self.update_progress(10.0, progress_callback)
                try:
                    for lora_config in loras:
                        lora_name = lora_config.get('lora_name')
                        if not lora_name:
                            continue

                        strength_model = lora_config.get('strength_model', 1.0)
                        strength_clip = lora_config.get('strength_clip', 1.0)

                        lora_path = os.path.join(Config.MODELS_DIR, "Lora", lora_name)

                        if not os.path.exists(lora_path):
                            print(f"Warning: LoRA not found: {lora_path}")
                            continue

                        # Apply LoRA to model and clip
                        self.model, self.clip = comfy_bricks.load_lora(
                            lora_path,
                            self.model,
                            self.clip,
                            strength_model,
                            strength_clip
                        )
                        print(f"Applied LoRA: {lora_name} (model: {strength_model}, clip: {strength_clip})")

                except Exception as e:
                    print(f"Warning: Failed to apply LoRA: {str(e)}")
                    # Continue generation without LoRA

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

            # Step 4: Create frame and initial preview image before sampling
            await self.update_progress(20.0, progress_callback)

            # Set up paths for generation
            if not regenerate_frame_id:
                # New generation: create new paths
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"task_{task_id}_{timestamp}.png"
                preview_filename = f"task_{task_id}_{timestamp}_preview.png"
                frames_dir = Path(Config.FRAMES_DIR)
                frames_dir.mkdir(parents=True, exist_ok=True)

                self.preview_path = str(frames_dir / preview_filename)
                final_path = str(frames_dir / filename)
            else:
                # Regeneration: use existing frame's path
                final_path = self.preview_path  # Same path for both preview and final

            # Create initial preview from latent (blank or noise pattern)
            try:
                # Generate initial preview from latent
                from bricks.preview_bricks import PreviewGenerator
                preview_gen = PreviewGenerator(self.model)
                initial_preview = preview_gen.generate_preview(latent["samples"])
                if initial_preview:
                    from bricks.preview_bricks import save_preview_image
                    save_preview_image(initial_preview, self.preview_path)
                    print(f"Created initial preview: {self.preview_path}")
                else:
                    # Create blank image if preview generation fails
                    blank_img = Image.new('RGB', (width, height), color=(32, 32, 32))
                    blank_img.save(self.preview_path)
                    print(f"Created blank preview: {self.preview_path}")
            except Exception as e:
                print(f"Warning: Failed to create initial preview: {e}")
                # Create blank image as fallback
                blank_img = Image.new('RGB', (width, height), color=(32, 32, 32))
                blank_img.save(self.preview_path)

            # Create frame record in database (only if not regenerating)
            if not regenerate_frame_id:
                from models.frame import FrameCreate
                frame_create = FrameCreate(
                    path=self.preview_path,  # Initially point to preview
                    generator='sdxl',
                    project_id=project_id
                )
                frame_record = await self.frame_service.create_frame(frame_create)
                self.current_frame_id = frame_record.id
                print(f"Created frame record: ID {self.current_frame_id}")

            # Broadcast "generation started" message with preview path
            from handlers.websocket import broadcast_message
            await broadcast_message({
                'type': 'generation_started',
                'data': {
                    'task_id': task_id,
                    'frame_id': self.current_frame_id,
                    'project_id': project_id,
                    'preview_path': self.preview_path,
                    'generator': 'sdxl'
                }
            })
            print(f"Broadcasted generation_started for frame {self.current_frame_id}")

            # Step 5: Run KSampler with preview callback (25% -> 85%)
            await self.update_progress(25.0, progress_callback)

            # Create preview callback to update frame during sampling
            def on_preview(step, total_steps, preview_image):
                """Called at each sampling step - just overwrites the preview file"""
                try:
                    # Update progress (25% + step progress to 85%)
                    step_progress = 25.0 + (step / total_steps) * 60.0
                    if progress_callback:
                        asyncio.create_task(self.update_progress(step_progress, progress_callback))

                    # Simply overwrite preview image file
                    if self.preview_path and preview_image:
                        save_preview_image(preview_image, self.preview_path)
                        if (step + 1) % 5 == 0:  # Log every 5 steps
                            print(f"Preview updated: step {step+1}/{total_steps}")

                except Exception as e:
                    print(f"Warning: Preview update failed: {e}")

            # Create ComfyUI callback with ProgressBar integration
            sampling_callback = create_preview_callback(self.model, steps, on_preview)

            try:
                sample, used_seed = comfy_bricks.common_ksampler(
                    self.model,
                    latent,
                    positive,
                    negative,
                    steps,
                    cfg_scale,
                    sampler_name=sampler,
                    scheduler=scheduler,
                    seed=seed,
                    callback=sampling_callback
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

            # Step 6: Save final frame (95%)
            await self.update_progress(95.0, progress_callback)
            try:
                # Ensure frames directory exists
                frames_dir = Path(Config.FRAMES_DIR)
                frames_dir.mkdir(parents=True, exist_ok=True)

                # Simply overwrite preview file with final image
                output_path_str = self.preview_path
                filename = os.path.basename(output_path_str)

                # Save final image (overwrite preview)
                for (batch_number, img_tensor) in enumerate(image):
                    i = 255. * img_tensor.cpu().detach().numpy()
                    img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
                    img.save(output_path_str, compress_level=4)

                print(f"Saved final image (overwrote preview): {output_path_str}")

                # Frame path is already correct in DB (points to this file)

                # Save generation parameters to JSON file
                if regenerate_frame_id:
                    # For regeneration: save with existing frame_id
                    save_generation_params(
                        frame_id=regenerate_frame_id,
                        plugin_name='sdxl',
                        plugin_version='1.0.0',
                        parameters={
                            'prompt': prompt,
                            'negative_prompt': negative_prompt,
                            'width': width,
                            'height': height,
                            'steps': steps,
                            'cfg_scale': cfg_scale,
                            'sampler': sampler,
                            'scheduler': scheduler,
                            'seed': used_seed,  # Save the actual seed that was used
                            'model_name': model_name,
                            'loras': loras
                        }
                    )
                else:
                    # For new generation: save with task_id
                    save_generation_params(
                        output_path=output_path_str,
                        plugin_name='sdxl',
                        plugin_version='1.0.0',
                        task_id=task_id,
                        timestamp=timestamp,
                        parameters={
                            'prompt': prompt,
                            'negative_prompt': negative_prompt,
                            'width': width,
                            'height': height,
                            'steps': steps,
                            'cfg_scale': cfg_scale,
                            'sampler': sampler,
                            'scheduler': scheduler,
                            'seed': used_seed,  # Save the actual seed that was used
                            'model_name': model_name,
                            'loras': loras
                        },
                        project_id=project_id
                    )

            except Exception as e:
                return PluginResult(
                    success=False,
                    data={},
                    error=f"Failed to save image: {str(e)}"
                )

            # Step 7: Complete (100%)
            await self.update_progress(100.0, progress_callback)

            # Broadcast "generation completed" message
            from handlers.websocket import broadcast_message
            await broadcast_message({
                'type': 'generation_completed',
                'data': {
                    'task_id': task_id,
                    'frame_id': self.current_frame_id,
                    'project_id': project_id,
                    'final_path': output_path_str,
                    'generator': 'sdxl'
                }
            })
            print(f"Broadcasted generation_completed for frame {self.current_frame_id}")

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
                'scheduler': scheduler,
                'seed': used_seed,
                'model_name': model_name,
                'project_id': project_id,
                'frame_id': self.current_frame_id  # Include frame_id to prevent duplicate creation
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
                    'default': 32,
                    'min': 1,
                    'max': 150,
                    'description': 'Number of inference steps'
                },
                'cfg_scale': {
                    'type': 'float',
                    'required': False,
                    'default': 3.5,
                    'min': 1.0,
                    'max': 20.0,
                    'description': 'CFG (Classifier Free Guidance) scale'
                },
                'sampler': {
                    'type': 'selection',
                    'required': False,
                    'default': 'dpmpp_2m_sde',
                    'options': RECOMMENDED_SAMPLERS,  # Use recommended list for better UX
                    'description': 'Sampling algorithm (noise reduction method)'
                },
                'scheduler': {
                    'type': 'selection',
                    'required': False,
                    'default': 'sgm_uniform',
                    'options': SCHEDULER_NAMES,
                    'description': 'Noise schedule (how noise is removed over steps)'
                },
                'seed': {
                    'type': 'integer',
                    'required': False,
                    'default': None,
                    'min': 1,
                    'max': 2147483647,
                    'description': 'Random seed for reproducibility (leave empty for random)'
                },
                'loras': {
                    'type': 'lora_list',
                    'required': False,
                    'default': [],
                    'description': 'List of LoRA models to apply',
                    'item_schema': {
                        'lora_name': {
                            'type': 'model_selection',
                            'category': 'Lora',
                            'required': True,
                            'description': 'LoRA model filename'
                        },
                        'strength_model': {
                            'type': 'float',
                            'required': False,
                            'default': 1.0,
                            'min': 0.0,
                            'max': 2.0,
                            'description': 'LoRA strength for model'
                        },
                        'strength_clip': {
                            'type': 'float',
                            'required': False,
                            'default': 1.0,
                            'min': 0.0,
                            'max': 2.0,
                            'description': 'LoRA strength for CLIP'
                        }
                    }
                }
            },
            'capabilities': {
                'supports_stop': True,
                'supports_progress': True,
                'supports_batch': False,
                'estimated_time_per_step': 0.5  # seconds
            }
        }

