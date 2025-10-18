import random
import sys
from pathlib import Path

import torch

# Add ComfyUI to Python path so internal imports work
comfyui_path = Path(__file__).parent.parent / "ComfyUI"
if str(comfyui_path) not in sys.path:
    sys.path.insert(0, str(comfyui_path))

# Imports from ComfyUI (via sys.path, linter may show warnings - ignore them)
from comfy.sample import fix_empty_latent_channels  # type: ignore
from comfy.sample import prepare_noise  # type: ignore
from comfy.sample import sample  # type: ignore
from comfy.sd import load_checkpoint_guess_config  # type: ignore
from comfy.sd import load_lora_for_models  # type: ignore
from comfy.utils import load_torch_file  # type: ignore
import comfy.model_sampling  # type: ignore


def load_checkpoint_plugin(ckpt_path):
    out = load_checkpoint_guess_config(ckpt_path, output_vae=True, output_clip=True, output_clipvision=True)
    return out


def clip_encode(clip, text):
    if clip is None:
        raise RuntimeError(
            "ERROR: clip input is invalid: None\n\nIf the clip is from a checkpoint loader node your checkpoint does not contain a valid clip or text encoder model.")
    tokens = clip.tokenize(text)
    return clip.encode_from_tokens_scheduled(tokens)


def generate_latent_image(width, height):
    latent = torch.zeros([1, 4, height // 8, width // 8])
    return {"samples": latent}


def common_ksampler(model, latent, positive, negative, steps, cfg, sampler_name='dpmpp_2m_sde', scheduler='sgm_uniform',
                    denoise=1.0, disable_noise=False, start_step=None, last_step=None, force_full_denoise=False, seed=None, callback=None):
    """
    Common KSampler wrapper

    Args:
        model: Model from checkpoint
        latent: Latent image dict
        positive: Positive conditioning
        negative: Negative conditioning
        steps: Number of sampling steps
        cfg: CFG scale
        sampler_name: Sampler algorithm name
        scheduler: Scheduler name
        denoise: Denoise strength (0.0-1.0)
        disable_noise: If True, use zeros instead of noise
        start_step: Starting step (optional)
        last_step: Last step (optional)
        force_full_denoise: Force full denoising
        seed: Random seed (auto-generated if None)
        callback: Optional callback function(step, x0, x, total_steps) called during sampling

    Returns:
        tuple: (output_latent_dict, used_seed)
    """
    # Generate random seed if not provided
    if seed is None:
        seed = random.randint(1, 1000000000)

    latent_image = latent["samples"]
    latent_image = fix_empty_latent_channels(model, latent_image)

    if disable_noise:
        noise = torch.zeros(latent_image.size(), dtype=latent_image.dtype, layout=latent_image.layout, device="cpu")
    else:
        batch_inds = latent["batch_index"] if "batch_index" in latent else None
        noise = prepare_noise(latent_image, seed, batch_inds)

    noise_mask = None
    if "noise_mask" in latent:
        noise_mask = latent["noise_mask"]

    disable_pbar = False

    samples = sample(model, noise, steps, cfg, sampler_name, scheduler, positive, negative, latent_image,
                     denoise=denoise, disable_noise=disable_noise, start_step=start_step, last_step=last_step,
                     force_full_denoise=force_full_denoise, noise_mask=noise_mask, callback=callback,
                     disable_pbar=disable_pbar, seed=seed)
    out = latent.copy()
    out["samples"] = samples
    # Return both output and the seed that was used
    return out, seed


def vae_decode(vae, samples):
    images = vae.decode(samples["samples"])
    if len(images.shape) == 5: #Combine batches
        images = images.reshape(-1, images.shape[-3], images.shape[-2], images.shape[-1])
    return images


def model_sampling_sd3(model, shift=8):
    """
    Apply SD3 model sampling with shift parameter

    Args:
        model: Loaded model
        shift: Shift parameter for SD3 sampling (default: 8)

    Returns:
        model: Model with SD3 sampling applied
    """
    try:
        # Clone model to avoid modifying original
        m = model.clone()

        # Create SD3 sampling class
        class ModelSamplingSD3(comfy.model_sampling.ModelSamplingDiscrete, comfy.model_sampling.V_PREDICTION):
            def __init__(self, model_config, shift=8):
                super().__init__(model_config)
                self.shift = shift

            def _register_schedule(self, given_betas=None, beta_schedule="linear", timesteps=1000,
                                  linear_start=1e-4, linear_end=2e-2, cosine_s=8e-3, zsnr=False):
                super()._register_schedule(given_betas, beta_schedule, timesteps, linear_start, linear_end, cosine_s, zsnr)
                # Apply shift to timesteps
                self.timesteps = torch.arange(timesteps + self.shift, dtype=torch.float32)

        # Apply SD3 sampling to model
        m.add_object_patch("model_sampling", ModelSamplingSD3(model.model.model_config, shift=shift))
        return m

    except Exception as e:
        print(f"Error applying SD3 sampling: {e}")
        return model


def load_lora(lora_path, model, clip, strength_model=1.0, strength_clip=1.0):
    """
    Load and apply LoRA to model and CLIP

    Args:
        lora_path: Path to LoRA .safetensors file
        model: Model from checkpoint loader
        clip: CLIP from checkpoint loader
        strength_model: LoRA strength for model (0.0-1.0, default 1.0)
        strength_clip: LoRA strength for CLIP (0.0-1.0, default 1.0)

    Returns:
        Tuple of (modified_model, modified_clip)
    """
    # Load LoRA from file
    lora_data = load_torch_file(lora_path, safe_load=False)

    # Apply LoRA to model and clip
    modified_model, modified_clip = load_lora_for_models(
        model,
        clip,
        lora_data,
        strength_model,
        strength_clip
    )

    return (modified_model, modified_clip)


def load_lora_model_only(lora_path, model, strength_model=1.0):
    """
    Load and apply LoRA to model only (without CLIP)

    Args:
        lora_path: Path to LoRA .safetensors file
        model: Model from checkpoint loader
        strength_model: LoRA strength for model (0.0-2.0, default 1.0)

    Returns:
        Modified model with LoRA applied
    """
    # Load LoRA from file
    lora_data = load_torch_file(lora_path, safe_load=False)

    # Apply LoRA to model only (pass None for clip)
    modified_model, _ = load_lora_for_models(
        model,
        None,  # No CLIP
        lora_data,
        strength_model,
        0.0  # strength_clip is 0 since we don't have CLIP
    )

    return modified_model
