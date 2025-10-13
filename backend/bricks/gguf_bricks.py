"""
GGUF Bricks - utility functions for loading quantized models in GGUF format

Based on ComfyUI-GGUF custom node:
- https://github.com/city96/ComfyUI-GGUF

These bricks provide functions for loading GGUF quantized models:
1. Diffusion models (UNET) - Flux, Wan, SD3, SDXL, etc.
2. CLIP text encoders - T5, LLaMA, etc.
3. VAE (optional, rarely used in GGUF format)

GGUF (GPT-Generated Unified Format) allows for quantized models that:
- Use less VRAM (4-8x smaller than float16)
- Load faster from disk
- Still maintain good quality
"""

import sys
from pathlib import Path

import torch
import logging

# Add ComfyUI to Python path so internal imports work
comfyui_path = Path(__file__).parent.parent / "ComfyUI"
if str(comfyui_path) not in sys.path:
    sys.path.insert(0, str(comfyui_path))

# Add ComfyUI-GGUF custom node to path
gguf_path = comfyui_path / "custom_nodes" / "ComfyUI-GGUF"
if str(gguf_path) not in sys.path:
    sys.path.insert(0, str(gguf_path))

# Imports from ComfyUI
import comfy.sd  # type: ignore
import comfy.model_management  # type: ignore
import folder_paths  # type: ignore

# Imports from ComfyUI-GGUF
try:
    from ops import GGMLOps, GGMLTensor  # type: ignore
    from loader import gguf_sd_loader, gguf_clip_loader  # type: ignore
    GGUF_AVAILABLE = True
except ImportError:
    GGUF_AVAILABLE = False
    logging.warning("ComfyUI-GGUF not available. GGUF loading will not work.")


def check_gguf_available():
    """Check if GGUF support is available"""
    if not GGUF_AVAILABLE:
        raise RuntimeError(
            "ComfyUI-GGUF is not available. "
            "Please install it: https://github.com/city96/ComfyUI-GGUF"
        )


def load_unet_gguf(
    unet_name: str,
    dequant_dtype: str = "default",
    patch_dtype: str = "default",
    patch_on_device: bool = False
):
    """
    Load diffusion model (UNET) in GGUF format.
    
    Supports: Flux, Wan, SD3, SDXL, SD1, Aura, HiDream, Cosmos, LTXV, HyVid, Lumina2, etc.
    
    Based on: UnetLoaderGGUF from ComfyUI-GGUF/nodes.py
    
    Args:
        unet_name: Name of the GGUF model file from diffusion_models folder
        dequant_dtype: Data type for dequantization
            - "default" (None) - Keep quantized
            - "target" - Dequantize to target dtype
            - "float32" - Dequantize to float32
            - "float16" - Dequantize to float16
            - "bfloat16" - Dequantize to bfloat16
        patch_dtype: Data type for patches (LoRA, etc)
            - "default" (None) - Use default
            - "target" - Use target dtype
            - "float32", "float16", "bfloat16" - Specific dtype
        patch_on_device: Whether to patch on device (False = offload, saves VRAM)
        
    Returns:
        model: Loaded GGUF model wrapped in GGUFModelPatcher
        
    Example:
        >>> # Load quantized Flux model
        >>> model = load_unet_gguf("flux1-dev-Q4_K_S.gguf")
        >>> 
        >>> # Load with float16 dequantization
        >>> model = load_unet_gguf(
        ...     "wan-2.1-Q8_0.gguf",
        ...     dequant_dtype="float16"
        ... )
    """
    check_gguf_available()
    
    # Import GGUFModelPatcher here to avoid import errors if GGUF not available
    from nodes import GGUFModelPatcher  # type: ignore
    
    # Setup operations with quantization settings
    ops = GGMLOps()
    
    # Configure dequantization dtype
    if dequant_dtype in ("default", None):
        ops.Linear.dequant_dtype = None
    elif dequant_dtype == "target":
        ops.Linear.dequant_dtype = "target"
    else:
        ops.Linear.dequant_dtype = getattr(torch, dequant_dtype)
    
    # Configure patch dtype
    if patch_dtype in ("default", None):
        ops.Linear.patch_dtype = None
    elif patch_dtype == "target":
        ops.Linear.patch_dtype = "target"
    else:
        ops.Linear.patch_dtype = getattr(torch, patch_dtype)
    
    # Load GGUF file
    unet_path = folder_paths.get_full_path("unet", unet_name)
    sd = gguf_sd_loader(unet_path)
    
    # Load diffusion model with GGUF operations
    model = comfy.sd.load_diffusion_model_state_dict(
        sd, model_options={"custom_operations": ops}
    )
    
    if model is None:
        logging.error(f"ERROR: Unsupported UNET {unet_path}")
        raise RuntimeError(f"ERROR: Could not detect model type of: {unet_path}")
    
    # Wrap in GGUF model patcher
    model = GGUFModelPatcher.clone(model)
    model.patch_on_device = patch_on_device
    
    return model


def load_clip_gguf(
    clip_name: str,
    clip_type: str = "stable_diffusion"
):
    """
    Load CLIP text encoder in GGUF format.
    
    Supports: T5, LLaMA, Qwen2VL, and standard CLIP variants
    
    Based on: CLIPLoaderGGUF from ComfyUI-GGUF/nodes.py
    
    Args:
        clip_name: Name of the GGUF CLIP file from text_encoders folder
            Can also be non-GGUF file (will load normally)
        clip_type: Type of CLIP model - one of:
            "stable_diffusion", "stable_cascade", "sd3", "stable_audio",
            "mochi", "ltxv", "pixart", "cosmos", "lumina2", "wan",
            "hidream", "chroma", "ace", "omnigen2", "qwen_image", "hunyuan_image"
            
    Returns:
        clip: Loaded CLIP model wrapped in GGUFModelPatcher
        
    Example:
        >>> # Load quantized T5 for Wan
        >>> clip = load_clip_gguf("umt5-xxl-Q8_0.gguf", clip_type="wan")
        >>> 
        >>> # Load quantized T5 for SD3
        >>> clip = load_clip_gguf("t5xxl-Q4_K_M.gguf", clip_type="sd3")
    """
    check_gguf_available()
    
    from nodes import GGUFModelPatcher  # type: ignore
    
    # Get clip path and type
    clip_path = folder_paths.get_full_path("clip", clip_name)
    clip_type_enum = getattr(
        comfy.sd.CLIPType,
        clip_type.upper(),
        comfy.sd.CLIPType.STABLE_DIFFUSION
    )
    
    # Load GGUF or regular file
    if clip_path.endswith(".gguf"):
        sd = gguf_clip_loader(clip_path)
    else:
        sd = comfy.utils.load_torch_file(clip_path, safe_load=True)  # type: ignore
    
    # Load text encoder with GGUF operations
    clip = comfy.sd.load_text_encoder_state_dicts(
        clip_type=clip_type_enum,
        state_dicts=[sd],
        model_options={
            "custom_operations": GGMLOps,
            "initial_device": comfy.model_management.text_encoder_offload_device()
        },
        embedding_directory=folder_paths.get_folder_paths("embeddings"),
    )
    
    # Wrap patcher in GGUF model patcher
    clip.patcher = GGUFModelPatcher.clone(clip.patcher)
    
    return clip


def load_dual_clip_gguf(
    clip_name1: str,
    clip_name2: str,
    clip_type: str = "sdxl"
):
    """
    Load dual CLIP text encoders in GGUF format.
    
    Used for models that require two CLIP encoders (SDXL, SD3, Flux, etc.)
    
    Based on: DualCLIPLoaderGGUF from ComfyUI-GGUF/nodes.py
    
    Args:
        clip_name1: First CLIP file (e.g., "clip-l.gguf")
        clip_name2: Second CLIP file (e.g., "t5xxl.gguf")
        clip_type: Type of dual CLIP model:
            - "sdxl" - SDXL (clip-l + clip-g)
            - "sd3" - SD3 (clip-l + clip-g / clip-l + t5 / clip-g + t5)
            - "flux" - Flux (clip-l + t5)
            - "hunyuan_video" - HunyuanVideo
            - "hidream" - HiDream
            - "hunyuan_image" - HunyuanImage (qwen2.5vl 7b + byt5 small)
            
    Returns:
        clip: Loaded dual CLIP model
        
    Example:
        >>> # Load SDXL dual CLIP
        >>> clip = load_dual_clip_gguf(
        ...     "clip-l-Q8_0.gguf",
        ...     "clip-g-Q8_0.gguf",
        ...     clip_type="sdxl"
        ... )
        >>> 
        >>> # Load Flux dual CLIP
        >>> clip = load_dual_clip_gguf(
        ...     "clip-l.safetensors",
        ...     "t5xxl-Q4_K_M.gguf",
        ...     clip_type="flux"
        ... )
    """
    check_gguf_available()
    
    from nodes import GGUFModelPatcher  # type: ignore
    
    # Get paths
    clip_path1 = folder_paths.get_full_path("clip", clip_name1)
    clip_path2 = folder_paths.get_full_path("clip", clip_name2)
    clip_paths = [clip_path1, clip_path2]
    
    # Get clip type
    clip_type_enum = getattr(
        comfy.sd.CLIPType,
        clip_type.upper(),
        comfy.sd.CLIPType.STABLE_DIFFUSION
    )
    
    # Load both CLIPs (GGUF or regular)
    clip_data = []
    for p in clip_paths:
        if p.endswith(".gguf"):
            sd = gguf_clip_loader(p)
        else:
            sd = comfy.utils.load_torch_file(p, safe_load=True)  # type: ignore
        clip_data.append(sd)
    
    # Load text encoders
    clip = comfy.sd.load_text_encoder_state_dicts(
        clip_type=clip_type_enum,
        state_dicts=clip_data,
        model_options={
            "custom_operations": GGMLOps,
            "initial_device": comfy.model_management.text_encoder_offload_device()
        },
        embedding_directory=folder_paths.get_folder_paths("embeddings"),
    )
    
    # Wrap patcher
    clip.patcher = GGUFModelPatcher.clone(clip.patcher)
    
    return clip


def load_triple_clip_gguf(
    clip_name1: str,
    clip_name2: str,
    clip_name3: str,
    clip_type: str = "sd3"
):
    """
    Load triple CLIP text encoders in GGUF format.
    
    Used for SD3 with all three text encoders.
    
    Based on: TripleCLIPLoaderGGUF from ComfyUI-GGUF/nodes.py
    
    Args:
        clip_name1: First CLIP file (e.g., "clip-l.gguf")
        clip_name2: Second CLIP file (e.g., "clip-g.gguf")
        clip_name3: Third CLIP file (e.g., "t5xxl.gguf")
        clip_type: Type (usually "sd3")
        
    Returns:
        clip: Loaded triple CLIP model
        
    Example:
        >>> # Load SD3 triple CLIP
        >>> clip = load_triple_clip_gguf(
        ...     "clip-l-Q8_0.gguf",
        ...     "clip-g-Q8_0.gguf",
        ...     "t5xxl-Q4_K_M.gguf",
        ...     clip_type="sd3"
        ... )
    """
    check_gguf_available()
    
    from nodes import GGUFModelPatcher  # type: ignore
    
    # Get paths
    clip_path1 = folder_paths.get_full_path("clip", clip_name1)
    clip_path2 = folder_paths.get_full_path("clip", clip_name2)
    clip_path3 = folder_paths.get_full_path("clip", clip_name3)
    clip_paths = [clip_path1, clip_path2, clip_path3]
    
    # Get clip type
    clip_type_enum = getattr(
        comfy.sd.CLIPType,
        clip_type.upper(),
        comfy.sd.CLIPType.STABLE_DIFFUSION
    )
    
    # Load all three CLIPs
    clip_data = []
    for p in clip_paths:
        if p.endswith(".gguf"):
            sd = gguf_clip_loader(p)
        else:
            sd = comfy.utils.load_torch_file(p, safe_load=True)  # type: ignore
        clip_data.append(sd)
    
    # Load text encoders
    clip = comfy.sd.load_text_encoder_state_dicts(
        clip_type=clip_type_enum,
        state_dicts=clip_data,
        model_options={
            "custom_operations": GGMLOps,
            "initial_device": comfy.model_management.text_encoder_offload_device()
        },
        embedding_directory=folder_paths.get_folder_paths("embeddings"),
    )
    
    # Wrap patcher
    clip.patcher = GGUFModelPatcher.clone(clip.patcher)
    
    return clip


# Quantization types reference
GGUF_QUANT_TYPES = {
    "Q4_0": "4-bit (smallest, lowest quality)",
    "Q4_1": "4-bit (slightly better than Q4_0)",
    "Q4_K_S": "4-bit (small, recommended for most use cases)",
    "Q4_K_M": "4-bit (medium, good balance)",
    "Q5_0": "5-bit",
    "Q5_1": "5-bit",
    "Q5_K_S": "5-bit (small)",
    "Q5_K_M": "5-bit (medium, recommended for quality)",
    "Q6_K": "6-bit (high quality, still compact)",
    "Q8_0": "8-bit (best quality, larger size)",
    "Q8_1": "8-bit",
    "F16": "float16 (no quantization)",
    "F32": "float32 (no quantization)",
}


def get_gguf_info():
    """
    Get information about GGUF support and available quantization types.
    
    Returns:
        dict: Information about GGUF availability and quant types
    """
    return {
        "available": GGUF_AVAILABLE,
        "quantization_types": GGUF_QUANT_TYPES,
        "supported_models": {
            "diffusion": [
                "flux", "wan", "sd3", "sdxl", "sd1",
                "aura", "hidream", "cosmos", "ltxv",
                "hyvid", "lumina2", "qwen_image"
            ],
            "text_encoders": ["t5", "llama", "qwen2vl", "clip"],
        }
    }

