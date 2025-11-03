# GPU Acceleration - Implementation Guide

## Overview
This document describes the GPU acceleration setup for the DEM (Discrete Element Method) physics simulation using NVIDIA CUDA and CuPy.

## Hardware Requirements
- **GPU**: NVIDIA RTX 4060 Laptop (8GB VRAM, Compute Capability 8.9)
- **Driver**: NVIDIA 580.95.05 or newer
- **CUDA**: 12.2+ compatible

## Two Deployment Options

### Option A: CUDA Runtime on Host (Recommended for Development)
**Advantages:**
- GPU accessible from host Python scripts
- Better debugging experience
- Easier profiling and monitoring

**Installation:**
```bash
# 1. Add CUDA repository
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update

# 2. Install CUDA Runtime (lighter than full toolkit)
sudo apt-get install -y cuda-runtime-12-2

# 3. Set environment variables
echo 'export PATH=/usr/local/cuda-12.2/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.2/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# 4. Verify installation
nvidia-smi
nvcc --version
```

**Docker Configuration:**
```yaml
# docker-compose.yml
backend:
  environment:
    NVIDIA_VISIBLE_DEVICES: all
    NVIDIA_DRIVER_CAPABILITIES: compute,utility
    LD_LIBRARY_PATH: /usr/local/nvidia/lib64
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

### Option B: CUDA in Docker Image (Recommended for Production)
**Advantages:**
- Portable across systems
- No host CUDA installation required
- Consistent environment
- Better for CI/CD

**Dockerfile:**
```dockerfile
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

# Install Python 3.11
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies including CuPy
COPY requirements.txt .
RUN pip install -r requirements.txt
```

**Build and Run:**
```bash
# Build GPU-enabled image
docker build -f Dockerfile.gpu -t optiflow-backend-gpu .

# Run with GPU access
docker run --gpus all optiflow-backend-gpu
```

## Code Implementation

### Automatic CPU/GPU Fallback
The DEM physics engine automatically detects GPU availability:

```python
# backend/app/services/dem_physics.py
try:
    import cupy as cp
    GPU_AVAILABLE = True
    xp = cp  # Use CuPy arrays (GPU)
    logger.info("🚀 GPU ACCELERATION ENABLED")
except ImportError:
    GPU_AVAILABLE = False
    xp = np  # Use NumPy arrays (CPU)
    logger.info("⚠️ GPU not available - Using CPU")
```

### GPU Utilities
```python
def _get_gpu_info(self):
    """Get GPU information"""
    if not GPU_AVAILABLE:
        return None
    device = cp.cuda.Device()
    mem_info = cp.cuda.runtime.memGetInfo()
    return {
        'name': device.name,
        'compute_capability': device.compute_capability,
        'memory_total_mb': mem_info[1] / (1024**2),
        'memory_free_mb': mem_info[0] / (1024**2)
    }

def to_numpy(self, arr):
    """Convert CuPy array to NumPy for compatibility"""
    if GPU_AVAILABLE and isinstance(arr, cp.ndarray):
        return cp.asnumpy(arr)
    return arr

def to_gpu(self, arr):
    """Convert NumPy array to GPU"""
    if GPU_AVAILABLE and isinstance(arr, np.ndarray):
        return cp.asarray(arr)
    return arr
```

## Performance Expectations

### Particle Count Limits
- **CPU (NumPy)**: 500-800 particles @ 60 FPS
- **GPU (CuPy)**: 5,000-8,000 particles @ 60 FPS
- **Speedup**: 10-50x depending on operation

### GPU Utilization
- Expected GPU usage: 20-40% during simulation
- VRAM usage: 500-1500 MB (out of 8GB available)
- Power consumption: ~15-25W

## Monitoring

### Check GPU Status
```bash
# Real-time monitoring
watch -n 0.5 nvidia-smi

# Container GPU access
docker exec optiflow-backend nvidia-smi

# CuPy version and GPU info
docker exec optiflow-backend python -c "import cupy as cp; print(cp.cuda.Device().name)"
```

### Application Logs
```bash
# Check if GPU is detected
docker logs optiflow-backend | grep GPU

# Expected output:
# 🚀 GPU ACCELERATION ENABLED - CuPy detected
# GPU: NVIDIA GeForce RTX 4060 Laptop GPU
# VRAM: 8188 MB
# Compute Capability: 8.9
```

## Troubleshooting

### Problem: "libcudart.so.12: cannot open shared object file"
**Solution:** CUDA libraries not in container path
```bash
# Option 1: Install CUDA runtime on host (Option A)
sudo apt-get install cuda-runtime-12-2

# Option 2: Use CUDA base image (Option B)
docker build -f Dockerfile.gpu -t optiflow-backend-gpu .
```

### Problem: "No module named 'cupy'"
**Solution:** CuPy not installed
```bash
# Install in container
docker exec optiflow-backend pip install cupy-cuda12x==12.3.0

# Or rebuild image with requirements.txt containing cupy
```

### Problem: GPU shows 0% utilization
**Possible causes:**
1. Simulation not running: Start with `/api/v1/simulator/start`
2. Particle count too low: Increase spawn rate
3. CPU fallback active: Check logs for ImportError

## Best Practices

### Development
1. Use Option A (host CUDA) for easier debugging
2. Monitor GPU with `nvidia-smi` during development
3. Profile with `nsight-systems` for optimization
4. Test CPU fallback regularly

### Production
1. Use Option B (Docker CUDA image) for consistency
2. Set resource limits in docker-compose.yml
3. Monitor VRAM usage to prevent OOM
4. Keep driver updated (580+)

### Code
1. Always use `xp` instead of hardcoding `np` or `cp`
2. Convert to NumPy only when necessary (e.g., JSON serialization)
3. Batch operations for better GPU utilization
4. Use `dtype=float64` explicitly for physics calculations

## Files Modified

- `/backend/app/services/dem_physics.py` - GPU/CPU abstraction
- `/backend/requirements.txt` - Added cupy-cuda12x==12.3.0
- `/backend/Dockerfile.gpu` - CUDA-enabled image
- `/docker-compose.yml` - GPU resource reservation
- `/etc/docker/daemon.json` - NVIDIA runtime configuration

## References

- NVIDIA CUDA Toolkit: https://developer.nvidia.com/cuda-downloads
- CuPy Documentation: https://docs.cupy.dev/
- nvidia-container-toolkit: https://github.com/NVIDIA/nvidia-container-toolkit
- Docker GPU Support: https://docs.docker.com/config/containers/resource_constraints/#gpu

## Status

✅ **Implemented:**
- GPU detection and automatic fallback
- CuPy integration in DEM engine
- Docker GPU configuration
- Dockerfile.gpu with CUDA 12.2

🔄 **In Progress:**
- Option A: Installing CUDA runtime on host
- Testing GPU acceleration with larger particle counts

⏳ **Pending:**
- Performance benchmarks (CPU vs GPU)
- GPU monitoring UI component
- Automatic particle count scaling based on GPU availability
