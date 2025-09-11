# 🎮 vLLM GPU Support Guide: NVIDIA vs AMD

## Quick Comparison

| Feature | NVIDIA (CUDA) | AMD (ROCm) | Universal Script |
|---------|--------------|------------|------------------|
| **Auto-detection** | ✅ nvidia-smi | ✅ rocm-smi | ✅ Both |
| **Docker GPU Flag** | `--gpus all` | `--device=/dev/dri --device=/dev/kfd` | Auto-selects |
| **Image** | `vllm/vllm-openai` | `rocm/vllm` | Auto-selects |
| **Environment** | `CUDA_VISIBLE_DEVICES` | `HIP_VISIBLE_DEVICES` | Auto-configures |
| **Tool Calling** | ✅ Full support | ✅ Full support | ✅ Full support |
| **Performance** | Excellent | Very Good | Optimized for both |

## 🚀 Quick Start

### Option 1: Universal Script (Recommended)
Automatically detects your GPU type:

```bash
# Auto-detect and start
./vllm_start_universal.sh

# Force specific GPU type if needed
./vllm_start_universal.sh --force-nvidia
./vllm_start_universal.sh --force-amd
```

### Option 2: GPU-Specific Scripts

#### For NVIDIA GPUs:
```bash
./vllm_start_enhanced.sh
```

#### For AMD GPUs:
```bash
./vllm_start_rocm.sh
```

## 📋 Configuration Files

Each GPU type can have its own configuration:

| GPU Type | Config File | Container Name |
|----------|------------|----------------|
| NVIDIA | `/opt/inference/config/vllm.conf` | `vllm-server` |
| AMD | `/opt/inference/config/vllm_rocm.conf` | `vllm-rocm-server` |
| Intel | `/opt/inference/config/vllm_intel.conf` | `vllm-intel-server` |

## 🔧 AMD ROCm Specific Setup

### Supported AMD GPUs

| GPU | Architecture | Override Needed | Notes |
|-----|-------------|-----------------|-------|
| MI200 series | gfx90a | No | Best performance |
| MI100 | gfx908 | No | Datacenter GPU |
| MI50/60 | gfx906 | No | Older datacenter |
| RX 7900 XTX | gfx1100 | Sometimes | Consumer flagship |
| RX 7900 XT | gfx1101 | Sometimes | High-end consumer |
| RX 6900 XT | gfx1030 | Yes: `10.3.0` | Previous gen |
| RX 6800 XT | gfx1030 | Yes: `10.3.0` | Previous gen |

### ROCm Installation Check

```bash
# Check ROCm version
/opt/rocm/bin/rocminfo

# Check AMD GPUs
rocm-smi --showid

# Monitor GPU usage
watch -n 1 rocm-smi

# Check GPU temperature
rocm-smi -t

# Check memory usage
rocm-smi --showmeminfo vram
```

### ROCm Troubleshooting

#### GPU Not Detected
```bash
# Check kernel driver
lsmod | grep amdgpu

# Check devices
ls -la /dev/dri/
ls -la /dev/kfd

# Add user to video group
sudo usermod -a -G video $USER
sudo usermod -a -G render $USER
```

#### Compatibility Issues
```bash
# Set architecture override in config
HSA_OVERRIDE_GFX_VERSION="10.3.0"  # For RX 6000 series
HSA_OVERRIDE_GFX_VERSION="11.0.0"  # For RX 7000 series
```

#### Out of Memory
```bash
# Reduce memory utilization
GPU_MEMORY_UTILIZATION="0.80"

# Use FP16 cache
KV_CACHE_DTYPE="fp16"

# Reduce batch size
MAX_NUM_SEQS="32"
```

## 🔧 NVIDIA CUDA Specific Setup

### Supported NVIDIA GPUs

| GPU | Memory | Recommended Models | Notes |
|-----|--------|-------------------|-------|
| H100 | 80GB | Any size | Best performance |
| A100 | 40/80GB | Up to 70B | Datacenter |
| A6000 | 48GB | Up to 34B | Workstation |
| RTX 4090 | 24GB | Up to 13B | Consumer flagship |
| RTX 4080 | 16GB | Up to 7B | High-end consumer |
| RTX 3090 | 24GB | Up to 13B | Previous gen |

### CUDA Installation Check

```bash
# Check CUDA version
nvidia-smi

# Check CUDA toolkit
nvcc --version

# Monitor GPU usage
nvidia-smi dmon -s pucvmet

# Check GPU utilization
watch -n 1 nvidia-smi
```

### NVIDIA Troubleshooting

#### Driver Issues
```bash
# Check driver version
nvidia-smi --query-gpu=driver_version --format=csv,noheader

# Minimum driver for vLLM
# CUDA 11.8: Driver 450.80.02+
# CUDA 12.1: Driver 525.60.13+
```

#### Multi-GPU Setup
```bash
# Use specific GPUs
CUDA_VISIBLE_DEVICES="0,1"

# Tensor parallel for 2 GPUs
TENSOR_PARALLEL_SIZE="2"

# Pipeline parallel for 4 GPUs
TENSOR_PARALLEL_SIZE="2"
PIPELINE_PARALLEL_SIZE="2"
```

## 📊 Performance Comparison

### Throughput (tokens/second)

| Model | RTX 4090 | RX 7900 XTX | A100 40GB | MI200 |
|-------|----------|-------------|-----------|--------|
| 7B | ~2000 | ~1800 | ~3000 | ~2800 |
| 13B | ~1000 | ~900 | ~1800 | ~1700 |
| 34B | OOM | OOM | ~800 | ~750 |

*Note: Actual performance depends on batch size, sequence length, and optimization settings*

### Memory Usage

| Model Size | FP16 Memory | INT8 Memory | INT4 Memory |
|------------|-------------|-------------|-------------|
| 7B | ~14 GB | ~7 GB | ~3.5 GB |
| 13B | ~26 GB | ~13 GB | ~6.5 GB |
| 34B | ~68 GB | ~34 GB | ~17 GB |
| 70B | ~140 GB | ~70 GB | ~35 GB |

## ⚙️ Optimization Tips

### For NVIDIA GPUs
```bash
# Maximum throughput
GPU_MEMORY_UTILIZATION="0.95"
ENABLE_PREFIX_CACHING="true"
MAX_NUM_SEQS="256"

# Low latency
GPU_MEMORY_UTILIZATION="0.85"
MAX_NUM_SEQS="16"
NUM_SCHEDULER_STEPS="1"
```

### For AMD GPUs
```bash
# Maximum throughput (MI200)
GPU_MEMORY_UTILIZATION="0.92"
KV_CACHE_DTYPE="fp16"
MAX_NUM_SEQS="128"

# Low latency (RX 7900 XTX)
GPU_MEMORY_UTILIZATION="0.80"
MAX_NUM_SEQS="16"
BLOCK_SIZE="8"
```

## 🐳 Docker Image Differences

### NVIDIA Images
```bash
# Official vLLM CUDA images
vllm/vllm-openai:latest       # Latest stable
vllm/vllm-openai:v0.11.0      # Specific version
vllm/vllm-openai:nightly      # Development build
```

### AMD ROCm Images
```bash
# Official vLLM ROCm images
rocm/vllm:latest          # Latest stable
rocm/vllm:rocm-v0.11.0    # Specific version
rocm/vllm:rocm6.0         # ROCm 6.0 specific
```

## 🔍 Monitoring Commands

### Universal Monitoring Script
Works with both NVIDIA and AMD:
```bash
./vllm_monitor.sh dashboard
./vllm_monitor.sh monitor
./vllm_monitor.sh benchmark
```

### GPU-Specific Monitoring

#### NVIDIA
```bash
# Real-time monitoring
nvidia-smi dmon -s pucvmet

# Power usage
nvidia-smi --query-gpu=power.draw --format=csv --loop=1

# Memory usage
nvidia-smi --query-gpu=memory.used,memory.total --format=csv --loop=1
```

#### AMD
```bash
# Real-time monitoring
rocm-smi --showuse
rocm-smi --showtemp
rocm-smi --showpower

# Detailed info
rocm-smi --showallinfo
```

## 🎯 Choosing the Right Setup

### Use NVIDIA if you have:
- ✅ RTX 3090, 4090, A100, H100
- ✅ CUDA 11.8+ installed
- ✅ Need maximum ecosystem support
- ✅ Want to use NVIDIA-specific optimizations

### Use AMD ROCm if you have:
- ✅ RX 6900 XT, 7900 XTX, MI100, MI200
- ✅ ROCm 5.7+ installed
- ✅ Want open-source stack
- ✅ Need cost-effective solution

### Use Universal Script if:
- ✅ You're not sure about your GPU
- ✅ You switch between systems
- ✅ You want automatic configuration
- ✅ You manage multiple servers

## 📝 Environment Variables Reference

### Common Variables
```bash
MODEL_ID                    # Model to load
MODEL_LENGTH               # Max sequence length
GPU_MEMORY_UTILIZATION     # GPU memory to use (0.0-1.0)
TENSOR_PARALLEL_SIZE       # Number of GPUs for tensor parallel
VLLM_PORT                  # Server port
CONTAINER_NAME             # Docker container name
```

### NVIDIA-Specific
```bash
CUDA_VISIBLE_DEVICES       # GPU selection (0,1,2...)
CUDA_LAUNCH_BLOCKING       # Debugging (set to 1)
```

### AMD-Specific
```bash
HIP_VISIBLE_DEVICES        # GPU selection (0,1,2...)
ROCR_VISIBLE_DEVICES       # Alternative GPU selection
HSA_OVERRIDE_GFX_VERSION   # Architecture override
GPU_DEVICE_ORDINAL         # GPU ordering
```

## 🚨 Common Issues and Solutions

### Issue: "GPU not found"
**NVIDIA**: Install NVIDIA drivers and CUDA toolkit
**AMD**: Install ROCm and add user to video/render groups
**Both**: Check Docker GPU runtime is installed

### Issue: "Out of memory"
**Both**: Reduce `GPU_MEMORY_UTILIZATION` to 0.80
**Both**: Use quantized models (AWQ, GPTQ)
**AMD**: Set `KV_CACHE_DTYPE="fp16"`

### Issue: "Slow inference"
**Both**: Enable `ENABLE_PREFIX_CACHING="true"`
**NVIDIA**: Check GPU boost clocks
**AMD**: Verify GPU clocks with `rocm-smi --showclocks`

### Issue: "Tool calling not working"
**Both**: Ensure `--tool-call-parser hermes` is set
**Both**: Verify model supports tool calling
**Both**: Check vLLM version is 0.11.0+

## 🎉 Summary

The enhanced vLLM scripts now support both NVIDIA and AMD GPUs with:
- ✅ **Automatic GPU detection** in universal script
- ✅ **Optimized configurations** for each GPU type
- ✅ **Full tool calling support** on both platforms
- ✅ **Comprehensive monitoring** for both GPU types
- ✅ **Easy switching** between GPU vendors

Choose the script that matches your needs:
- `vllm_start_universal.sh` - Auto-detects and configures
- `vllm_start_enhanced.sh` - NVIDIA-optimized
- `vllm_start_rocm.sh` - AMD ROCm-optimized

All scripts integrate perfectly with your Chat with Tools framework!
