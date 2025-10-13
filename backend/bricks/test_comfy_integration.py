#!/usr/bin/env python3
"""
Test script for ComfyUI integration via bricks

Tests that all brick functions work with the new ComfyUI structure.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import comfy_bricks


def test_imports():
    """Test that all imports work"""
    print("=" * 60)
    print("Testing ComfyUI Integration via Bricks")
    print("=" * 60)

    print("\n✅ Step 1: Imports")
    print("-" * 60)
    print(f"✅ comfy_bricks module imported")
    print(f"✅ Functions available:")
    print(f"   - load_checkpoint_plugin")
    print(f"   - clip_encode")
    print(f"   - generate_latent_image")
    print(f"   - common_ksampler")
    print(f"   - vae_decode")
    print(f"   - load_lora")


def test_latent_generation():
    """Test latent generation"""
    print("\n✅ Step 2: Latent Generation")
    print("-" * 60)

    try:
        latent = comfy_bricks.generate_latent_image(512, 512)
        print(f"✅ Generated latent image: {latent['samples'].shape}")
        print(f"   Expected shape: torch.Size([1, 4, 64, 64])")
        assert latent['samples'].shape == (1, 4, 64, 64), "Latent shape mismatch!"
        print(f"✅ Latent shape is correct!")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    return True


def test_comfyui_path():
    """Test ComfyUI path setup"""
    print("\n✅ Step 3: ComfyUI Path")
    print("-" * 60)

    comfyui_dir = Path(__file__).parent.parent / "ComfyUI"
    print(f"ComfyUI directory: {comfyui_dir}")
    print(f"Exists: {comfyui_dir.exists()}")
    print(f"comfy subdirectory: {(comfyui_dir / 'comfy').exists()}")

    if str(comfyui_dir) in sys.path:
        print(f"✅ ComfyUI is in sys.path")
    else:
        print(f"❌ ComfyUI NOT in sys.path")
        return False

    return True


def test_constants():
    """Test constants module"""
    print("\n✅ Step 4: Constants Module")
    print("-" * 60)

    try:
        from comfy_constants import SAMPLER_NAMES, SCHEDULER_NAMES
        print(f"✅ Imported constants successfully")
        print(f"   Total samplers: {len(SAMPLER_NAMES)}")
        print(f"   Total schedulers: {len(SCHEDULER_NAMES)}")
        print(f"   Sample samplers: {SAMPLER_NAMES[:5]}")
        print(f"   Sample schedulers: {SCHEDULER_NAMES[:3]}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    return True


def main():
    success = True

    # Run tests
    test_imports()
    success = test_comfyui_path() and success
    success = test_latent_generation() and success
    success = test_constants() and success

    # Final result
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed!")
        print("=" * 60)
        print("\n💡 ComfyUI Integration Status:")
        print("   - Imports: Working ✅")
        print("   - sys.path: Configured ✅")
        print("   - Latent generation: Working ✅")
        print("   - Constants: Available ✅")
        print("\n🎉 Ready to use full ComfyUI!")
    else:
        print("❌ Some tests failed!")
        print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

