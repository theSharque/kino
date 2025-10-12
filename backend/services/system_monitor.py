"""
System monitoring service for CPU, GPU, and memory metrics
"""
import psutil
from typing import Dict, Any, Optional


class SystemMonitor:
    """Monitor system resources (CPU, GPU, Memory)"""

    def __init__(self):
        self._gpu_available = self._check_gpu_available()

    def _check_gpu_available(self) -> bool:
        """Check if GPU monitoring is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current system metrics

        Returns:
            Dict with cpu_percent, memory_percent, gpu_percent, gpu_memory_percent
        """
        metrics = {
            'cpu_percent': round(psutil.cpu_percent(interval=0.1), 1),
            'memory_percent': round(psutil.virtual_memory().percent, 1),
            'gpu_percent': 0.0,
            'gpu_memory_percent': 0.0,
            'gpu_available': self._gpu_available
        }

        if self._gpu_available:
            try:
                import torch
                if torch.cuda.is_available():
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
                print(f"GPU monitoring error: {e}")

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

