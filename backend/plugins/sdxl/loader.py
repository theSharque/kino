"""
SDXL Plugin Loader for ComfyUI Integration
"""
import os
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from PIL import Image

from config import Config
from database import get_db
from services.frame_service import FrameService
from bricks import comfy_bricks
from bricks.preview_bricks import create_preview_callback
from logger import setup_logging
from ..base_plugin import BasePlugin

# Initialize logger
log = setup_logging()


class PluginResult:
    """Result of plugin execution"""
    def __init__(self, success: bool, data: Dict[str, Any], error: str = ""):
        self.success = success
        self.data = data
        self.error = error


class SDXLLoader:
    """SDXL Plugin Loader for ComfyUI Integration"""

    def __init__(self):
        self.model = None
        self.clip = None
        self.vae = None
        self.loaded_checkpoint = None
        self.is_running = False
        self.should_stop = False
        self.progress = 0.0
        self.preview_path = None
        self.current_frame_id = None
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
        - num_variants: int (optional, default: 1) - Number of variants to generate
        """
        try:
            self.is_running = True
            self.should_stop = False
            self.progress = 0.0

            # Check if this is a regeneration request
            regenerate_frame_id = data.get('frame_id', None)
            log.info("sdxl_generation_start", {"task_id": task_id, "regenerate_frame_id": regenerate_frame_id})

            # Extract and validate parameters
            parameters = data.get('parameters', {})
            prompt = parameters.get('prompt')
            model_name = parameters.get('model_name')
            num_variants = parameters.get('num_variants', 1)  # Default to 1 variant
            base_seed = parameters.get('seed', None)  # Base seed for variants

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

            # Validate num_variants
            if not isinstance(num_variants, int) or num_variants < 1 or num_variants > 10:
                return PluginResult(
                    success=False,
                    data={},
                    error="Parameter 'num_variants' must be an integer between 1 and 10"
                )

            negative_prompt = data.get('negative_prompt', '')
            width = data.get('width', 1024)
            height = data.get('height', 1024)
            steps = data.get('steps', 32)
            cfg_scale = data.get('cfg_scale', 3.5)
            sampler = data.get('sampler', 'dpmpp_2m_sde')
            scheduler = data.get('scheduler', 'sgm_uniform')
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
                    log.info("sdxl_checkpoint_loaded", {"checkpoint": ckpt_path})
                except Exception as e:
                    return PluginResult(
                        success=False,
                        data={},
                        error=f"Failed to load checkpoint: {str(e)}"
                    )

            # Generate multiple variants
            generated_frames = []
            base_frame_id = None  # Will be set by first variant

            for variant_idx in range(num_variants):
                if self.should_stop:
                    return PluginResult(success=False, data={}, error="Generation stopped")

                # Calculate progress for this variant
                variant_progress_start = 5.0 + (variant_idx / num_variants) * 90.0
                variant_progress_end = 5.0 + ((variant_idx + 1) / num_variants) * 90.0

                # Generate single variant
                variant_result = await self._generate_single_variant(
                    variant_idx=variant_idx,
                    base_seed=base_seed,
                    data=data,
                    base_frame_id=base_frame_id,  # Pass base_frame_id to reuse for variants
                    progress_callback=lambda p: progress_callback(min(100.0, variant_progress_start + p * (variant_progress_end - variant_progress_start) / 100.0)) if progress_callback else None
                )

                if not variant_result['success']:
                    return PluginResult(
                        success=False,
                        data={},
                        error=f"Failed to generate variant {variant_idx + 1}: {variant_result['error']}"
                    )

                # Set base_frame_id from first variant
                if base_frame_id is None:
                    base_frame_id = variant_result['frame_id']

                generated_frames.append(variant_result['frame_id'])
                log.info("sdxl_variant_completed", {
                    "variant_idx": variant_idx + 1,
                    "total_variants": num_variants,
                    "frame_id": variant_result['frame_id'],
                    "base_frame_id": base_frame_id
                })

            # Final progress update
            await self.update_progress(100.0, progress_callback)

            # Return success with all generated frame IDs
            result_data = {
                'generated_frames': generated_frames,
                'num_variants': num_variants,
                'project_id': project_id
            }

            self.is_running = False
            log.info("sdxl_generation_completed", {"generated_frames": generated_frames})
            return PluginResult(
                success=True,
                data=result_data
            )

        except Exception as e:
            self.is_running = False
            log.error("sdxl_generation_error", {"error": str(e)})
            return PluginResult(
                success=False,
                data={},
                error=f"SDXL generation error: {str(e)}"
            )

    async def _generate_single_variant(
        self,
        variant_idx: int,
        base_seed: Optional[int],
        data: Dict[str, Any],
        base_frame_id: Optional[int] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Dict[str, Any]:
        """Generate a single variant of the image"""
        try:
            # Extract parameters from data.parameters
            parameters = data.get('parameters', {})
            prompt = parameters.get('prompt')
            negative_prompt = parameters.get('negative_prompt', '')
            width = parameters.get('width', 1024)
            height = parameters.get('height', 1024)
            steps = parameters.get('steps', 32)
            cfg_scale = parameters.get('cfg_scale', 3.5)
            model_name = parameters.get('model_name')
            sampler = parameters.get('sampler', 'dpmpp_2m_sde')
            scheduler = parameters.get('scheduler', 'sgm_uniform')
            project_id = data.get('project_id', None)  # project_id is at top level
            loras = parameters.get('loras', [])
            regenerate_frame_id = data.get('frame_id', None)
            task_id = data.get('task_id', 0)

            # Calculate seed for this variant
            if base_seed is not None:
                current_seed = base_seed + variant_idx
            else:
                import random
                current_seed = random.randint(0, 2**32 - 1) + variant_idx

            log.info("sdxl_variant_start", {
                "variant_idx": variant_idx,
                "seed": current_seed,
                "prompt": prompt[:50] + "..." if prompt and len(prompt) > 50 else prompt
            })

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
                            log.warning("sdxl_lora_not_found", {"lora_path": lora_path})
                            continue

                        # Apply LoRA to model and clip
                        self.model, self.clip = comfy_bricks.load_lora(
                            lora_path,
                            self.model,
                            self.clip,
                            strength_model,
                            strength_clip
                        )
                        log.info("sdxl_lora_applied", {
                            "lora_name": lora_name,
                            "strength_model": strength_model,
                            "strength_clip": strength_clip
                        })

                except Exception as e:
                    log.warning("sdxl_lora_error", {"error": str(e)})
                    # Continue generation without LoRA

            if self.should_stop:
                return {'success': False, 'error': 'Generation stopped'}

            # Step 2: Encode prompts (15%)
            await self.update_progress(15.0, progress_callback)
            try:
                positive = comfy_bricks.clip_encode(self.clip, prompt)
                negative = comfy_bricks.clip_encode(self.clip, negative_prompt)
            except Exception as e:
                return {'success': False, 'error': f'Failed to encode prompts: {str(e)}'}

            if self.should_stop:
                return {'success': False, 'error': 'Generation stopped'}

            # Step 3: Generate latent image (20%)
            await self.update_progress(20.0, progress_callback)
            latent = comfy_bricks.generate_latent_image(width, height)

            if self.should_stop:
                return {'success': False, 'error': 'Generation stopped'}

            # Step 4: Create frame record first to get frame_id for naming
            await self.update_progress(15.0, progress_callback)

            # Set up paths for generation
            if not regenerate_frame_id:
                # New generation: create frame record first to get frame_id
                from models.frame import FrameCreate

                if base_frame_id is None:
                    # First variant: create new frame and get frame_id
                    temp_path = f"temp_frame_{project_id}_{variant_idx}.png"

                    frame_create = FrameCreate(
                        path=temp_path,  # Temporary path
                        generator='sdxl',
                        project_id=project_id,
                        variant_id=variant_idx
                    )

                    created_frame = await self.frame_service.create_frame(frame_create)
                    frame_id = created_frame.id
                else:
                    # Subsequent variants: reuse base_frame_id but create new record
                    temp_path = f"temp_frame_{project_id}_{variant_idx}.png"

                    frame_create = FrameCreate(
                        path=temp_path,  # Temporary path
                        generator='sdxl',
                        project_id=project_id,
                        variant_id=variant_idx
                    )

                    created_frame = await self.frame_service.create_frame(frame_create)
                    frame_id = created_frame.id  # This will be different, but we'll use base_frame_id for naming

                # Use base_frame_id for naming (or frame_id if it's the first variant)
                naming_frame_id = base_frame_id if base_frame_id is not None else frame_id
                filename = f"project_{project_id}_frame_{naming_frame_id}_variant_{variant_idx}.png"
                preview_filename = f"project_{project_id}_frame_{naming_frame_id}_variant_{variant_idx}.png"
                frames_dir = Path(Config.FRAMES_DIR)
                frames_dir.mkdir(parents=True, exist_ok=True)

                self.preview_path = str(frames_dir / preview_filename)
                final_path = str(frames_dir / filename)

                # Update frame path with correct path
                from models.frame import FrameUpdate
                await self.frame_service.update_frame(frame_id, FrameUpdate(
                    path=self.preview_path
                ))
            else:
                # Regeneration: use existing frame's path
                existing_frame = await self.frame_service.get_frame_by_id(regenerate_frame_id)
                final_path = existing_frame.path
                self.preview_path = final_path  # Same path for both preview and final
                frame_id = regenerate_frame_id

            # Create initial preview from latent (blank or noise pattern)
            try:
                # Generate initial preview from latent
                from bricks.preview_bricks import PreviewGenerator
                preview_gen = PreviewGenerator(self.model)
                initial_preview = preview_gen.generate_preview(latent["samples"])
                if initial_preview:
                    from bricks.preview_bricks import save_preview_image
                    save_preview_image(initial_preview, self.preview_path)
                    log.info("sdxl_initial_preview_created", {"path": self.preview_path})
                else:
                    # Create blank image if preview generation fails
                    blank_img = Image.new('RGB', (width, height), color=(32, 32, 32))
                    blank_img.save(self.preview_path)
                    log.info("sdxl_blank_preview_created", {"path": self.preview_path})
            except Exception as e:
                log.warning("sdxl_preview_error", {"error": str(e)})
                # Create blank image as fallback
                blank_img = Image.new('RGB', (width, height), color=(32, 32, 32))
                blank_img.save(self.preview_path)

            # Set current frame ID for logging and WebSocket
            self.current_frame_id = frame_id
            log.info("sdxl_frame_created", {
                "frame_id": self.current_frame_id,
                "variant_id": variant_idx
            })

            # Broadcast "generation started" message with preview path
            from handlers.websocket import broadcast_message
            await broadcast_message({
                'type': 'generation_started',
                'data': {
                    'task_id': task_id,
                    'frame_id': self.current_frame_id,
                    'project_id': project_id,
                    'preview_path': self.preview_path,
                    'generator': 'sdxl',
                    'variant_id': variant_idx
                }
            })

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
                        log.debug("sdxl_preview_updated", {
                            "step": step + 1,
                            "total_steps": total_steps,
                            "variant_idx": variant_idx
                        })

                except Exception as e:
                    log.warning("sdxl_preview_update_error", {"error": str(e)})

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
                    sampler,
                    scheduler,
                    seed=current_seed,
                    callback=sampling_callback
                )
            except Exception as e:
                return {'success': False, 'error': f'KSampler failed: {str(e)}'}

            if self.should_stop:
                return {'success': False, 'error': 'Generation stopped'}

            # Step 6: Decode and save image (85% -> 95%)
            await self.update_progress(85.0, progress_callback)
            try:
                # Decode latent to image
                decoded_image = comfy_bricks.vae_decode(self.vae, sample)

                # Convert to PIL Image and save
                from PIL import Image
                import numpy as np

                # Convert tensor to numpy array
                if hasattr(decoded_image, 'cpu'):
                    image_array = decoded_image.cpu().detach().numpy()
                else:
                    image_array = decoded_image.detach().numpy()

                # Convert to PIL Image
                image_array = (image_array * 255).astype(np.uint8)
                if len(image_array.shape) == 4:
                    image_array = image_array[0]  # Remove batch dimension

                # Convert from CHW to HWC format
                if image_array.shape[0] == 3:
                    image_array = np.transpose(image_array, (1, 2, 0))

                pil_image = Image.fromarray(image_array)
                pil_image.save(final_path)
                output_path_str = final_path
                log.info("sdxl_image_saved", {"path": output_path_str, "variant_idx": variant_idx})

                # Update frame path in database
                await self.frame_service.update_frame_path(self.current_frame_id, final_path)

            except Exception as e:
                return {'success': False, 'error': f'Failed to save image: {str(e)}'}

            # Step 7: Save generation parameters (95% -> 100%)
            await self.update_progress(95.0, progress_callback)
            try:
                from bricks.generation_params import save_generation_params
                await save_generation_params(
                    output_path=final_path,
                    plugin_name='sdxl',
                    plugin_version='1.0.0',
                    task_id=task_id,
                    timestamp=None,  # No timestamp needed with new naming
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
                        'loras': loras,
                        'num_variants': data.get('num_variants', 1)
                    },
                    project_id=project_id
                )

            except Exception as e:
                log.warning("sdxl_params_save_error", {"error": str(e)})

            # Step 8: Complete (100%)
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
                    'generator': 'sdxl',
                    'variant_id': variant_idx
                }
            })

            log.info("sdxl_variant_completed", {
                "frame_id": self.current_frame_id,
                "variant_id": variant_idx,
                "seed": used_seed
            })

            return {
                'success': True,
                'frame_id': naming_frame_id if not regenerate_frame_id else frame_id,  # Return naming frame_id for grouping
                'output_path': output_path_str,
                'variant_id': variant_idx,
                'seed': used_seed
            }

        except Exception as e:
            log.error("sdxl_variant_error", {"error": str(e), "variant_idx": variant_idx})
            return {'success': False, 'error': f'Variant generation error: {str(e)}'}

    async def stop(self):
        """Stop SDXL generation"""
        self.should_stop = True
        self.is_running = False
        log.info("sdxl_generation_stopped")

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
                    'description': 'Negative prompt to avoid certain elements',
                    'example': 'blurry, low quality, distorted'
                },
                'width': {
                    'type': 'integer',
                    'required': False,
                    'default': 1024,
                    'min': 64,
                    'max': 2048,
                    'step': 64,
                    'description': 'Image width in pixels'
                },
                'height': {
                    'type': 'integer',
                    'required': False,
                    'default': 1024,
                    'min': 64,
                    'max': 2048,
                    'step': 64,
                    'description': 'Image height in pixels'
                },
                'steps': {
                    'type': 'integer',
                    'required': False,
                    'default': 32,
                    'min': 1,
                    'max': 100,
                    'description': 'Number of inference steps'
                },
                'cfg_scale': {
                    'type': 'float',
                    'required': False,
                    'default': 3.5,
                    'min': 1.0,
                    'max': 20.0,
                    'step': 0.1,
                    'description': 'CFG scale for prompt adherence'
                },
                'sampler': {
                    'type': 'select',
                    'required': False,
                    'default': 'dpmpp_2m_sde',
                    'options': [
                        'dpmpp_2m_sde',
                        'dpmpp_2m',
                        'euler',
                        'euler_ancestral',
                        'dpm_2',
                        'dpm_2_ancestral',
                        'lms',
                        'ddim'
                    ],
                    'description': 'Sampling method'
                },
                'scheduler': {
                    'type': 'select',
                    'required': False,
                    'default': 'sgm_uniform',
                    'options': [
                        'sgm_uniform',
                        'karras',
                        'exponential',
                        'polyexponential'
                    ],
                    'description': 'Scheduler type'
                },
                'seed': {
                    'type': 'integer',
                    'required': False,
                    'description': 'Random seed (leave empty for random)',
                    'example': 12345
                },
                'loras': {
                    'type': 'array',
                    'required': False,
                    'description': 'List of LoRA configurations',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'lora_name': {
                                'type': 'string',
                                'description': 'LoRA filename (must be in models_storage/Lora/ folder)'
                            },
                            'strength_model': {
                                'type': 'float',
                                'default': 1.0,
                                'min': 0.0,
                                'max': 2.0,
                                'description': 'LoRA strength for model'
                            },
                            'strength_clip': {
                                'type': 'float',
                                'default': 1.0,
                                'min': 0.0,
                                'max': 2.0,
                                'description': 'LoRA strength for CLIP'
                            }
                        }
                    }
                },
                'num_variants': {
                    'type': 'integer',
                    'required': False,
                    'default': 1,
                    'min': 1,
                    'max': 10,
                    'description': 'Number of variants to generate'
                }
            }
        }

    async def update_progress(self, progress: float, callback: Optional[Callable[[float], None]]):
        """Update progress and call callback if provided"""
        # Ensure progress is within 0-100 range
        self.progress = max(0.0, min(100.0, progress))
        if callback:
            try:
                await callback(self.progress)
            except Exception as e:
                log.warning("sdxl_progress_callback_error", {"error": str(e)})


class SDXLPlugin(BasePlugin):
    """
    SDXL plugin for image generation
    """

    def __init__(self):
        super().__init__()
        self.loader = SDXLLoader()

    async def generate(
        self,
        task_id: int,
        data: Dict[str, Any],
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> PluginResult:
        """Generate image using SDXL"""
        return await self.loader.generate(task_id, data, progress_callback)

    async def stop(self):
        """Stop the generation process"""
        if hasattr(self.loader, 'should_stop'):
            self.loader.should_stop = True
        self.should_stop = True

    @classmethod
    def get_plugin_info(cls) -> Dict[str, Any]:
        """Get plugin information"""
        loader = SDXLLoader()
        return loader.get_plugin_info()
