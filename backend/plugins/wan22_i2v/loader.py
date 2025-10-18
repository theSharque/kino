"""
Wan22-I2V Plugin Loader for Video Generation
"""
import os
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from PIL import Image
import torch
import numpy as np

from config import Config
from database import get_db
from services.frame_service import FrameService
from bricks import wan_bricks
from bricks.preview_bricks import create_preview_callback
from bricks import comfy_bricks  # Import for KSampler and VAE decode
from bricks import gguf_bricks  # Import for GGUF model loading
from logger import setup_logging
from ..base_plugin import BasePlugin

# Wan22-I2V Model Constants
WAN22_HIGH_NOISE_MODEL = "wan2.2_i2v_high_noise_14B_Q6_K.gguf"
WAN22_LOW_NOISE_MODEL = "wan2.2_i2v_low_noise_14B_Q6_K.gguf"

# Additional Model Constants
VAE_WAN_2_1_MODEL = "wan_2.1.safetensors"  # VAE model
TEXT_ENCODER_MODEL = "umt5-xxl-encoder-Q6_K.gguf"  # Text encoder model

# SysLora Constants
SYS_LORA_WAN_2_1_FUSION_X = "Wan2.1_I2V_14B_FusionX_LoRA.safetensors"
SYS_LORA_WAN_2_2_LIGHTNING_I2V_HIGH = "Wan2.2-Lightning_I2V-A14B-4steps-lora_HIGH_fp16.safetensors"
SYS_LORA_WAN_2_2_LIGHTNING_I2V_LOW = "Wan2.2-Lightning_I2V-A14B-4steps-lora_LOW_fp16.safetensors"
SYS_LORA_WAN_2_2_LIGHTNING_T2V_HIGH = "Wan2.2-Lightning_T2V-A14B-4steps-lora_HIGH_fp16.safetensors"
SYS_LORA_WAN_2_2_LIGHTNING_T2V_LOW = "Wan2.2-Lightning_T2V-A14B-4steps-lora_LOW_fp16.safetensors"

# Initialize logger
log = setup_logging()


class PluginResult:
    """Result of plugin execution"""
    def __init__(self, success: bool, data: Dict[str, Any], error: str = ""):
        self.success = success
        self.data = data
        self.error = error


class Wan22I2VLoader:
    """Wan22-I2V Plugin Loader for Video Generation"""

    def __init__(self):
        self.model = None
        self.loaded_model = None
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
        Generate video using Wan22-I2V

        Expected data parameters:
        - prompt: str (required) - Text prompt for video generation
        - negative_prompt: str (optional) - Negative prompt
        - width: int (optional, default: 512) - Video width
        - height: int (optional, default: 512) - Video height
        - num_frames: int (optional, default: 81) - Number of frames (must be 1 + X * 4)
        - seed: int (optional, default: None) - Random seed (None = auto-generate)
        - high_loras: list (optional) - List of LoRA configurations for HIGH model with lora_name, strength_model
        - low_loras: list (optional) - List of LoRA configurations for LOW model with lora_name, strength_model
        - project_id: int (optional) - Project ID (automatically added by frontend)
        - num_variants: int (optional, default: 1) - Number of variants to generate
        """
        try:
            self.is_running = True
            self.should_stop = False
            self.progress = 0.0

            # Check if this is a regeneration request
            regenerate_frame_id = data.get('frame_id', None)
            log.info("wan22_i2v_generation_start", {"task_id": task_id, "regenerate_frame_id": regenerate_frame_id})

            # Extract and validate parameters
            parameters = data.get('parameters', {})
            prompt = parameters.get('prompt')
            num_variants = parameters.get('num_variants', 1)  # Default to 1 variant
            base_seed = parameters.get('seed', None)  # Base seed for variants

            # Use default model (can be made configurable later)
            model_name = WAN22_HIGH_NOISE_MODEL

            # Validate required parameters before initializing DB
            if not prompt:
                return PluginResult(
                    success=False,
                    data={},
                    error="Parameter 'prompt' is required"
                )

            # Validate num_variants
            if not isinstance(num_variants, int) or num_variants < 1 or num_variants > 5:
                return PluginResult(
                    success=False,
                    data={},
                    error="Parameter 'num_variants' must be an integer between 1 and 5"
                )

            negative_prompt = parameters.get('negative_prompt', '')
            width = parameters.get('width', 512)
            height = parameters.get('height', 512)
            steps = parameters.get('steps', 20)
            cfg_scale = parameters.get('cfg_scale', 3.5)
            project_id = data.get('project_id', None)

            # Initialize frame service for preview updates using global DB
            self.db = get_db()
            self.frame_service = FrameService(self.db)

            # Check for stop request
            if self.should_stop:
                return PluginResult(success=False, data={}, error="Generation stopped")

            # Step 1: Load Wan22-I2V model (10%)
            await self.update_progress(10.0, progress_callback)
            model_path = os.path.join(Config.MODELS_DIR, "DiffusionModels", model_name)

            if not os.path.exists(model_path):
                return PluginResult(
                    success=False,
                    data={},
                    error=f"Model not found: {model_path}"
                )

            # Load model (only if not already loaded or different model)
            if self.loaded_model != model_path:
                try:
                    self.model = wan_bricks.load_wan22_i2v_model(model_path)
                    self.loaded_model = model_path
                    log.info("wan22_i2v_model_loaded", {"model": model_path})
                except Exception as e:
                    return PluginResult(
                        success=False,
                        data={},
                        error=f"Failed to load model: {str(e)}"
                    )

            # Generate multiple variants
            generated_frames = []
            base_frame_id = None  # Will be set by first variant

            for variant_idx in range(num_variants):
                if self.should_stop:
                    return PluginResult(success=False, data={}, error="Generation stopped")

                # Calculate progress for this variant
                variant_progress_start = 10.0 + (variant_idx / num_variants) * 85.0
                variant_progress_end = 10.0 + ((variant_idx + 1) / num_variants) * 85.0

                # Generate single variant
                variant_result = await self._generate_single_variant(
                    variant_idx=variant_idx,
                    base_seed=base_seed,
                    data=data,
                    base_frame_id=base_frame_id,
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
                log.info("wan22_i2v_variant_completed", {
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
            log.info("wan22_i2v_generation_completed", {"generated_frames": generated_frames})
            return PluginResult(
                success=True,
                data=result_data
            )

        except Exception as e:
            self.is_running = False
            log.error("wan22_i2v_generation_error", {"error": str(e)})
            return PluginResult(
                success=False,
                data={},
                error=f"Wan22-I2V generation error: {str(e)}"
            )

    async def _generate_single_variant(
        self,
        variant_idx: int,
        base_seed: Optional[int],
        data: Dict[str, Any],
        base_frame_id: Optional[int] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Dict[str, Any]:
        """Generate a single variant of the video"""
        try:
            # Extract parameters from data.parameters
            parameters = data.get('parameters', {})
            prompt = parameters.get('prompt')
            negative_prompt = parameters.get('negative_prompt', 'vivid colors, overexposed, static, blurry details, subtitles, style, artwork, painting, picture, still, overall gray, worst quality, low quality, JPEG artifacts, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn face, deformed, disfigured, malformed limbs, fused fingers, static frame, cluttered background, three legs, walking backwards, slow motion, slowmo')
            width = parameters.get('width', 512)
            height = parameters.get('height', 512)
            num_frames = parameters.get('num_frames', 81)

            # Validate num_frames: must be 1 + X * 4
            if (num_frames - 1) % 4 != 0:
                log.warning("wan22_i2v_invalid_num_frames", {
                    "num_frames": num_frames,
                    "corrected_to": 81
                })
                num_frames = 81  # Default to 81 if invalid

            # Constants for KSampler (not user-configurable)
            steps = 4  # Always 4 steps for Wan22-I2V
            cfg_scale = 1.0  # Always 1.0 for Wan22-I2V

            model_name = WAN22_HIGH_NOISE_MODEL  # Use constant instead of parameter
            project_id = data.get('project_id', None)
            regenerate_frame_id = data.get('frame_id', None)
            task_id = data.get('task_id', 0)
            high_loras = parameters.get('high_loras', [])  # LoRAs for HIGH noise model
            low_loras = parameters.get('low_loras', [])  # LoRAs for LOW noise model

            # Calculate seed for this variant
            if base_seed is not None:
                current_seed = base_seed + variant_idx
            else:
                import random
                current_seed = random.randint(0, 2**32 - 1) + variant_idx

            log.info("wan22_i2v_variant_start", {
                "variant_idx": variant_idx,
                "seed": current_seed,
                "prompt": prompt[:50] + "..." if prompt and len(prompt) > 50 else prompt
            })

            if self.should_stop:
                return {'success': False, 'error': 'Generation stopped'}

            # Step 2: Create frame record first to get frame_id for naming (20%)
            await self.update_progress(20.0, progress_callback)

            # Set up paths for generation
            if not regenerate_frame_id:
                # New generation: create frame record first to get frame_id
                from models.frame import FrameCreate

                if base_frame_id is None:
                    # First variant: create new frame and get frame_id
                    temp_path = f"temp_frame_{project_id}_{variant_idx}.mp4"

                    frame_create = FrameCreate(
                        path=temp_path,  # Temporary path
                        generator='wan22_i2v',
                        project_id=project_id,
                        variant_id=variant_idx
                    )

                    created_frame = await self.frame_service.create_frame(frame_create)
                    frame_id = created_frame.id
                else:
                    # Subsequent variants: reuse base_frame_id but create new record
                    temp_path = f"temp_frame_{project_id}_{variant_idx}.mp4"

                    frame_create = FrameCreate(
                        path=temp_path,  # Temporary path
                        generator='wan22_i2v',
                        project_id=project_id,
                        variant_id=variant_idx
                    )

                    created_frame = await self.frame_service.create_frame(frame_create)
                    frame_id = created_frame.id

                # Use base_frame_id for naming (or frame_id if it's the first variant)
                naming_frame_id = base_frame_id if base_frame_id is not None else frame_id
                # Preview will be the first frame of the sequence (seq_000.png)
                preview_filename = f"project_{project_id}_frame_{naming_frame_id}_variant_{variant_idx}_seq_000.png"
                frames_dir = Path(Config.FRAMES_DIR)
                frames_dir.mkdir(parents=True, exist_ok=True)

                self.preview_path = str(frames_dir / preview_filename)

                # Update frame path with correct path
                from models.frame import FrameUpdate
                await self.frame_service.update_frame(frame_id, FrameUpdate(
                    path=self.preview_path
                ))
            else:
                # Regeneration: use existing frame's path (should be seq_000.png)
                existing_frame = await self.frame_service.get_frame_by_id(regenerate_frame_id)
                self.preview_path = existing_frame.path
                frame_id = regenerate_frame_id
                naming_frame_id = frame_id

            # Create initial preview (blank image)
            try:
                blank_img = Image.new('RGB', (width, height), color=(32, 32, 32))
                blank_img.save(self.preview_path)
                log.info("wan22_i2v_blank_preview_created", {"path": self.preview_path})
            except Exception as e:
                log.warning("wan22_i2v_preview_error", {"error": str(e)})

            # Set current frame ID for logging and WebSocket
            self.current_frame_id = frame_id
            log.info("wan22_i2v_frame_created", {
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
                    'generator': 'wan22_i2v',
                    'variant_id': variant_idx
                }
            })

            # Step 3: Wan22-I2V Video Generation Pipeline (30% -> 90%)
            await self.update_progress(30.0, progress_callback)

            try:
                # 1. Load CLIP Vision
                await self.update_progress(35.0, progress_callback)
                clip_vision_name = "clip_vision_h.safetensors"
                clip_vision = wan_bricks.load_clip_vision(clip_vision_name)
                log.info("wan22_i2v_clip_vision_loaded", {"clip_vision_name": clip_vision_name})

                # 2. Get previous frame and encode with CLIP Vision
                await self.update_progress(40.0, progress_callback)
                previous_frame = None
                clip_vision_output = None
                start_image = None

                if project_id:
                    project_frames = await self.frame_service.get_frames_by_project_id(project_id)
                    if project_frames:
                        sorted_frames = sorted(project_frames, key=lambda f: f.id)
                        previous_frame = sorted_frames[-1]

                        # Load previous frame image
                        if previous_frame.path and os.path.exists(previous_frame.path):
                            start_image = Image.open(previous_frame.path)
                            # Convert PIL Image to ComfyUI format (tensor)
                            start_image_array = np.array(start_image).astype(np.float32) / 255.0
                            start_image_tensor = torch.from_numpy(start_image_array).unsqueeze(0)  # Add batch dimension

                            # Encode with CLIP Vision
                            clip_vision_output = wan_bricks.clip_vision_encode(clip_vision, start_image_tensor)
                            log.info("wan22_i2v_previous_frame_encoded", {
                                "frame_id": previous_frame.id,
                                "frame_path": previous_frame.path
                            })
                        else:
                            log.warning("wan22_i2v_previous_frame_not_found", {"path": previous_frame.path})
                    else:
                        log.warning("wan22_i2v_no_previous_frame", {"project_id": project_id})

                # 3. Load VAE wan_2.1
                await self.update_progress(45.0, progress_callback)
                vae = wan_bricks.load_vae(VAE_WAN_2_1_MODEL)
                log.info("wan22_i2v_vae_loaded", {"vae_name": VAE_WAN_2_1_MODEL})

                # 4. Load Text Encoder (GGUF)
                await self.update_progress(50.0, progress_callback)
                text_encoder = wan_bricks.load_clip(TEXT_ENCODER_MODEL, clip_type="wan")
                log.info("wan22_i2v_text_encoder_loaded", {"text_encoder_name": TEXT_ENCODER_MODEL})

                # 5. Text Encoding for Positive and Negative
                await self.update_progress(55.0, progress_callback)
                positive = comfy_bricks.clip_encode(text_encoder, prompt)
                negative = comfy_bricks.clip_encode(text_encoder, negative_prompt)
                log.info("wan22_i2v_text_encoded", {
                    "prompt": prompt[:50] + "..." if len(prompt) > 50 else prompt,
                    "negative_prompt": negative_prompt[:50] + "..." if len(negative_prompt) > 50 else negative_prompt
                })

                # 6. WanImageToVideo
                await self.update_progress(60.0, progress_callback)
                positive, negative, latent_video = wan_bricks.wan_image_to_video(
                    positive=positive,
                    negative=negative,
                    vae=vae,
                    width=width,
                    height=height,
                    length=num_frames,  # User-configurable number of frames
                    batch_size=1,
                    clip_vision_output=clip_vision_output,
                    start_image=start_image_tensor if start_image is not None else None
                )
                log.info("wan22_i2v_latent_video_created", {
                    "width": width,
                    "height": height,
                    "length": num_frames
                })

                # 7. Load HIGH model and First KSampler (Advanced)
                await self.update_progress(70.0, progress_callback)

                # Load HIGH model just before using it (saves memory)
                high_model = gguf_bricks.load_unet_gguf(WAN22_HIGH_NOISE_MODEL)
                log.info("wan22_i2v_high_model_loaded", {"model": WAN22_HIGH_NOISE_MODEL})

                # Apply ModelSamplingSD3 with shift = 8 for HIGH model
                high_model = comfy_bricks.model_sampling_sd3(high_model, shift=8)
                log.info("wan22_i2v_high_model_sampling_applied", {"shift": 8})

                # Load and apply LoRA for HIGH model
                # Apply FusionX LoRA
                fusion_x_path = os.path.join(Config.MODELS_DIR, "SysLora", SYS_LORA_WAN_2_1_FUSION_X)
                if os.path.exists(fusion_x_path):
                    high_model = comfy_bricks.load_lora_model_only(
                        fusion_x_path,
                        high_model,
                        strength_model=1.0
                    )
                    log.info("wan22_i2v_high_fusionx_lora_applied", {"lora": SYS_LORA_WAN_2_1_FUSION_X})
                else:
                    log.warning("wan22_i2v_high_fusionx_lora_not_found", {"path": fusion_x_path})

                # Apply Lightning I2V HIGH LoRA
                lightning_high_path = os.path.join(Config.MODELS_DIR, "SysLora", SYS_LORA_WAN_2_2_LIGHTNING_I2V_HIGH)
                if os.path.exists(lightning_high_path):
                    high_model = comfy_bricks.load_lora_model_only(
                        lightning_high_path,
                        high_model,
                        strength_model=1.0
                    )
                    log.info("wan22_i2v_high_lightning_lora_applied", {"lora": SYS_LORA_WAN_2_2_LIGHTNING_I2V_HIGH})
                else:
                    log.warning("wan22_i2v_high_lightning_lora_not_found", {"path": lightning_high_path})

                # Apply user-specified HIGH LoRAs
                if high_loras and len(high_loras) > 0:
                    for lora_config in high_loras:
                        lora_name = lora_config.get('lora_name')
                        if not lora_name:
                            continue

                        strength_model = lora_config.get('strength_model', 1.0)
                        lora_path = os.path.join(Config.MODELS_DIR, "Lora", lora_name)

                        if not os.path.exists(lora_path):
                            log.warning("wan22_i2v_high_user_lora_not_found", {"lora_path": lora_path})
                            continue

                        high_model = comfy_bricks.load_lora_model_only(
                            lora_path,
                            high_model,
                            strength_model=strength_model
                        )
                        log.info("wan22_i2v_high_user_lora_applied", {
                            "lora_name": lora_name,
                            "strength_model": strength_model
                        })

                await self.update_progress(75.0, progress_callback)
                high_latent_video, _ = comfy_bricks.common_ksampler(
                    model=high_model,  # Use loaded HIGH GGUF model
                    latent=latent_video,
                    positive=positive,
                    negative=negative,
                    steps=4,
                    cfg=1.0,
                    sampler_name='dpmpp_2m_sde',
                    scheduler='sgm_uniform',
                    seed=current_seed,
                    start_step=0,
                    last_step=2,
                    disable_noise=False
                )
                log.info("wan22_i2v_high_sampling_completed")

                # 8. Load LOW model and Second KSampler (Advanced)
                await self.update_progress(80.0, progress_callback)

                # Load LOW model just before using it (saves memory)
                low_model = gguf_bricks.load_unet_gguf(WAN22_LOW_NOISE_MODEL)
                log.info("wan22_i2v_low_model_loaded", {"model": WAN22_LOW_NOISE_MODEL})

                # Apply ModelSamplingSD3 with shift = 8 for LOW model
                low_model = comfy_bricks.model_sampling_sd3(low_model, shift=8)
                log.info("wan22_i2v_low_model_sampling_applied", {"shift": 8})

                # Load and apply LoRA for LOW model
                # Apply FusionX LoRA
                fusion_x_path = os.path.join(Config.MODELS_DIR, "SysLora", SYS_LORA_WAN_2_1_FUSION_X)
                if os.path.exists(fusion_x_path):
                    low_model = comfy_bricks.load_lora_model_only(
                        fusion_x_path,
                        low_model,
                        strength_model=1.0
                    )
                    log.info("wan22_i2v_low_fusionx_lora_applied", {"lora": SYS_LORA_WAN_2_1_FUSION_X})
                else:
                    log.warning("wan22_i2v_low_fusionx_lora_not_found", {"path": fusion_x_path})

                # Apply Lightning I2V LOW LoRA
                lightning_low_path = os.path.join(Config.MODELS_DIR, "SysLora", SYS_LORA_WAN_2_2_LIGHTNING_I2V_LOW)
                if os.path.exists(lightning_low_path):
                    low_model = comfy_bricks.load_lora_model_only(
                        lightning_low_path,
                        low_model,
                        strength_model=1.0
                    )
                    log.info("wan22_i2v_low_lightning_lora_applied", {"lora": SYS_LORA_WAN_2_2_LIGHTNING_I2V_LOW})
                else:
                    log.warning("wan22_i2v_low_lightning_lora_not_found", {"path": lightning_low_path})

                # Apply user-specified LOW LoRAs
                if low_loras and len(low_loras) > 0:
                    for lora_config in low_loras:
                        lora_name = lora_config.get('lora_name')
                        if not lora_name:
                            continue

                        strength_model = lora_config.get('strength_model', 1.0)
                        lora_path = os.path.join(Config.MODELS_DIR, "Lora", lora_name)

                        if not os.path.exists(lora_path):
                            log.warning("wan22_i2v_low_user_lora_not_found", {"lora_path": lora_path})
                            continue

                        low_model = comfy_bricks.load_lora_model_only(
                            lora_path,
                            low_model,
                            strength_model=strength_model
                        )
                        log.info("wan22_i2v_low_user_lora_applied", {
                            "lora_name": lora_name,
                            "strength_model": strength_model
                        })

                await self.update_progress(85.0, progress_callback)
                low_latent_video, _ = comfy_bricks.common_ksampler(
                    model=low_model,  # Use loaded LOW GGUF model
                    latent=high_latent_video,
                    positive=positive,
                    negative=negative,
                    steps=4,
                    cfg=1.0,
                    sampler_name='dpmpp_2m_sde',
                    scheduler='sgm_uniform',
                    seed=current_seed,
                    start_step=2,
                    last_step=10000,
                    disable_noise=True
                )
                log.info("wan22_i2v_low_sampling_completed")

                # 9. VAE Decode
                await self.update_progress(90.0, progress_callback)
                images = comfy_bricks.vae_decode(vae, low_latent_video)
                log.info("wan22_i2v_vae_decode_completed", {"frames_count": len(images)})

                # Save video frames as sequence
                await self.update_progress(92.0, progress_callback)

                # Convert images batch to list of PIL Images
                saved_paths = []
                frames_dir = Path(Config.FRAMES_DIR)
                frames_dir.mkdir(parents=True, exist_ok=True)

                # Use naming_frame_id for consistency with variants
                naming_frame_id = base_frame_id if base_frame_id is not None else frame_id

                for seq_idx, image in enumerate(images):
                    try:
                        # Convert tensor to numpy array
                        if hasattr(image, 'cpu'):
                            image_array = image.cpu().detach().numpy()
                        else:
                            image_array = image.detach().numpy()

                        # Convert to PIL Image
                        image_array = (image_array * 255).astype(np.uint8)

                        # Remove batch dimension if present
                        if len(image_array.shape) == 4:
                            image_array = image_array[0]

                        # Convert from CHW to HWC format if needed
                        if image_array.shape[0] == 3:
                            image_array = np.transpose(image_array, (1, 2, 0))

                        pil_image = Image.fromarray(image_array)

                        # Save with sequence number: project_ID_frame_ID_variant_ID_seq_###.png
                        seq_filename = f"project_{project_id}_frame_{naming_frame_id}_variant_{variant_idx}_seq_{seq_idx:03d}.png"
                        seq_path = str(frames_dir / seq_filename)
                        pil_image.save(seq_path)
                        saved_paths.append(seq_path)

                        log.debug("wan22_i2v_frame_saved", {
                            "seq_idx": seq_idx,
                            "path": seq_path
                        })

                    except Exception as e:
                        log.error("wan22_i2v_frame_save_error", {
                            "seq_idx": seq_idx,
                            "error": str(e)
                        })
                        continue

                # Update progress after saving all frames
                await self.update_progress(95.0, progress_callback)

                # Save the first frame as the main preview/thumbnail
                if saved_paths:
                    output_path_str = saved_paths[0]  # First frame as main output
                    await self.frame_service.update_frame_path(self.current_frame_id, output_path_str)
                    log.info("wan22_i2v_sequence_saved", {
                        "total_frames": len(saved_paths),
                        "first_frame": output_path_str,
                        "variant_idx": variant_idx
                    })
                else:
                    log.error("wan22_i2v_no_frames_saved", {"variant_idx": variant_idx})
                    return {'success': False, 'error': 'No frames were saved'}

            except Exception as e:
                return {'success': False, 'error': f'Failed to generate video: {str(e)}'}

            # Step 4: Save generation parameters (95% -> 98%)
            await self.update_progress(96.0, progress_callback)
            try:
                from bricks.generation_params import save_generation_params
                await save_generation_params(
                    output_path=output_path_str,  # Save params with first frame path
                    plugin_name='wan22_i2v',
                    plugin_version='1.0.0',
                    task_id=task_id,
                    timestamp=None,
                    parameters={
                        'prompt': prompt,
                        'negative_prompt': negative_prompt,
                        'width': width,
                        'height': height,
                        'num_frames': num_frames,
                        'seed': current_seed,
                        'model_name': model_name,  # Keep for reference but not user-configurable
                        'num_variants': data.get('num_variants', 1),
                        'total_frames': len(saved_paths),  # Actual number of saved frames
                        'steps': steps,  # Constant, for reference
                        'high_loras': high_loras,  # User-specified LoRAs for HIGH model
                        'low_loras': low_loras  # User-specified LoRAs for LOW model
                    },
                    project_id=project_id
                )

            except Exception as e:
                log.warning("wan22_i2v_params_save_error", {"error": str(e)})

            # Step 5: Complete (100%)
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
                    'generator': 'wan22_i2v',
                    'variant_id': variant_idx
                }
            })

            log.info("wan22_i2v_variant_completed", {
                "frame_id": self.current_frame_id,
                "variant_id": variant_idx,
                "seed": current_seed
            })

            return {
                'success': True,
                'frame_id': naming_frame_id if not regenerate_frame_id else frame_id,
                'output_path': output_path_str,
                'variant_id': variant_idx,
                'seed': current_seed
            }

        except Exception as e:
            log.error("wan22_i2v_variant_error", {"error": str(e), "variant_idx": variant_idx})
            return {'success': False, 'error': f'Variant generation error: {str(e)}'}

    async def stop(self):
        """Stop Wan22-I2V generation"""
        self.should_stop = True
        self.is_running = False
        log.info("wan22_i2v_generation_stopped")

    @classmethod
    def get_plugin_info(cls) -> Dict[str, Any]:
        """Get Wan22-I2V plugin information"""
        return {
            'name': 'wan22_i2v',
            'version': '1.0.0',
            'description': 'Wan22-I2V video generator for image-to-video generation',
            'author': 'Kino Team',
            'visible': True,  # Show in UI
            'model_type': 'video_diffusion',
            'parameters': {
                'prompt': {
                    'type': 'string',
                    'required': True,
                    'description': 'Text prompt for video generation',
                    'example': 'A cat walking in a garden'
                },
                'negative_prompt': {
                    'type': 'string',
                    'required': False,
                    'default': 'vivid colors, overexposed, static, blurry details, subtitles, style, artwork, painting, picture, still, overall gray, worst quality, low quality, JPEG artifacts, ugly, incomplete, extra fingers, poorly drawn hands, poorly drawn face, deformed, disfigured, malformed limbs, fused fingers, static frame, cluttered background, three legs, walking backwards, slow motion, slowmo',
                    'description': 'Negative prompt to avoid certain elements',
                    'example': 'blurry, low quality, distorted'
                },
                'width': {
                    'type': 'integer',
                    'required': False,
                    'default': 512,
                    'min': 256,
                    'max': 1024,
                    'step': 64,
                    'description': 'Video width in pixels'
                },
                'height': {
                    'type': 'integer',
                    'required': False,
                    'default': 512,
                    'min': 256,
                    'max': 1024,
                    'step': 64,
                    'description': 'Video height in pixels'
                },
                'num_frames': {
                    'type': 'integer',
                    'required': False,
                    'default': 81,
                    'min': 5,
                    'max': 121,
                    'step': 4,
                    'description': 'Number of frames (must be 1 + X * 4, e.g., 5, 9, 13, 17, 21, ..., 81, ..., 121)',
                    'validation': 'value must satisfy: (value - 1) % 4 == 0'
                },
                'seed': {
                    'type': 'integer',
                    'required': False,
                    'description': 'Random seed (leave empty for random)',
                    'example': 12345
                },
                'high_loras': {
                    'type': 'lora_list',
                    'required': False,
                    'description': 'LoRAs applied to HIGH noise model',
                    'item_schema': {
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
                        }
                    }
                },
                'low_loras': {
                    'type': 'lora_list',
                    'required': False,
                    'description': 'LoRAs applied to LOW noise model',
                    'item_schema': {
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
                        }
                    }
                },
                'num_variants': {
                    'type': 'integer',
                    'required': False,
                    'default': 1,
                    'min': 1,
                    'max': 5,
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
                log.warning("wan22_i2v_progress_callback_error", {"error": str(e)})


class Wan22I2VPlugin(BasePlugin):
    """
    Wan22-I2V plugin for video generation
    """

    def __init__(self):
        super().__init__()
        self.loader = Wan22I2VLoader()

    async def generate(
        self,
        task_id: int,
        data: Dict[str, Any],
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> PluginResult:
        """Generate video using Wan22-I2V"""
        return await self.loader.generate(task_id, data, progress_callback)

    async def stop(self):
        """Stop the generation process"""
        if hasattr(self.loader, 'should_stop'):
            self.loader.should_stop = True
        self.should_stop = True

    @classmethod
    def get_plugin_info(cls) -> Dict[str, Any]:
        """Get plugin information"""
        loader = Wan22I2VLoader()
        return loader.get_plugin_info()
