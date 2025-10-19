"""
WAN (Wan) Bricks - utility functions for Wan video generation workflow

Based on ComfyUI nodes from:
- nodes.py (CLIPVisionLoader, CLIPVisionEncode, VAELoader, CLIPLoader)
- comfy_extras/nodes_wan.py (WanImageToVideo)

These bricks provide building blocks for Wan image-to-video generation.
"""

import sys
from pathlib import Path

import torch

# Add ComfyUI to Python path so internal imports work
comfyui_path = Path(__file__).parent.parent / "ComfyUI"
if str(comfyui_path) not in sys.path:
    sys.path.insert(0, str(comfyui_path))

# Imports from ComfyUI (via sys.path, linter may show warnings - ignore them)
import comfy.clip_vision  # type: ignore
import comfy.model_management  # type: ignore
import comfy.sd  # type: ignore
import comfy.utils  # type: ignore
import folder_paths  # type: ignore
import node_helpers  # type: ignore


def load_clip_vision(clip_name: str):
    """
    Load CLIP Vision model for image encoding.

    Based on: CLIPVisionLoader from nodes.py (lines 985-1000)

    Args:
        clip_name: Name of the CLIP Vision model file from clip_vision folder

    Returns:
        clip_vision: Loaded CLIP Vision model

    Raises:
        RuntimeError: If clip vision file is invalid
    """
    clip_path = folder_paths.get_full_path_or_raise("clip_vision", clip_name)
    clip_vision = comfy.clip_vision.load(clip_path)
    if clip_vision is None:
        raise RuntimeError(
            "ERROR: clip vision file is invalid and does not contain a valid vision model."
        )
    return clip_vision


def clip_vision_encode(clip_vision, image, crop="center"):
    """
    Encode image using CLIP Vision model.

    Based on: CLIPVisionEncode from nodes.py (lines 1002-1019)

    Args:
        clip_vision: CLIP Vision model from load_clip_vision()
        image: Input image tensor (IMAGE type from ComfyUI)
        crop: Crop method - "center" or "none" (default: "center")

    Returns:
        output: CLIP Vision output embedding (CLIP_VISION_OUTPUT type)
    """
    crop_image = True
    if crop != "center":
        crop_image = False
    output = clip_vision.encode_image(image, crop=crop_image)
    return output


def load_clip(clip_name: str, clip_type: str = "stable_diffusion"):
    """
    Load CLIP text encoder in GGUF format.

    Based on: CLIPLoader from nodes.py and gguf_bricks.load_clip_gguf

    Args:
        clip_name: Name of the CLIP model file from text_encoders folder
        clip_type: Type of CLIP model (default: "stable_diffusion")

    Returns:
        clip: Loaded CLIP text encoder

    Raises:
        RuntimeError: If CLIP file is invalid or not found
    """
    # Import GGUF bricks for CLIP loading
    from bricks.gguf_bricks import load_clip_gguf

    try:
        clip = load_clip_gguf(clip_name, clip_type)
        return clip
    except Exception as e:
        raise RuntimeError(f"Failed to load CLIP model {clip_name}: {e}")


def load_vae(vae_name: str):
    """
    Load VAE model for encoding/decoding images.

    Based on: VAELoader from nodes.py (lines 694-786)

    Args:
        vae_name: Name of the VAE model file

    Returns:
        vae: Loaded VAE model

    Raises:
        Exception: If VAE is invalid
    """
    if vae_name == "pixel_space":
        sd = {}
        sd["pixel_space_vae"] = torch.tensor(1.0)
    elif vae_name in ["taesd", "taesdxl", "taesd3", "taef1"]:
        # Load TAESD (Tiny AutoEncoder) VAE
        sd = _load_taesd(vae_name)
    else:
        vae_path = folder_paths.get_full_path_or_raise("vae", vae_name)
        sd = comfy.utils.load_torch_file(vae_path)

    vae = comfy.sd.VAE(sd=sd)
    vae.throw_exception_if_invalid()
    return vae


def _load_taesd(name: str):
    """Internal helper to load TAESD VAE models"""
    sd = {}
    approx_vaes = folder_paths.get_filename_list("vae_approx")

    encoder = next(filter(lambda a: a.startswith(f"{name}_encoder."), approx_vaes))
    decoder = next(filter(lambda a: a.startswith(f"{name}_decoder."), approx_vaes))

    enc = comfy.utils.load_torch_file(folder_paths.get_full_path_or_raise("vae_approx", encoder))
    for k in enc:
        sd[f"taesd_encoder.{k}"] = enc[k]

    dec = comfy.utils.load_torch_file(folder_paths.get_full_path_or_raise("vae_approx", decoder))
    for k in dec:
        sd[f"taesd_decoder.{k}"] = dec[k]

    # Set scale and shift parameters based on model type
    if name == "taesd":
        sd["vae_scale"] = torch.tensor(0.18215)
        sd["vae_shift"] = torch.tensor(0.0)
    elif name == "taesdxl":
        sd["vae_scale"] = torch.tensor(0.13025)
        sd["vae_shift"] = torch.tensor(0.0)
    elif name == "taesd3":
        sd["vae_scale"] = torch.tensor(1.5305)
        sd["vae_shift"] = torch.tensor(0.0609)
    elif name == "taef1":
        sd["vae_scale"] = torch.tensor(0.3611)
        sd["vae_shift"] = torch.tensor(0.1159)

    return sd


def load_clip(clip_name: str, clip_type: str = "wan", device: str = "default"):
    """
    Load CLIP text encoder model (supports GGUF format).

    Based on: CLIPLoader from nodes.py (lines 928-953)

    Args:
        clip_name: Name of the CLIP model file from text_encoders folder
        clip_type: Type of CLIP model - one of:
            "stable_diffusion", "stable_cascade", "sd3", "stable_audio", "mochi",
            "ltxv", "pixart", "cosmos", "lumina2", "wan", "hidream", "chroma",
            "ace", "omnigen2", "qwen_image", "hunyuan_image"
            Default: "wan" for Wan video models
        device: Device to load on - "default" or "cpu"

    Returns:
        clip: Loaded CLIP model
    """
    # Get CLIP type enum from string
    clip_type_upper = clip_type.upper()
    clip_type_enum = getattr(
        comfy.sd.CLIPType,
        clip_type_upper,
        comfy.sd.CLIPType.STABLE_DIFFUSION
    )

    model_options = {}
    if device == "cpu":
        model_options["load_device"] = model_options["offload_device"] = torch.device("cpu")

    clip_path = folder_paths.get_full_path_or_raise("text_encoders", clip_name)
    clip = comfy.sd.load_clip(
        ckpt_paths=[clip_path],
        embedding_directory=folder_paths.get_folder_paths("embeddings"),
        clip_type=clip_type_enum,
        model_options=model_options
    )
    return clip


def wan_image_to_video(
    positive,
    negative,
    vae,
    width: int = 832,
    height: int = 480,
    length: int = 81,
    batch_size: int = 1,
    clip_vision_output=None,
    start_image=None
):
    """
    Prepare conditioning and latent for Wan image-to-video generation.

    Based on: WanImageToVideo from comfy_extras/nodes_wan.py (lines 15-60)

    Args:
        positive: Positive conditioning from CLIP text encode
        negative: Negative conditioning from CLIP text encode
        vae: VAE model for encoding images
        width: Video width (default: 832)
        height: Video height (default: 480)
        length: Video length in frames (default: 81)
        batch_size: Batch size (default: 1)
        clip_vision_output: Optional CLIP Vision encoding of reference image
        start_image: Optional starting image for video generation

    Returns:
        Tuple of (positive, negative, latent):
            - positive: Modified positive conditioning with video setup
            - negative: Modified negative conditioning with video setup
            - latent: Empty latent tensor for video generation
    """
    # Create empty latent for video
    # Wan uses 16 channels, temporal dimension is ((length-1)//4)+1
    latent = torch.zeros(
        [batch_size, 16, ((length - 1) // 4) + 1, height // 8, width // 8],
        device=comfy.model_management.intermediate_device()
    )

    # Process start image if provided
    if start_image is not None:
        # Upscale and prepare start image
        start_image = comfy.utils.common_upscale(
            start_image[:length].movedim(-1, 1),
            width,
            height,
            "bilinear",
            "center"
        ).movedim(1, -1)

        # Create full video tensor filled with gray (0.5)
        image = torch.ones(
            (length, height, width, start_image.shape[-1]),
            device=start_image.device,
            dtype=start_image.dtype
        ) * 0.5
        image[:start_image.shape[0]] = start_image

        # Encode to latent
        concat_latent_image = vae.encode(image[:, :, :, :3])

        # Create mask (1 = denoise, 0 = keep)
        mask = torch.ones(
            (1, 1, latent.shape[2], concat_latent_image.shape[-2], concat_latent_image.shape[-1]),
            device=start_image.device,
            dtype=start_image.dtype
        )
        mask[:, :, :((start_image.shape[0] - 1) // 4) + 1] = 0.0

        # Add to conditioning
        positive = node_helpers.conditioning_set_values(
            positive,
            {"concat_latent_image": concat_latent_image, "concat_mask": mask}
        )
        negative = node_helpers.conditioning_set_values(
            negative,
            {"concat_latent_image": concat_latent_image, "concat_mask": mask}
        )

    # Add CLIP vision output if provided
    if clip_vision_output is not None:
        positive = node_helpers.conditioning_set_values(
            positive,
            {"clip_vision_output": clip_vision_output}
        )
        negative = node_helpers.conditioning_set_values(
            negative,
            {"clip_vision_output": clip_vision_output}
        )

    # Prepare output latent
    out_latent = {"samples": latent}

    return positive, negative, out_latent

