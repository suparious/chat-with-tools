#!/bin/bash
# Universal vLLM Server Startup Script - Auto-detects NVIDIA/AMD GPUs
# ====================================================================

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Function for colored output
log_info() { echo -e "${GREEN}[INFO]${NC} $1" | tee -a ${LOG_FILE}; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a ${LOG_FILE}; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a ${LOG_FILE}; }
log_debug() { echo -e "${BLUE}[DEBUG]${NC} $1" | tee -a ${LOG_FILE}; }
log_gpu() { echo -e "${CYAN}[GPU]${NC} $1" | tee -a ${LOG_FILE}; }

# Log configuration
LOG_DIR="${LOG_DIR:-/opt/inference/logs}"
LOG_FILE="${LOG_DIR}/vllm_universal_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$LOG_DIR"

# Detect GPU type
detect_gpu_type() {
    local gpu_type="none"
    
    log_gpu "Detecting GPU type..."
    
    # Check for NVIDIA GPUs
    if command -v nvidia-smi &> /dev/null; then
        if nvidia-smi &> /dev/null; then
            gpu_type="nvidia"
            log_gpu "Detected NVIDIA GPU(s)"
            nvidia-smi --query-gpu=name --format=csv,noheader | while read gpu; do
                log_gpu "  - $gpu"
            done
        fi
    fi
    
    # Check for AMD GPUs (only if NVIDIA not found)
    if [[ "$gpu_type" == "none" ]]; then
        if command -v rocm-smi &> /dev/null; then
            if rocm-smi --showid &> /dev/null; then
                gpu_type="amd"
                log_gpu "Detected AMD GPU(s)"
                rocm-smi --showproductname 2>/dev/null | grep -E "Card series|GPU" | while read line; do
                    log_gpu "  - $line"
                done
            fi
        elif command -v rocminfo &> /dev/null; then
            if rocminfo | grep -q "Device Type.*GPU"; then
                gpu_type="amd"
                log_gpu "Detected AMD GPU(s) via rocminfo"
            fi
        elif [[ -e /dev/kfd ]]; then
            gpu_type="amd"
            log_gpu "Detected AMD GPU support (KFD driver present)"
        fi
    fi
    
    # Check for Intel GPUs (future support)
    if [[ "$gpu_type" == "none" ]]; then
        if [[ -e /dev/dri/renderD128 ]] && command -v clinfo &> /dev/null; then
            if clinfo 2>/dev/null | grep -q "Intel"; then
                gpu_type="intel"
                log_gpu "Detected Intel GPU(s)"
                log_warn "Intel GPU support is experimental in vLLM"
            fi
        fi
    fi
    
    echo "$gpu_type"
}

# Load configuration based on GPU type
load_configuration() {
    local gpu_type="$1"
    local config_file=""
    
    # Determine config file
    case "$gpu_type" in
        nvidia)
            config_file="${CONFIG_FILE:-/opt/inference/config/vllm.conf}"
            DEFAULT_IMAGE_TAG="v0.11.0"
            DEFAULT_CONTAINER_NAME="vllm-server"
            ;;
        amd)
            config_file="${CONFIG_FILE:-/opt/inference/config/vllm_rocm.conf}"
            DEFAULT_IMAGE_TAG="rocm-v0.11.0"
            DEFAULT_CONTAINER_NAME="vllm-rocm-server"
            ;;
        intel)
            config_file="${CONFIG_FILE:-/opt/inference/config/vllm_intel.conf}"
            DEFAULT_IMAGE_TAG="intel-v0.11.0"
            DEFAULT_CONTAINER_NAME="vllm-intel-server"
            ;;
        *)
            log_error "No supported GPU detected!"
            log_info "Supported GPUs: NVIDIA (CUDA), AMD (ROCm), Intel (experimental)"
            exit 1
            ;;
    esac
    
    # Load config if exists
    if [[ -f "$config_file" ]]; then
        log_info "Loading configuration from $config_file"
        source "$config_file"
    else
        log_warn "Config file not found: $config_file"
        log_info "Using default settings"
    fi
    
    # Set defaults if not configured
    MODEL_ID="${MODEL_ID:-Orion-zhen/DeepHermes-3-Llama-3-8B-Preview-AWQ}"
    MODEL_LENGTH="${MODEL_LENGTH:-14992}"
    GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.90}"
    TENSOR_PARALLEL_SIZE="${TENSOR_PARALLEL_SIZE:-1}"
    MAX_NUM_SEQS="${MAX_NUM_SEQS:-64}"
    VLLM_PORT="${VLLM_PORT:-8081}"
    VLLM_LOGGING_LEVEL="${VLLM_LOGGING_LEVEL:-INFO}"
    IMAGE_TAG="${IMAGE_TAG:-$DEFAULT_IMAGE_TAG}"
    CONTAINER_NAME="${CONTAINER_NAME:-$DEFAULT_CONTAINER_NAME}"
    TOOL_CALL_PARSER="${TOOL_CALL_PARSER:-hermes}"
    ENABLE_AUTO_TOOL_CHOICE="${ENABLE_AUTO_TOOL_CHOICE:-true}"
}

# Check Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running or you don't have permission."
        exit 1
    fi
}

# Check existing container
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

# Get GPU count based on type
get_gpu_count() {
    local gpu_type="$1"
    local count=0
    
    case "$gpu_type" in
        nvidia)
            count=$(nvidia-smi --query-gpu=count --format=csv,noheader | head -1)
            ;;
        amd)
            if command -v rocm-smi &> /dev/null; then
                count=$(rocm-smi --showid | grep -c "GPU" || echo "1")
            else
                count=1  # Assume at least 1 if detection worked
            fi
            ;;
        intel)
            count=1  # Intel GPU support is typically single GPU
            ;;
    esac
    
    echo "$count"
}

# Build Docker command based on GPU type
build_docker_command() {
    local gpu_type="$1"
    local cmd="docker run"
    
    # GPU-specific flags
    case "$gpu_type" in
        nvidia)
            cmd+=" --gpus all"
            cmd+=" --privileged"
            local image_name="vllm/vllm-openai:${IMAGE_TAG}"
            ;;
        amd)
            # ROCm requires device mapping
            if [[ -d /dev/dri ]]; then
                for device in /dev/dri/card* /dev/dri/renderD*; do
                    [[ -e "$device" ]] && cmd+=" --device=$device"
                done
            fi
            [[ -e /dev/kfd ]] && cmd+=" --device=/dev/kfd"
            
            cmd+=" --cap-add=SYS_PTRACE"
            cmd+=" --security-opt seccomp=unconfined"
            cmd+=" --group-add video"
            
            # Mount ROCm libraries
            [[ -d /opt/rocm ]] && cmd+=" -v /opt/rocm:/opt/rocm:ro"
            
            local image_name="rocm/vllm:${IMAGE_TAG}"
            ;;
        intel)
            # Intel GPU support (experimental)
            cmd+=" --device=/dev/dri"
            cmd+=" --group-add video"
            local image_name="vllm/vllm-openai:${IMAGE_TAG}"  # May need special image
            ;;
    esac
    
    # Common flags
    cmd+=" --restart unless-stopped"
    cmd+=" -p ${VLLM_PORT}:8000"
    cmd+=" -v ${HF_CACHE:-$HOME/.cache/huggingface}:/root/.cache/huggingface"
    cmd+=" -v ${VLLM_CACHE:-/opt/inference/cache}:/data"
    cmd+=" --env VLLM_LOGGING_LEVEL=${VLLM_LOGGING_LEVEL}"
    
    # GPU-specific environment variables
    case "$gpu_type" in
        nvidia)
            cmd+=" --env CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-all}"
            ;;
        amd)
            cmd+=" --env HIP_VISIBLE_DEVICES=${HIP_VISIBLE_DEVICES:-0}"
            cmd+=" --env ROCR_VISIBLE_DEVICES=${HIP_VISIBLE_DEVICES:-0}"
            [[ -n "${HSA_OVERRIDE_GFX_VERSION:-}" ]] && \
                cmd+=" --env HSA_OVERRIDE_GFX_VERSION=${HSA_OVERRIDE_GFX_VERSION}"
            ;;
        intel)
            cmd+=" --env SYCL_DEVICE_FILTER=gpu"
            ;;
    esac
    
    # Container settings
    cmd+=" --ipc=host"
    cmd+=" --ulimit memlock=-1"
    cmd+=" --ulimit stack=67108864"
    cmd+=" --name ${CONTAINER_NAME}"
    cmd+=" -d"
    cmd+=" ${image_name}"
    
    # vLLM arguments
    cmd+=" --model ${MODEL_ID}"
    cmd+=" --trust-remote-code"
    cmd+=" --dtype auto"
    cmd+=" --max-model-len ${MODEL_LENGTH}"
    cmd+=" --gpu-memory-utilization ${GPU_MEMORY_UTILIZATION}"
    cmd+=" --tensor-parallel-size ${TENSOR_PARALLEL_SIZE}"
    cmd+=" --max-num-seqs ${MAX_NUM_SEQS}"
    cmd+=" --tool-call-parser ${TOOL_CALL_PARSER}"
    
    [[ "$ENABLE_AUTO_TOOL_CHOICE" == "true" ]] && cmd+=" --enable-auto-tool-choice"
    
    echo "$cmd"
}

# Pull appropriate image
pull_image() {
    local gpu_type="$1"
    local image_name=""
    
    case "$gpu_type" in
        nvidia)
            image_name="vllm/vllm-openai:${IMAGE_TAG}"
            ;;
        amd)
            image_name="rocm/vllm:${IMAGE_TAG}"
            ;;
        intel)
            image_name="vllm/vllm-openai:${IMAGE_TAG}"
            log_warn "Intel GPU support may require custom image"
            ;;
    esac
    
    log_info "Pulling image: ${image_name}"
    if docker pull "${image_name}"; then
        log_info "Successfully pulled image"
    else
        log_warn "Failed to pull image, will use local if available"
    fi
}

# Wait for server
wait_for_server() {
    local max_attempts=60
    local attempt=0
    
    log_info "Waiting for vLLM server to be ready..."
    
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -s -o /dev/null -w "%{http_code}" "http://localhost:${VLLM_PORT}/health" | grep -q "200"; then
            log_info "vLLM server is ready!"
            return 0
        fi
        
        attempt=$((attempt + 1))
        [[ $((attempt % 10)) -eq 0 ]] && log_info "Still waiting... (${attempt}/${max_attempts})"
        sleep 2
    done
    
    log_error "Server failed to start"
    return 1
}

# Display GPU stats
display_gpu_stats() {
    local gpu_type="$1"
    
    log_gpu "GPU Statistics:"
    
    case "$gpu_type" in
        nvidia)
            nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu \
                       --format=csv,noheader | while IFS=',' read -r idx name util mem_used mem_total temp; do
                echo "  GPU $idx: $name - Util: ${util}, Mem: ${mem_used}/${mem_total}, Temp: ${temp}°C"
            done
            ;;
        amd)
            if command -v rocm-smi &> /dev/null; then
                rocm-smi --showtemp | grep -E "GPU|Temp" | head -5
                rocm-smi --showmeminfo vram | grep -E "GPU|Used" | head -5
            fi
            ;;
        intel)
            if command -v intel_gpu_top &> /dev/null; then
                timeout 1 intel_gpu_top -l | head -5
            else
                echo "  Intel GPU monitoring tools not available"
            fi
            ;;
    esac
}

# Main execution
main() {
    log_info "Universal vLLM Server Startup Script"
    log_info "======================================"
    
    # Detect GPU type
    GPU_TYPE=$(detect_gpu_type)
    
    log_gpu "Selected GPU type: ${GPU_TYPE^^}"
    
    # Load appropriate configuration
    load_configuration "$GPU_TYPE"
    
    # Show configuration
    log_info "Configuration:"
    log_info "  Model: ${MODEL_ID}"
    log_info "  Port: ${VLLM_PORT}"
    log_info "  GPU Type: ${GPU_TYPE^^}"
    log_info "  Container: ${CONTAINER_NAME}"
    log_info "  Image Tag: ${IMAGE_TAG}"
    
    # Validate GPU count
    local gpu_count=$(get_gpu_count "$GPU_TYPE")
    log_gpu "Available GPUs: ${gpu_count}"
    
    if [[ $TENSOR_PARALLEL_SIZE -gt $gpu_count ]]; then
        log_error "Tensor parallel size ($TENSOR_PARALLEL_SIZE) exceeds GPUs ($gpu_count)"
        exit 1
    fi
    
    # Pre-flight checks
    check_docker
    check_existing_container
    pull_image "$GPU_TYPE"
    
    # Build and run container
    local docker_cmd=$(build_docker_command "$GPU_TYPE")
    
    log_info "Starting container..."
    log_debug "Command: ${docker_cmd}"
    
    if container_id=$(eval "${docker_cmd}" 2>&1); then
        log_info "Container started: ${container_id:0:12}"
        
        if wait_for_server; then
            log_info "==============================================="
            log_info "✅ vLLM Server Started Successfully!"
            log_info "==============================================="
            log_info "URL: http://localhost:${VLLM_PORT}"
            log_info "GPU Type: ${GPU_TYPE^^}"
            log_info "==============================================="
            
            display_gpu_stats "$GPU_TYPE"
            
            # Test API
            if curl -s "http://localhost:${VLLM_PORT}/v1/models" | grep -q "${MODEL_ID}"; then
                log_info "✅ API test successful!"
            else
                log_warn "⚠️  API test failed"
            fi
        else
            log_error "Health check failed"
            docker logs --tail 50 "${CONTAINER_NAME}"
            exit 1
        fi
    else
        log_error "Failed to start: ${container_id}"
        exit 1
    fi
    
    log_info "Setup completed successfully!"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force-nvidia)
            GPU_TYPE="nvidia"
            log_info "Forcing NVIDIA GPU mode"
            shift
            ;;
        --force-amd|--force-rocm)
            GPU_TYPE="amd"
            log_info "Forcing AMD/ROCm GPU mode"
            shift
            ;;
        --force-intel)
            GPU_TYPE="intel"
            log_info "Forcing Intel GPU mode"
            shift
            ;;
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --help)
            cat << EOF
Universal vLLM Startup Script

Usage: $0 [OPTIONS]

Options:
  --force-nvidia    Force NVIDIA GPU mode
  --force-amd       Force AMD/ROCm GPU mode
  --force-intel     Force Intel GPU mode (experimental)
  --config FILE     Specify configuration file
  --help           Show this help message

The script automatically detects your GPU type (NVIDIA/AMD/Intel)
and uses the appropriate configuration and Docker image.

Configuration files:
  NVIDIA: /opt/inference/config/vllm.conf
  AMD:    /opt/inference/config/vllm_rocm.conf
  Intel:  /opt/inference/config/vllm_intel.conf

EOF
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main
main "$@"
