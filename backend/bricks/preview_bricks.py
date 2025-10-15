"""
Preview generation bricks for ComfyUI integration

This module provides preview generation functionality during sampling.
It uses ComfyUI's latent preview system to generate quick previews
that are updated in real-time during image generation.
"""
import sys
from pathlib import Path
from PIL import Image
import numpy as np
import torch

# Add ComfyUI to path
comfyui_path = Path(__file__).parent.parent / "ComfyUI"
if str(comfyui_path) not in sys.path:
    sys.path.insert(0, str(comfyui_path))

from latent_preview import get_previewer, Latent2RGBPreviewer
import comfy.utils


class PreviewGenerator:
    """
    Generates preview images during sampling process
    """
    def __init__(self, model):
        """
        Initialize preview generator

        Args:
            model: ComfyUI model object (has load_device and model.latent_format)
        """
        self.model = model
        self.previewer = get_previewer(model.load_device, model.model.latent_format)

        # Fallback to Latent2RGB if no previewer found
        if self.previewer is None:
            latent_format = model.model.latent_format
            if hasattr(latent_format, 'latent_rgb_factors') and latent_format.latent_rgb_factors is not None:
                self.previewer = Latent2RGBPreviewer(
                    latent_format.latent_rgb_factors,
                    getattr(latent_format, 'latent_rgb_factors_bias', None)
                )

    def generate_preview(self, x0):
        """
        Generate preview image from latent

        Args:
            x0: Latent tensor from sampling step

        Returns:
            PIL.Image: Preview image or None if preview generation not available
        """
        if self.previewer is None:
            return None

        try:
            preview_image = self.previewer.decode_latent_to_preview(x0)
            return preview_image
        except Exception as e:
            print(f"Warning: Failed to generate preview: {e}")
            return None


def create_preview_callback(model, steps, preview_callback=None):
    """
    Create a callback function for sampling that generates previews
    Compatible with ComfyUI's ProgressBar system

    Args:
        model: ComfyUI model object
        steps: Total number of sampling steps
        preview_callback: Optional callback function(step, total_steps, preview_image)
                         Called with preview image at each step

    Returns:
        Callback function for sampler.sample()
    """
    preview_gen = PreviewGenerator(model)

    # Create ProgressBar (required for ComfyUI callback integration)
    pbar = comfy.utils.ProgressBar(steps)

    def callback(step, x0, x, total_steps):
        """
        Callback called during sampling

        Args:
            step: Current step number (0-based)
            x0: Predicted x0 (denoised latent)
            x: Current noisy latent
            total_steps: Total number of steps
        """
        # Generate preview image
        preview_image = None
        if preview_gen.previewer:
            preview_image = preview_gen.generate_preview(x0)

        # Update ProgressBar (required for ComfyUI)
        pbar.update_absolute(step + 1, total_steps, None)

        # Call user's preview callback if provided
        if preview_callback is not None and preview_image is not None:
            preview_callback(step, total_steps, preview_image)

    return callback


def save_preview_image(preview_image, output_path):
    """
    Save preview image to file

    Args:
        preview_image: PIL.Image object
        output_path: Path to save image

    Returns:
        bool: True if saved successfully
    """
    try:
        preview_image.save(output_path, format='PNG', compress_level=4)
        return True
    except Exception as e:
        print(f"Error saving preview image: {e}")
        return False

