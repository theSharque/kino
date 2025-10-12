import random

import torch

from comfy.sample import fix_empty_latent_channels
from comfy.sample import prepare_noise
from comfy.sample import sample
from comfy.sd import load_checkpoint_guess_config
from comfy.sd import load_lora_for_models
from comfy.utils import load_torch_file


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
                    denoise=1.0, disable_noise=False, start_step=None, last_step=None, force_full_denoise=False):
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

    callback = None
    disable_pbar = False
    samples = sample(model, noise, steps, cfg, sampler_name, scheduler, positive, negative, latent_image,
                     denoise=denoise, disable_noise=disable_noise, start_step=start_step, last_step=last_step,
                     force_full_denoise=force_full_denoise, noise_mask=noise_mask, callback=callback,
                     disable_pbar=disable_pbar, seed=seed)
    out = latent.copy()
    out["samples"] = samples
    return out


def vae_decode(vae, samples):
    images = vae.decode(samples["samples"])
    if len(images.shape) == 5: #Combine batches
        images = images.reshape(-1, images.shape[-3], images.shape[-2], images.shape[-1])
    return images


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
