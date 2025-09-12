# 🔧 vLLM ROCm Fix Guide

## Problem
The error you encountered:
```
docker: Error response from daemon: failed to create task for container: 
exec: "--host": executable file not found in $PATH
```

## Root Cause
AMD's `rocm/vllm` Docker images have a **different entrypoint** than the standard `vllm/vllm-openai` images:

| Image Source | Docker Hub | Entrypoint | Command Format |
|-------------|------------|------------|----------------|
| **Standard vLLM** | `vllm/vllm-openai` | Pre-configured | `docker run image --host 0.0.0.0 --model ...` |
| **AMD ROCm** | `rocm/vllm` | Basic shell | `docker run image python -m vllm.entrypoints.openai.api_server --host ...` |

## The Fix

### ❌ Wrong (what was causing the error):
```bash
docker run rocm/vllm:tag --host 0.0.0.0 --model ...
```

### ✅ Correct (the fix):
```bash
docker run rocm/vllm:tag python -m vllm.entrypoints.openai.api_server --host 0.0.0.0 --model ...
```

## Key Changes Made

1. **Docker Registry Change**:
   ```bash
   # Old (doesn't exist anymore)
   IMAGE="vllm/vllm-rocm:latest"
   
   # New (AMD's official)
   IMAGE="rocm/vllm:rocm6.4.1_vllm_0.10.1_20250909"
   ```

2. **Added Python Command**:
   ```bash
   # In the docker run command, added:
   python -m vllm.entrypoints.openai.api_server
   ```

3. **Fixed GPU Count Detection**:
   ```bash
   # Old (was counting wrong)
   gpu_count=$(rocm-smi --showid | grep -c "GPU" || echo "0")
   
   # New (counts correctly)
   gpu_count=$(rocm-smi --showid | grep -c "^GPU\[" || echo "0")
   ```

## Available AMD Docker Images

Browse tags at: https://hub.docker.com/r/rocm/vllm/tags

### Stable Options:
- `rocm/vllm:rocm6.4.1_vllm_0.10.1_20250909` - For ROCm 6.4.x
- `rocm/vllm:rocm6.2_ubuntu22.04_py3.10_vllm_0.6.3` - For ROCm 6.2.x
- `rocm/vllm:rocm6.1.2_ubuntu22.04_py3.10_vllm` - For ROCm 6.1.x

### Version Compatibility:
| ROCm Version | Recommended Image Tag |
|-------------|----------------------|
| 6.4.x | `rocm6.4.1_vllm_0.10.1_20250909` |
| 6.2.x | `rocm6.2_ubuntu22.04_py3.10_vllm_0.6.3` |
| 6.1.x | `rocm6.1.2_ubuntu22.04_py3.10_vllm` |

## Quick Start with Fixed Script

1. **Use the fixed script**:
   ```bash
   chmod +x vllm_start_rocm_fixed.sh
   ./vllm_start_rocm_fixed.sh
   ```

2. **Or manually with correct command**:
   ```bash
   docker run \
     --device=/dev/dri \
     --device=/dev/kfd \
     --group-add video \
     -v /opt/rocm:/opt/rocm:ro \
     -p 8081:8000 \
     rocm/vllm:rocm6.4.1_vllm_0.10.1_20250909 \
     python -m vllm.entrypoints.openai.api_server \
     --model NousResearch/Hermes-3-Llama-3.1-8B \
     --tensor-parallel-size 1
   ```

3. **Test the server**:
   ```bash
   chmod +x test_vllm_rocm.sh
   ./test_vllm_rocm.sh
   ```

## Configuration for Dual RX 7900 XTX

For your dual GPU setup, use these settings in `vllm_rocm.conf`:

### Single GPU Mode (Recommended to start):
```bash
HIP_VISIBLE_DEVICES="0"
TENSOR_PARALLEL_SIZE="1"
MODEL_ID="NousResearch/Hermes-3-Llama-3.1-8B"
```

### Dual GPU Mode (For larger models):
```bash
HIP_VISIBLE_DEVICES="0,1"
TENSOR_PARALLEL_SIZE="2"
MODEL_ID="NousResearch/Hermes-4-14B"
```

## Monitoring Your GPUs

```bash
# Real-time monitoring
watch -n 1 rocm-smi

# Check specific stats
rocm-smi --showuse     # Utilization
rocm-smi --showtemp    # Temperature
rocm-smi --showpower   # Power usage
rocm-smi --showmeminfo vram  # Memory usage
```

## Troubleshooting

### If server fails to start:
1. Check container logs:
   ```bash
   docker logs vllm-rocm-server
   ```

2. Verify GPU access:
   ```bash
   docker run --rm --device=/dev/kfd --device=/dev/dri \
     rocm/vllm:latest rocminfo
   ```

3. Try with override for RX 7900 XTX:
   ```bash
   export HSA_OVERRIDE_GFX_VERSION=11.0.0
   ```

### If out of memory:
- Reduce `GPU_MEMORY_UTILIZATION` to 0.85
- Use smaller model or reduce `MODEL_LENGTH`
- Enable tensor parallelism for multi-GPU

## Summary

The main issue was that AMD's Docker images need the full Python command, not just the arguments. The fixed script (`vllm_start_rocm_fixed.sh`) handles this correctly and should work with your dual RX 7900 XTX setup!
