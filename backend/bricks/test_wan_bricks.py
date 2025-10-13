#!/usr/bin/env python3
"""
Test script for wan_bricks components.

This script demonstrates and tests the individual wan_bricks functions
to ensure they can be imported and their signatures are correct.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import wan_bricks


def test_imports():
    """Test that all functions can be imported"""
    print("Testing imports...")

    functions = [
        'load_clip_vision',
        'clip_vision_encode',
        'load_vae',
        'load_clip',
        'wan_image_to_video'
    ]

    for func_name in functions:
        if hasattr(wan_bricks, func_name):
            print(f"  ✓ {func_name} imported successfully")
        else:
            print(f"  ✗ {func_name} NOT FOUND")
            return False

    return True


def print_function_signatures():
    """Print function signatures for reference"""
    print("\nFunction Signatures:")
    print("=" * 60)

    print("\n1. load_clip_vision(clip_name: str)")
    print("   → Returns: clip_vision model")

    print("\n2. clip_vision_encode(clip_vision, image, crop='center')")
    print("   → Returns: CLIP_VISION_OUTPUT embedding")

    print("\n3. load_vae(vae_name: str)")
    print("   → Returns: VAE model")

    print("\n4. load_clip(clip_name: str, clip_type: str = 'wan', device: str = 'default')")
    print("   → Returns: CLIP text encoder model")

    print("\n5. wan_image_to_video(")
    print("       positive, negative, vae,")
    print("       width=832, height=480, length=81, batch_size=1,")
    print("       clip_vision_output=None, start_image=None)")
    print("   → Returns: (positive, negative, latent)")

    print("\n" + "=" * 60)


def print_input_output_summary():
    """Print summary of inputs and outputs for each component"""
    print("\nInput/Output Summary:")
    print("=" * 60)

    components = [
        {
            "name": "1. Load CLIP Vision",
            "inputs": [
                "clip_name: str - model filename"
            ],
            "outputs": [
                "clip_vision - CLIP Vision model object"
            ]
        },
        {
            "name": "2. CLIP Vision Encode",
            "inputs": [
                "clip_vision - model from load_clip_vision()",
                "image - torch.Tensor [B, H, W, C]",
                "crop - 'center' or 'none'"
            ],
            "outputs": [
                "clip_vision_output - CLIP_VISION_OUTPUT embedding"
            ]
        },
        {
            "name": "3. Load VAE",
            "inputs": [
                "vae_name: str - model filename or special name"
            ],
            "outputs": [
                "vae - VAE model object"
            ]
        },
        {
            "name": "4. Load CLIP (Text Encoder)",
            "inputs": [
                "clip_name: str - model filename",
                "clip_type: str - model type (default: 'wan')",
                "device: str - 'default' or 'cpu'"
            ],
            "outputs": [
                "clip - CLIP text encoder model"
            ]
        },
        {
            "name": "5. Wan Image to Video",
            "inputs": [
                "positive - positive conditioning",
                "negative - negative conditioning",
                "vae - VAE model",
                "width: int - video width (default: 832)",
                "height: int - video height (default: 480)",
                "length: int - frames (default: 81)",
                "batch_size: int - (default: 1)",
                "clip_vision_output - optional CLIP vision embedding",
                "start_image - optional starting frame"
            ],
            "outputs": [
                "positive - modified conditioning",
                "negative - modified conditioning",
                "latent - dict with 'samples' key"
            ]
        }
    ]

    for comp in components:
        print(f"\n{comp['name']}")
        print("-" * 60)
        print("INPUTS:")
        for inp in comp['inputs']:
            print(f"  • {inp}")
        print("OUTPUTS:")
        for out in comp['outputs']:
            print(f"  • {out}")

    print("\n" + "=" * 60)


def print_workflow_example():
    """Print a complete workflow example"""
    print("\nComplete Workflow Example:")
    print("=" * 60)
    print("""
# Step 1: Load CLIP Vision
clip_vision = load_clip_vision("clip_vision_g.safetensors")

# Step 2: Encode reference image (optional)
clip_vision_output = clip_vision_encode(
    clip_vision=clip_vision,
    image=reference_image,  # torch.Tensor [1, H, W, 3]
    crop="center"
)

# Step 3: Load VAE
vae = load_vae("wan_2.1_vae.safetensors")

# Step 4: Load CLIP text encoder
clip = load_clip(
    clip_name="umt5_xxl.safetensors",
    clip_type="wan"
)

# Step 5: Encode text prompts (from comfy_bricks)
from bricks.comfy_bricks import clip_encode
positive = clip_encode(clip, "a beautiful cat walking")
negative = clip_encode(clip, "blurry, low quality")

# Step 6: Prepare video generation
positive, negative, latent = wan_image_to_video(
    positive=positive,
    negative=negative,
    vae=vae,
    width=832,
    height=480,
    length=81,
    clip_vision_output=clip_vision_output,
    start_image=first_frame  # torch.Tensor [1, H, W, 3]
)

# Step 7: Use with sampler (from comfy_bricks)
# from bricks.comfy_bricks import common_ksampler
# samples, seed = common_ksampler(
#     model=model,  # Wan diffusion model
#     latent=latent,
#     positive=positive,
#     negative=negative,
#     steps=20,
#     cfg=7.0,
#     sampler_name='euler',
#     scheduler='simple'
# )

# Step 8: Decode video (from comfy_bricks)
# from bricks.comfy_bricks import vae_decode
# video_frames = vae_decode(vae, samples)
""")
    print("=" * 60)


if __name__ == "__main__":
    print("Wan Bricks Test Script")
    print("=" * 60)

    # Test imports
    if test_imports():
        print("\n✓ All imports successful!")
    else:
        print("\n✗ Import test failed!")
        sys.exit(1)

    # Print function signatures
    print_function_signatures()

    # Print input/output summary
    print_input_output_summary()

    # Print workflow example
    print_workflow_example()

    print("\nTest completed successfully!")
    print("\nNote: This script only tests imports and displays documentation.")
    print("Actual model loading requires the models to be present in the")
    print("appropriate directories (models/clip_vision/, models/vae/, etc.)")

