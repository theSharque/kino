# GPU Monitoring in Kino

This document describes GPU monitoring functionality in the Kino backend.

## Supported GPU Types

- **Intel Arc GPU (XPU)** - Intel discrete GPUs with PyTorch XPU support
- **NVIDIA GPU (CUDA)** - NVIDIA GPUs with CUDA support
- **CPU-only mode** - Graceful fallback when no GPU is detected

## Architecture

### Detection Flow

1. **Initialization** (`SystemMonitor.__init__`)
   - Checks for Intel XPU via `torch.xpu.is_available()`
   - Falls back to NVIDIA CUDA via `torch.cuda.is_available()`
   - Sets `gpu_type` to 'xpu', 'cuda', or 'none'

2. **Metrics Collection** (`SystemMonitor.get_metrics`)
   - Collects CPU and RAM metrics via psutil
   - Calls `_get_xpu_metrics()` or `_get_cuda_metrics()` based on GPU type
   - Returns unified metrics dictionary

3. **WebSocket Broadcast**
   - Metrics sent to frontend every 2 seconds
   - Includes: `cpu_percent`, `memory_percent`, `gpu_percent`, `gpu_memory_percent`, `gpu_type`, `gpu_available`

## XPU (Intel Arc) Monitoring

### API Used
- `torch.xpu.is_available()` - Check XPU availability
- `torch.xpu.memory_allocated(device)` - Get allocated memory in bytes
- `torch.xpu.memory_reserved(device)` - Get reserved memory in bytes

### Metrics
- **GPU Memory %**: `(allocated / reserved) * 100`
- **GPU Utilization %**: Estimated as `memory_percent * 0.8` (heuristic)
  - Note: True utilization requires Intel level-zero library

### Limitations
- GPU utilization is estimated from memory usage
- For accurate utilization, consider using Intel's level-zero library

## CUDA (NVIDIA) Monitoring

### Primary Method (nvidia-ml-py3)
- Uses `pynvml` library for accurate metrics
- **GPU Utilization %**: From `nvmlDeviceGetUtilizationRates()`
- **GPU Memory %**: From `nvmlDeviceGetMemoryInfo()`

### Fallback Method (PyTorch)
- When nvidia-ml-py3 is not available
- Uses `torch.cuda.memory_allocated()` and `torch.cuda.memory_reserved()`
- Only provides memory metrics, not utilization

## Testing

### Quick Test
```bash
cd backend/services
python test_gpu_detection.py
```

This script will:
- Detect available GPU type
- Show current metrics
- Display PyTorch GPU information
- Provide recommendations for your system

### Expected Output Examples

**With Intel Arc GPU:**
```
GPU Available: True
GPU Type: xpu
XPU available: True
XPU device 0: Intel(R) Arc(TM) A770 Graphics
```

**With NVIDIA GPU:**
```
GPU Available: True
GPU Type: cuda
CUDA available: True
CUDA device 0: NVIDIA GeForce RTX 3090
```

**Without GPU:**
```
GPU Available: False
GPU Type: none
```

## Installation

### For Intel Arc GPU
```bash
# Install PyTorch with XPU support
pip install torch --index-url https://download.pytorch.org/whl/xpu

# Verify installation
python -c "import torch; print(torch.xpu.is_available())"
```

### For NVIDIA GPU
```bash
# Install PyTorch with CUDA support
pip install torch --index-url https://download.pytorch.org/whl/cu118

# Install nvidia-ml-py3 for accurate metrics (recommended)
pip install nvidia-ml-py3

# Verify installation
python -c "import torch; print(torch.cuda.is_available())"
```

## Frontend Display

When GPU is available, the MenuBar shows:
- **GPU Type**: `XPU` or `CUDA` (with hover tooltip)
- **GPU Utilization**: e.g., `XPU: 45.2%`
- **GPU Memory**: e.g., `VRAM: 78.5%`

## Troubleshooting

### Intel XPU not detected
1. Verify Intel GPU drivers are installed
2. Check PyTorch XPU support: `python -c "import torch; print(hasattr(torch, 'xpu'))"`
3. Reinstall PyTorch with XPU: `pip install torch --index-url https://download.pytorch.org/whl/xpu`

### NVIDIA CUDA not detected
1. Verify NVIDIA drivers are installed
2. Check CUDA installation: `nvidia-smi`
3. Reinstall PyTorch with CUDA: `pip install torch --index-url https://download.pytorch.org/whl/cu118`

### Metrics showing 0%
- **XPU**: GPU may be idle, metrics shown only when memory is allocated
- **CUDA**: Install nvidia-ml-py3 for accurate readings

## Code References

- **Backend Monitoring**: `/backend/services/system_monitor.py`
- **WebSocket Handler**: `/backend/handlers/websocket.py`
- **Frontend Hook**: `/frontend/src/hooks/useWebSocket.ts`
- **Frontend Display**: `/frontend/src/components/MenuBar.tsx`
- **Test Script**: `/backend/services/test_gpu_detection.py`


