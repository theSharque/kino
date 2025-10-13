"""
System monitoring service for CPU, GPU, and memory metrics
"""
import psutil
from typing import Dict, Any, Optional, Tuple


class SystemMonitor:
    """Monitor system resources (CPU, GPU, Memory)"""

    def __init__(self):
        self._gpu_info = self._check_gpu_available()
        self._gpu_available = self._gpu_info[0]
        self._gpu_type = self._gpu_info[1]

    def _check_gpu_available(self) -> Tuple[bool, str]:
        """
        Check if GPU monitoring is available and determine GPU type

        Returns:
            Tuple[bool, str]: (is_available, gpu_type)
            gpu_type can be: 'xpu' (Intel Arc), 'cuda' (NVIDIA), or 'none'
        """
        try:
            import torch

            # Check for Intel XPU (Arc GPU)
            if hasattr(torch, 'xpu') and torch.xpu.is_available():
                return (True, 'xpu')

            # Check for NVIDIA CUDA
            if torch.cuda.is_available():
                return (True, 'cuda')

            return (False, 'none')
        except Exception as e:
            print(f"GPU detection error: {e}")
            return (False, 'none')

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current system metrics

        Returns:
            Dict with cpu_percent, memory_percent, gpu_percent, gpu_memory_percent, gpu_type
        """
        metrics = {
            'cpu_percent': round(psutil.cpu_percent(interval=0.1), 1),
            'memory_percent': round(psutil.virtual_memory().percent, 1),
            'gpu_percent': 0.0,
            'gpu_memory_percent': 0.0,
            'gpu_available': self._gpu_available,
            'gpu_type': self._gpu_type
        }

        if self._gpu_available:
            try:
                import torch

                if self._gpu_type == 'xpu':
                    # Intel XPU (Arc GPU) monitoring
                    metrics.update(self._get_xpu_metrics(torch))

                elif self._gpu_type == 'cuda':
                    # NVIDIA CUDA monitoring
                    metrics.update(self._get_cuda_metrics(torch))

            except Exception as e:
                print(f"GPU monitoring error: {e}")

        return metrics

    def _get_xpu_metrics(self, torch) -> Dict[str, float]:
        """
        Get Intel XPU (Arc GPU) metrics

        Args:
            torch: PyTorch module

        Returns:
            Dict with gpu_percent and gpu_memory_percent
        """
        metrics = {
            'gpu_percent': 0.0,
            'gpu_memory_percent': 0.0
        }

        try:
            # Get XPU memory info
            # PyTorch XPU API is similar to CUDA API
            mem_allocated = torch.xpu.memory_allocated(0)
            mem_reserved = torch.xpu.memory_reserved(0)

            if mem_reserved > 0:
                metrics['gpu_memory_percent'] = round(
                    (mem_allocated / mem_reserved) * 100, 1
                )

            # Note: XPU utilization percentage is harder to get without specific drivers
            # For now, we estimate based on memory usage as a proxy
            # A more accurate solution would require Intel's level-zero library
            if mem_allocated > 0:
                # Basic heuristic: if memory is being used, GPU is likely active
                metrics['gpu_percent'] = min(
                    round(metrics['gpu_memory_percent'] * 0.8, 1),
                    100.0
                )

        except Exception as e:
            print(f"XPU metrics error: {e}")

        return metrics

    def _get_cuda_metrics(self, torch) -> Dict[str, float]:
        """
        Get NVIDIA CUDA metrics

        Args:
            torch: PyTorch module

        Returns:
            Dict with gpu_percent and gpu_memory_percent
        """
        metrics = {
            'gpu_percent': 0.0,
            'gpu_memory_percent': 0.0
        }

        try:
            # GPU utilization (requires nvidia-ml-py3 for accurate readings)
            try:
                import pynvml
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)

                # GPU utilization
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                metrics['gpu_percent'] = round(util.gpu, 1)

                # GPU memory
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                metrics['gpu_memory_percent'] = round(
                    (mem_info.used / mem_info.total) * 100, 1
                )

                pynvml.nvmlShutdown()
            except:
                # Fallback to PyTorch memory info
                mem_allocated = torch.cuda.memory_allocated(0)
                mem_reserved = torch.cuda.memory_reserved(0)
                if mem_reserved > 0:
                    metrics['gpu_memory_percent'] = round(
                        (mem_allocated / mem_reserved) * 100, 1
                    )
        except Exception as e:
            print(f"CUDA metrics error: {e}")

        return metrics

    def get_disk_usage(self, path: str = '/') -> Dict[str, Any]:
        """Get disk usage for a path"""
        try:
            usage = psutil.disk_usage(path)
            return {
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': round(usage.percent, 1)
            }
        except:
            return {'percent': 0.0}

