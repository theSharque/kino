#!/usr/bin/env python3
"""
Test script for GPU detection and monitoring

Run this script to check what GPU is available on your system:
- Intel Arc GPU (XPU)
- NVIDIA GPU (CUDA)
- No GPU

Usage:
    python test_gpu_detection.py
"""

from system_monitor import SystemMonitor


def main():
    print("=" * 60)
    print("GPU Detection Test")
    print("=" * 60)

    # Create system monitor
    monitor = SystemMonitor()

    # Get GPU info
    print(f"\nGPU Available: {monitor._gpu_available}")
    print(f"GPU Type: {monitor._gpu_type}")

    # Get full metrics
    print("\nSystem Metrics:")
    print("-" * 60)
    metrics = monitor.get_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 60)

    # Additional PyTorch info
    print("\nPyTorch GPU Information:")
    print("-" * 60)
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")

        # Check CUDA
        print(f"\nCUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA version: {torch.version.cuda}")
            print(f"CUDA device count: {torch.cuda.device_count()}")
            if torch.cuda.device_count() > 0:
                print(f"CUDA device 0: {torch.cuda.get_device_name(0)}")

        # Check XPU (Intel Arc)
        if hasattr(torch, 'xpu'):
            print(f"\nXPU available: {torch.xpu.is_available()}")
            if torch.xpu.is_available():
                print(f"XPU device count: {torch.xpu.device_count()}")
                if torch.xpu.device_count() > 0:
                    print(f"XPU device 0: {torch.xpu.get_device_name(0)}")
        else:
            print("\nXPU: Not supported (PyTorch not compiled with XPU support)")

    except Exception as e:
        print(f"Error checking PyTorch: {e}")

    print("\n" + "=" * 60)
    print("\nRecommendations:")
    print("-" * 60)

    if monitor._gpu_type == 'xpu':
        print("✅ Intel Arc GPU (XPU) detected!")
        print("   - Metrics will show XPU usage and VRAM in the UI")
        print("   - GPU utilization is estimated from memory usage")
    elif monitor._gpu_type == 'cuda':
        print("✅ NVIDIA GPU (CUDA) detected!")
        print("   - Metrics will show GPU usage and VRAM in the UI")
        if 'pynvml' in dir():
            print("   - Using nvidia-ml-py3 for accurate GPU metrics")
        else:
            print("   - Install nvidia-ml-py3 for more accurate metrics:")
            print("     pip install nvidia-ml-py3")
    else:
        print("ℹ️  No GPU detected")
        print("   - Application will run on CPU only")
        print("   - To enable GPU support:")
        print("\n   For Intel Arc GPU:")
        print("     pip install torch --index-url https://download.pytorch.org/whl/xpu")
        print("\n   For NVIDIA GPU:")
        print("     pip install torch --index-url https://download.pytorch.org/whl/cu118")

    print("=" * 60)


if __name__ == "__main__":
    main()


