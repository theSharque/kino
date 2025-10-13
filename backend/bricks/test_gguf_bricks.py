#!/usr/bin/env python3
"""
Test script for gguf_bricks components.

This script checks GGUF support availability and displays information
about the gguf_bricks functions.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

try:
    import gguf_bricks
    GGUF_BRICKS_AVAILABLE = True
except ImportError as e:
    GGUF_BRICKS_AVAILABLE = False
    IMPORT_ERROR = str(e)


def test_imports():
    """Test that gguf_bricks can be imported"""
    print("Testing imports...")
    
    if not GGUF_BRICKS_AVAILABLE:
        print(f"  ✗ gguf_bricks import failed: {IMPORT_ERROR}")
        return False
    
    functions = [
        'load_unet_gguf',
        'load_clip_gguf',
        'load_dual_clip_gguf',
        'load_triple_clip_gguf',
        'get_gguf_info',
    ]
    
    for func_name in functions:
        if hasattr(gguf_bricks, func_name):
            print(f"  ✓ {func_name} imported successfully")
        else:
            print(f"  ✗ {func_name} NOT FOUND")
            return False
    
    return True


def check_gguf_support():
    """Check if ComfyUI-GGUF is available"""
    print("\nChecking GGUF Support:")
    print("=" * 60)
    
    if not GGUF_BRICKS_AVAILABLE:
        print("  ✗ gguf_bricks not available")
        return False
    
    info = gguf_bricks.get_gguf_info()
    
    if info['available']:
        print("  ✓ ComfyUI-GGUF is installed and available")
    else:
        print("  ✗ ComfyUI-GGUF is NOT installed")
        print("\nTo install ComfyUI-GGUF:")
        print("  cd /qs/kino/backend/ComfyUI/custom_nodes")
        print("  git clone https://github.com/city96/ComfyUI-GGUF.git")
        print("  cd ComfyUI-GGUF")
        print("  pip install -r requirements.txt")
        return False
    
    return True


def print_quantization_types():
    """Print available quantization types"""
    if not GGUF_BRICKS_AVAILABLE:
        return
    
    print("\nQuantization Types:")
    print("=" * 60)
    
    info = gguf_bricks.get_gguf_info()
    quant_types = info['quantization_types']
    
    print("\n{:<12} {}".format("Type", "Description"))
    print("-" * 60)
    
    # Recommended types first
    recommended = ['Q4_K_S', 'Q5_K_M', 'Q8_0']
    for qtype in recommended:
        if qtype in quant_types:
            desc = quant_types[qtype]
            print("{:<12} {} ⭐ RECOMMENDED".format(qtype, desc))
    
    print()
    
    # Other types
    for qtype, desc in quant_types.items():
        if qtype not in recommended:
            print("{:<12} {}".format(qtype, desc))


def print_supported_models():
    """Print supported model types"""
    if not GGUF_BRICKS_AVAILABLE:
        return
    
    print("\nSupported Model Types:")
    print("=" * 60)
    
    info = gguf_bricks.get_gguf_info()
    supported = info['supported_models']
    
    print("\nDiffusion Models:")
    for model in supported['diffusion']:
        print(f"  • {model}")
    
    print("\nText Encoders:")
    for model in supported['text_encoders']:
        print(f"  • {model}")


def print_function_signatures():
    """Print function signatures for reference"""
    print("\nFunction Signatures:")
    print("=" * 60)
    
    print("\n1. load_unet_gguf(")
    print("       unet_name: str,")
    print("       dequant_dtype: str = 'default',")
    print("       patch_dtype: str = 'default',")
    print("       patch_on_device: bool = False")
    print("   )")
    print("   → Returns: GGUF model")
    
    print("\n2. load_clip_gguf(")
    print("       clip_name: str,")
    print("       clip_type: str = 'stable_diffusion'")
    print("   )")
    print("   → Returns: GGUF CLIP")
    
    print("\n3. load_dual_clip_gguf(")
    print("       clip_name1: str,")
    print("       clip_name2: str,")
    print("       clip_type: str = 'sdxl'")
    print("   )")
    print("   → Returns: Dual GGUF CLIP")
    
    print("\n4. load_triple_clip_gguf(")
    print("       clip_name1: str,")
    print("       clip_name2: str,")
    print("       clip_name3: str,")
    print("       clip_type: str = 'sd3'")
    print("   )")
    print("   → Returns: Triple GGUF CLIP")
    
    print("\n5. get_gguf_info()")
    print("   → Returns: dict with GGUF info")


def print_usage_examples():
    """Print usage examples"""
    print("\nUsage Examples:")
    print("=" * 60)
    
    print("\n# Example 1: Load quantized Flux")
    print("from bricks.gguf_bricks import load_unet_gguf, load_dual_clip_gguf")
    print("")
    print("model = load_unet_gguf('flux1-dev-Q4_K_S.gguf')")
    print("clip = load_dual_clip_gguf(")
    print("    'clip-l.safetensors',")
    print("    't5xxl-Q4_K_M.gguf',")
    print("    clip_type='flux'")
    print(")")
    
    print("\n# Example 2: Load quantized Wan")
    print("from bricks.gguf_bricks import load_unet_gguf, load_clip_gguf")
    print("from bricks.wan_bricks import load_vae, load_clip_vision")
    print("")
    print("model = load_unet_gguf('wan-2.1-Q8_0.gguf')")
    print("clip = load_clip_gguf('umt5-xxl-Q8_0.gguf', clip_type='wan')")
    print("vae = load_vae('wan_2.1_vae.safetensors')")
    print("clip_vision = load_clip_vision('clip_vision_g.safetensors')")
    
    print("\n# Example 3: Load SD3 with triple CLIP")
    print("from bricks.gguf_bricks import load_unet_gguf, load_triple_clip_gguf")
    print("")
    print("model = load_unet_gguf('sd3-Q5_K_M.gguf')")
    print("clip = load_triple_clip_gguf(")
    print("    'clip-l-Q8_0.gguf',")
    print("    'clip-g-Q8_0.gguf',")
    print("    't5xxl-Q4_K_M.gguf',")
    print("    clip_type='sd3'")
    print(")")


def print_vram_comparison():
    """Print VRAM usage comparison"""
    print("\nVRAM Usage Comparison (Flux Dev example):")
    print("=" * 60)
    print("\n{:<10} {:>8} {:>15}".format("Format", "Size", "VRAM Usage"))
    print("-" * 60)
    print("{:<10} {:>8} {:>15}".format("F16", "24 GB", "~24 GB"))
    print("{:<10} {:>8} {:>15}".format("Q8_0", "12 GB", "~12 GB"))
    print("{:<10} {:>8} {:>15}".format("Q5_K_M", "8 GB", "~8 GB"))
    print("{:<10} {:>8} {:>15} ⭐".format("Q4_K_S", "6 GB", "~6 GB"))
    print("\nNote: Actual usage depends on resolution, batch size, etc.")


if __name__ == "__main__":
    print("GGUF Bricks Test Script")
    print("=" * 60)
    
    # Test imports
    if not test_imports():
        print("\n✗ Import test failed!")
        print("\nMake sure you're running from the backend directory:")
        print("  cd /qs/kino/backend")
        print("  python bricks/test_gguf_bricks.py")
        sys.exit(1)
    
    print("\n✓ All imports successful!")
    
    # Check GGUF support
    gguf_available = check_gguf_support()
    
    # Print info
    print_quantization_types()
    print_supported_models()
    print_function_signatures()
    print_usage_examples()
    print_vram_comparison()
    
    # Final status
    print("\n" + "=" * 60)
    if gguf_available:
        print("✓ GGUF support is ready to use!")
    else:
        print("⚠ GGUF support is available but ComfyUI-GGUF needs to be installed")
    print("\nFor detailed documentation, see:")
    print("  backend/bricks/README_GGUF.md")
    print("=" * 60)

