#!/bin/bash
# Enhanced vLLM Server Startup Script for ROCm (AMD GPUs)
# Updated for AMD-maintained rocm/vllm Docker images
# =========================================================

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration file support
CONFIG_FILE="${CONFIG_FILE:-/opt/inference/config/vllm_rocm.conf}"
if [[ -f "$CONFIG_FILE" ]]; then
    echo "Loading configuration from $CONFIG_FILE"
    source "$CONFIG_FILE"
fi

# Log configuration
LOG_DIR="${LOG_DIR:-/opt/inference/logs}"
LOG_FILE="${LOG_DIR}/vllm_rocm_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$LOG_DIR"

# Function for colored output
log_info() { echo -e "${GREEN}[INFO]${NC} $1" | tee -a ${LOG_FILE}; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a ${LOG_FILE}; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a ${LOG_FILE}; }
log_debug() { echo -e "${BLUE}[DEBUG]${NC} $1" | tee -a ${LOG_FILE}; }
log_rocm() { echo -e "${MAGENTA}[ROCm]${NC} $1" | tee -a ${LOG_FILE}; }

# Model configuration with defaults
MODEL_ID="${MODEL_ID:-NousResearch/Hermes-3-Llama-3.1-8B}"
MODEL_LENGTH="${MODEL_LENGTH:-8192}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.90}"
TENSOR_PARALLEL_SIZE="${TENSOR_PARALLEL_SIZE:-1}"
PIPELINE_PARALLEL_SIZE="${PIPELINE_PARALLEL_SIZE:-1}"
MAX_NUM_SEQS="${MAX_NUM_SEQS:-64}"
MAX_NUM_BATCHED_TOKENS="${MAX_NUM_BATCHED_TOKENS:-}"

# Server configuration
VLLM_PORT="${VLLM_PORT:-8081}"
VLLM_HOST="${VLLM_HOST:-0.0.0.0}"
VLLM_LOGGING_LEVEL="${VLLM_LOGGING_LEVEL:-INFO}"
CONTAINER_NAME="${CONTAINER_NAME:-vllm-rocm-server}"
RESTART_POLICY="${RESTART_POLICY:-unless-stopped}"

# ROCm specific settings - Updated for AMD's Docker Hub
# AMD now maintains images at rocm/vllm instead of vllm/vllm-rocm
IMAGE_REGISTRY="${IMAGE_REGISTRY:-rocm}"  # 'rocm' for AMD's registry
IMAGE_NAME="${IMAGE_NAME:-vllm}"
IMAGE_TAG="${IMAGE_TAG:-rocm6.2_ubuntu22.04_py3.10_vllm_0.6.3}"  # Default stable

# Common AMD image tags:
# rocm6.2_ubuntu22.04_py3.10_vllm_0.6.3
# rocm6.4.1_vllm_0.10.1_20250909
# rocm6.1.2_ubuntu22.04_py3.10_vllm

ROCM_VERSION="${ROCM_VERSION:-6.2}"
HIP_VISIBLE_DEVICES="${HIP_VISIBLE_DEVICES:-0}"
HSA_OVERRIDE_GFX_VERSION="${HSA_OVERRIDE_GFX_VERSION:-}"

# vLLM settings
TOOL_CALL_PARSER="${TOOL_CALL_PARSER:-hermes}"
ENABLE_AUTO_TOOL_CHOICE="${ENABLE_AUTO_TOOL_CHOICE:-true}"
ENABLE_CHUNKED_PREFILL="${ENABLE_CHUNKED_PREFILL:-false}"

# Performance tuning
BLOCK_SIZE="${BLOCK_SIZE:-16}"
NUM_SCHEDULER_STEPS="${NUM_SCHEDULER_STEPS:-1}"
ENABLE_PREFIX_CACHING="${ENABLE_PREFIX_CACHING:-false}"
KV_CACHE_DTYPE="${KV_CACHE_DTYPE:-auto}"

# Cache and data paths
HF_CACHE="${HF_CACHE:-/home/shaun/.cache/huggingface}"
VLLM_CACHE="${VLLM_CACHE:-/opt/inference/cache}"
DOWNLOAD_DIR="${DOWNLOAD_DIR:-/opt/inference/downloads}"

# Create necessary directories
mkdir -p "$VLLM_CACHE" "$DOWNLOAD_DIR"

# Function to check if container is already running
check_existing_container() {
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log_warn "Container '${CONTAINER_NAME}' already exists"
        read -p "Do you want to remove it and start fresh? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Stopping and removing existing container..."
            docker stop "${CONTAINER_NAME}" 2>/dev/null || true
            docker rm "${CONTAINER_NAME}" 2>/dev/null || true
        else
            log_error "Exiting. Please remove or rename the existing container."
            exit 1
        fi
    fi
}

# Function to detect and validate AMD GPUs
check_amd_gpu() {
    log_rocm "Checking for AMD GPUs..."
    
    # Check if rocm-smi is available
    if command -v rocm-smi &> /dev/null; then
        log_rocm "Found rocm-smi"
        
        # Get GPU information
        local gpu_info=$(rocm-smi --showid 2>/dev/null || true)
        if [[ -n "$gpu_info" ]]; then
            log_rocm "AMD GPUs detected:"
            echo "$gpu_info" | tee -a ${LOG_FILE}
            
            # Count GPUs (fixed the count logic)
            local gpu_count=$(rocm-smi --showid 2>/dev/null | grep -c "^GPU\[" || echo "0")
            log_rocm "Found ${gpu_count} AMD GPU(s)"
            
            # Verify tensor parallel size
            if [[ $TENSOR_PARALLEL_SIZE -gt $gpu_count ]]; then
                log_error "Tensor parallel size ($TENSOR_PARALLEL_SIZE) exceeds available GPUs ($gpu_count)"
                exit 1
            fi
        else
            log_warn "rocm-smi found but no GPUs detected"
        fi
    else
        log_warn "rocm-smi not found. Checking for ROCm installation..."
        
        # Check if ROCm is installed via other methods
        if [[ -d "/opt/rocm" ]]; then
            log_rocm "ROCm installation found at /opt/rocm"
            log_warn "rocm-smi not in PATH. Add /opt/rocm/bin to PATH"
        else
            log_error "ROCm not detected. Please install ROCm drivers."
            log_info "Visit: https://rocm.docs.amd.com/en/latest/deploy/linux/index.html"
            exit 1
        fi
    fi
    
    # Check for specific GPU compatibility
    if command -v rocminfo &> /dev/null; then
        log_rocm "Checking GPU compatibility with rocminfo..."
        rocminfo | grep -E "Name:|Marketing Name:" | head -5 | tee -a ${LOG_FILE}
    fi
}

# Function to check Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running or you don't have permission."
        exit 1
    fi
    
    # Check if Docker has access to GPU devices
    if ! docker info 2>/dev/null | grep -q "Runtimes.*rocm\|nvidia"; then
        log_warn "Docker may not have GPU runtime support"
        log_info "You may need to install docker-ce and rocm-docker packages"
    fi
}

# Function to pull ROCm-specific image
pull_rocm_image() {
    local full_image="${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    
    log_rocm "Pulling ROCm-specific vLLM image: ${full_image}"
    if docker pull "${full_image}"; then
        log_info "Successfully pulled ROCm image"
        return 0
    else
        log_warn "Failed to pull image ${full_image}"
        
        # Try some common alternative tags
        log_info "Trying alternative image tags..."
        local alt_tags=(
            "rocm6.2_ubuntu22.04_py3.10_vllm_0.6.3"
            "rocm6.1.2_ubuntu22.04_py3.10_vllm"
            "latest"
        )
        
        for alt_tag in "${alt_tags[@]}"; do
            local alt_image="${IMAGE_REGISTRY}/${IMAGE_NAME}:${alt_tag}"
            log_info "Trying ${alt_image}"
            if docker pull "${alt_image}"; then
                IMAGE_TAG="${alt_tag}"
                log_info "Successfully pulled with tag: ${alt_tag}"
                return 0
            fi
        done
        
        log_error "Could not pull any ROCm vLLM image"
        log_info "Available images at: https://hub.docker.com/r/rocm/vllm/tags"
        return 1
    fi
}

# Function to get AMD GPU device list
get_amd_gpu_devices() {
    local devices=""
    
    # Method 1: Use /dev/dri devices
    if [[ -d /dev/dri ]]; then
        for device in /dev/dri/card* /dev/dri/renderD*; do
            if [[ -e "$device" ]]; then
                devices+=" --device=$device"
            fi
        done
    fi
    
    # Method 2: Use /dev/kfd for compute
    if [[ -e /dev/kfd ]]; then
        devices+=" --device=/dev/kfd"
    fi
    
    echo "$devices"
}

# Function to build Docker run command for ROCm
build_docker_command() {
    local cmd="docker run"
    
    # ROCm GPU access (different from NVIDIA's --gpus all)
    local gpu_devices=$(get_amd_gpu_devices)
    if [[ -n "$gpu_devices" ]]; then
        cmd+=" $gpu_devices"
    else
        log_warn "No GPU devices found, container may not have GPU access"
    fi
    
    # Security and capabilities
    cmd+=" --cap-add=SYS_PTRACE"
    cmd+=" --security-opt seccomp=unconfined"
    cmd+=" --group-add video"
    
    # Network and restart
    cmd+=" --restart ${RESTART_POLICY}"
    cmd+=" -p ${VLLM_PORT}:8000"
    
    # Volume mounts
    cmd+=" -v ${HF_CACHE}:/root/.cache/huggingface"
    cmd+=" -v ${VLLM_CACHE}:/data"
    cmd+=" -v ${DOWNLOAD_DIR}:/downloads"
    
    # ROCm library paths (important!)
    if [[ -d /opt/rocm ]]; then
        cmd+=" -v /opt/rocm:/opt/rocm:ro"
    fi
    
    # Environment variables for ROCm
    cmd+=" --env VLLM_LOGGING_LEVEL=${VLLM_LOGGING_LEVEL}"
    cmd+=" --env HF_HUB_OFFLINE=${HF_HUB_OFFLINE:-0}"
    cmd+=" --env HIP_VISIBLE_DEVICES=${HIP_VISIBLE_DEVICES}"
    cmd+=" --env ROCR_VISIBLE_DEVICES=${HIP_VISIBLE_DEVICES}"
    cmd+=" --env GPU_DEVICE_ORDINAL=${HIP_VISIBLE_DEVICES}"
    
    # ROCm compatibility settings
    if [[ -n "$HSA_OVERRIDE_GFX_VERSION" ]]; then
        cmd+=" --env HSA_OVERRIDE_GFX_VERSION=${HSA_OVERRIDE_GFX_VERSION}"
    fi
    
    # Additional ROCm environment variables
    cmd+=" --env ROCM_VERSION=${ROCM_VERSION}"
    cmd+=" --env HCC_AMDGPU_TARGET=gfx90a,gfx908,gfx906,gfx1030,gfx1100"
    
    # Optional API key
    if [[ -n "${API_KEY:-}" ]]; then
        cmd+=" --env VLLM_API_KEY=${API_KEY}"
    fi
    
    # Container settings
    cmd+=" --ipc=host"
    cmd+=" --ulimit memlock=-1"
    cmd+=" --ulimit stack=67108864"
    cmd+=" --name ${CONTAINER_NAME}"
    cmd+=" -d"
    
    # Use the full image name
    local full_image="${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    cmd+=" ${full_image}"
    
    # IMPORTANT: AMD's rocm/vllm images need the full Python command
    # Not just the arguments like standard vLLM images
    cmd+=" python -m vllm.entrypoints.openai.api_server"
    
    # Now add vLLM arguments
    cmd+=" --host ${VLLM_HOST}"
    cmd+=" --port 8000"
    cmd+=" --model ${MODEL_ID}"
    cmd+=" --trust-remote-code"
    cmd+=" --dtype auto"
    cmd+=" --max-model-len ${MODEL_LENGTH}"
    cmd+=" --gpu-memory-utilization ${GPU_MEMORY_UTILIZATION}"
    cmd+=" --tensor-parallel-size ${TENSOR_PARALLEL_SIZE}"
    cmd+=" --max-num-seqs ${MAX_NUM_SEQS}"
    
    # Only add tool parser options if the image supports them (0.5.4+)
    # Check image tag to determine version
    if [[ "$IMAGE_TAG" == *"0.6"* ]] || [[ "$IMAGE_TAG" == *"0.10"* ]] || [[ "$IMAGE_TAG" == *"0.11"* ]]; then
        cmd+=" --tool-call-parser ${TOOL_CALL_PARSER}"
        if [[ "$ENABLE_AUTO_TOOL_CHOICE" == "true" ]]; then
            cmd+=" --enable-auto-tool-choice"
        fi
    else
        log_warn "Tool calling may not be supported in this vLLM version"
    fi
    
    # Performance options
    if [[ "$ENABLE_PREFIX_CACHING" == "true" ]]; then
        cmd+=" --enable-prefix-caching"
    fi
    
    if [[ "$ENABLE_CHUNKED_PREFILL" == "true" ]]; then
        cmd+=" --enable-chunked-prefill"
    fi
    
    # Optional parameters
    if [[ -n "$MAX_NUM_BATCHED_TOKENS" ]]; then
        cmd+=" --max-num-batched-tokens ${MAX_NUM_BATCHED_TOKENS}"
    fi
    
    echo "$cmd"
}

# Function to wait for server to be ready
wait_for_server() {
    local max_attempts=60
    local attempt=0
    
    log_info "Waiting for vLLM ROCm server to be ready..."
    
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:${VLLM_PORT}/health" | grep -q "200"; then
            log_info "vLLM ROCm server is ready!"
            return 0
        fi
        
        attempt=$((attempt + 1))
        if [[ $((attempt % 10)) -eq 0 ]]; then
            log_info "Still waiting... (${attempt}/${max_attempts})"
            
            # Show last few log lines to help debug
            if [[ $attempt -eq 30 ]]; then
                log_warn "Server is taking longer than expected. Checking logs..."
                docker logs --tail 10 "${CONTAINER_NAME}" 2>&1 | tee -a ${LOG_FILE}
            fi
        fi
        sleep 2
    done
    
    log_error "vLLM server failed to start after ${max_attempts} attempts"
    return 1
}

# Function to display AMD GPU stats
display_gpu_stats() {
    log_rocm "GPU Statistics:"
    
    if command -v rocm-smi &> /dev/null; then
        # Temperature
        rocm-smi -t 2>/dev/null | grep -E "GPU|Temp" | head -10 | tee -a ${LOG_FILE}
        
        # Memory usage
        rocm-smi --showmeminfo vram 2>/dev/null | grep -E "GPU|Used|Free" | head -10 | tee -a ${LOG_FILE}
        
        # Power
        rocm-smi -P 2>/dev/null | grep -E "GPU|Power" | head -10 | tee -a ${LOG_FILE}
    else
        log_warn "rocm-smi not available for GPU stats"
    fi
}

# Function to display server info
display_server_info() {
    log_info "==============================================="
    log_rocm "vLLM ROCm Server Started Successfully!"
    log_info "==============================================="
    log_info "Model: ${MODEL_ID}"
    log_info "Server URL: http://localhost:${VLLM_PORT}"
    log_info "Container: ${CONTAINER_NAME}"
    log_info "GPU Type: AMD ROCm"
    log_info "ROCm Version: ${ROCM_VERSION}"
    log_info "HIP Devices: ${HIP_VISIBLE_DEVICES}"
    log_info "Docker Image: ${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    log_info "==============================================="
    
    # Display GPU stats
    display_gpu_stats
    
    # Test the API
    log_info "Testing API endpoint..."
    if curl -s "http://localhost:${VLLM_PORT}/v1/models" | grep -q "model"; then
        log_info "✅ API test successful!"
        
        # Show model details
        log_info "Available models:"
        curl -s "http://localhost:${VLLM_PORT}/v1/models" | python3 -m json.tool 2>/dev/null | grep '"id"' | head -5
    else
        log_warn "⚠️  API test failed or returned unexpected response"
    fi
}

# Function to show ROCm-specific tips
show_rocm_tips() {
    cat << EOF | tee -a ${LOG_FILE}

📚 ROCm-Specific Tips:
======================

1. Monitor GPU Usage:
   rocm-smi --showuse
   watch -n 1 rocm-smi

2. Check Logs:
   docker logs -f ${CONTAINER_NAME}

3. Test Inference:
   curl http://localhost:${VLLM_PORT}/v1/completions \\
     -H "Content-Type: application/json" \\
     -d '{
       "model": "${MODEL_ID}",
       "prompt": "Hello world",
       "max_tokens": 100
     }'

4. Common Issues:
   - If using RX 7900 XTX with older images, you may need:
     export HSA_OVERRIDE_GFX_VERSION=11.0.0
   
   - For multi-GPU, ensure HIP_VISIBLE_DEVICES is set correctly:
     HIP_VISIBLE_DEVICES=0,1 for 2 GPUs

5. AMD Docker Hub:
   Browse available images at:
   https://hub.docker.com/r/rocm/vllm/tags

EOF
}

# Main execution
main() {
    log_rocm "Starting vLLM ROCm server setup at $(date)"
    log_info "Configuration:"
    log_info "  Model: ${MODEL_ID}"
    log_info "  Port: ${VLLM_PORT}"
    log_info "  Image: ${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    log_info "  ROCm Version: ${ROCM_VERSION}"
    log_info "  HIP Devices: ${HIP_VISIBLE_DEVICES}"
    
    # Pre-flight checks
    check_docker
    check_amd_gpu
    check_existing_container
    pull_rocm_image
    
    # Build and execute Docker command
    local docker_cmd=$(build_docker_command)
    
    log_info "Starting ROCm container..."
    log_debug "Docker command: ${docker_cmd}"
    
    if container_id=$(eval "${docker_cmd}" 2>&1); then
        log_info "Container started with ID: ${container_id:0:12}"
        
        # Wait for server to be ready
        if wait_for_server; then
            display_server_info
            show_rocm_tips
        else
            log_error "Server health check failed"
            log_info "Checking container logs..."
            docker logs --tail 50 "${CONTAINER_NAME}"
            exit 1
        fi
    else
        log_error "Failed to start container: ${container_id}"
        log_info "This might be due to:"
        log_info "  1. Incorrect image entrypoint - try a different image tag"
        log_info "  2. GPU compatibility issues - check HSA_OVERRIDE_GFX_VERSION"
        log_info "  3. Missing dependencies - ensure ROCm is properly installed"
        exit 1
    fi
    
    log_rocm "Setup completed at $(date)"
}

# Run main function
main "$@"
