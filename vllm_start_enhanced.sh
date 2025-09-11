#!/bin/bash
# Enhanced vLLM Server Startup Script for v0.11+
# Optimized for Chat with Tools framework compatibility
# =====================================================

set -euo pipefail  # Exit on error, undefined vars, and pipe failures

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function for colored output
log_info() { echo -e "${GREEN}[INFO]${NC} $1" | tee -a ${LOG_FILE}; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a ${LOG_FILE}; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" | tee -a ${LOG_FILE}; }
log_debug() { echo -e "${BLUE}[DEBUG]${NC} $1" | tee -a ${LOG_FILE}; }

# Configuration file support
CONFIG_FILE="${CONFIG_FILE:-/opt/inference/config/vllm.conf}"
if [[ -f "$CONFIG_FILE" ]]; then
    log_info "Loading configuration from $CONFIG_FILE"
    source "$CONFIG_FILE"
fi

# Log configuration
LOG_DIR="${LOG_DIR:-/opt/inference/logs}"
LOG_FILE="${LOG_DIR}/vllm_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$LOG_DIR"

# Model configuration with defaults
MODEL_ID="${MODEL_ID:-Orion-zhen/DeepHermes-3-Llama-3-8B-Preview-AWQ}"
MODEL_LENGTH="${MODEL_LENGTH:-14992}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.90}"
TENSOR_PARALLEL_SIZE="${TENSOR_PARALLEL_SIZE:-1}"
PIPELINE_PARALLEL_SIZE="${PIPELINE_PARALLEL_SIZE:-1}"
MAX_NUM_SEQS="${MAX_NUM_SEQS:-64}"
MAX_NUM_BATCHED_TOKENS="${MAX_NUM_BATCHED_TOKENS:-}"  # Auto if not set

# Server configuration
VLLM_PORT="${VLLM_PORT:-8081}"
VLLM_HOST="${VLLM_HOST:-0.0.0.0}"
VLLM_LOGGING_LEVEL="${VLLM_LOGGING_LEVEL:-INFO}"
CONTAINER_NAME="${CONTAINER_NAME:-vllm-server}"
RESTART_POLICY="${RESTART_POLICY:-unless-stopped}"

# vLLM v0.11+ specific settings
IMAGE_TAG="${IMAGE_TAG:-v0.10.1.1}"
TOOL_CALL_PARSER="${TOOL_CALL_PARSER:-hermes}"
ENABLE_AUTO_TOOL_CHOICE="${ENABLE_AUTO_TOOL_CHOICE:-true}"
ENABLE_CHUNKED_PREFILL="${ENABLE_CHUNKED_PREFILL:-false}"
MAX_NUM_SCHEDULED_SPLITS="${MAX_NUM_SCHEDULED_SPLITS:-}"

# Performance tuning
BLOCK_SIZE="${BLOCK_SIZE:-16}"
NUM_SCHEDULER_STEPS="${NUM_SCHEDULER_STEPS:-1}"
ENABLE_PREFIX_CACHING="${ENABLE_PREFIX_CACHING:-false}"
KV_CACHE_DTYPE="${KV_CACHE_DTYPE:-auto}"
QUANTIZATION_PARAM_PATH="${QUANTIZATION_PARAM_PATH:-}"

# API settings
API_KEY="${API_KEY:-}"  # Optional API key for security
SERVED_MODEL_NAME="${SERVED_MODEL_NAME:-}"  # Custom model name in API
RESPONSE_ROLE="${RESPONSE_ROLE:-assistant}"
CHAT_TEMPLATE="${CHAT_TEMPLATE:-}"  # Custom chat template path

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

# Function to validate GPU availability
check_gpu() {
    if ! command -v nvidia-smi &> /dev/null; then
        log_error "nvidia-smi not found. Please ensure NVIDIA drivers are installed."
        exit 1
    fi
    
    local gpu_count=$(nvidia-smi --query-gpu=count --format=csv,noheader | head -1)
    log_info "Found ${gpu_count} GPU(s)"
    
    if [[ $TENSOR_PARALLEL_SIZE -gt $gpu_count ]]; then
        log_error "Tensor parallel size ($TENSOR_PARALLEL_SIZE) exceeds available GPUs ($gpu_count)"
        exit 1
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
}

# Function to pull latest image
pull_image() {
    log_info "Pulling vLLM image: vllm/vllm-openai:${IMAGE_TAG}"
    if docker pull "vllm/vllm-openai:${IMAGE_TAG}"; then
        log_info "Successfully pulled image"
    else
        log_warn "Failed to pull image, will use local if available"
    fi
}

# Function to build Docker run command
build_docker_command() {
    local cmd="docker run --gpus all"
    cmd+=" --privileged"
    cmd+=" --restart ${RESTART_POLICY}"
    cmd+=" -p ${VLLM_PORT}:8000"
    cmd+=" -v ${HF_CACHE}:/root/.cache/huggingface"
    cmd+=" -v ${VLLM_CACHE}:/data"
    cmd+=" -v ${DOWNLOAD_DIR}:/downloads"
    
    # Environment variables
    cmd+=" --env VLLM_LOGGING_LEVEL=${VLLM_LOGGING_LEVEL}"
    cmd+=" --env HF_HUB_OFFLINE=${HF_HUB_OFFLINE:-0}"
    cmd+=" --env CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-all}"
    
    # Optional API key
    if [[ -n "$API_KEY" ]]; then
        cmd+=" --env VLLM_API_KEY=${API_KEY}"
    fi
    
    # Container settings
    cmd+=" --ipc=host"
    cmd+=" --ulimit memlock=-1"
    cmd+=" --ulimit stack=67108864"
    cmd+=" --name ${CONTAINER_NAME}"
    cmd+=" -d"
    cmd+=" vllm/vllm-openai:${IMAGE_TAG}"
    
    # vLLM arguments
    cmd+=" --host ${VLLM_HOST}"
    cmd+=" --port 8000"
    cmd+=" --model ${MODEL_ID}"
    cmd+=" --tokenizer ${MODEL_ID}"
    cmd+=" --trust-remote-code"
    cmd+=" --dtype auto"
    cmd+=" --max-model-len ${MODEL_LENGTH}"
    cmd+=" --gpu-memory-utilization ${GPU_MEMORY_UTILIZATION}"
    cmd+=" --tensor-parallel-size ${TENSOR_PARALLEL_SIZE}"
    cmd+=" --pipeline-parallel-size ${PIPELINE_PARALLEL_SIZE}"
    cmd+=" --max-num-seqs ${MAX_NUM_SEQS}"
    cmd+=" --block-size ${BLOCK_SIZE}"
    cmd+=" --num-scheduler-steps ${NUM_SCHEDULER_STEPS}"
    
    # Tool calling features (v0.11+)
    cmd+=" --tool-call-parser ${TOOL_CALL_PARSER}"
    if [[ "$ENABLE_AUTO_TOOL_CHOICE" == "true" ]]; then
        cmd+=" --enable-auto-tool-choice"
    fi
    
    # Optional parameters
    if [[ -n "$MAX_NUM_BATCHED_TOKENS" ]]; then
        cmd+=" --max-num-batched-tokens ${MAX_NUM_BATCHED_TOKENS}"
    fi
    
    if [[ -n "$SERVED_MODEL_NAME" ]]; then
        cmd+=" --served-model-name ${SERVED_MODEL_NAME}"
    fi
    
    if [[ -n "$CHAT_TEMPLATE" ]]; then
        cmd+=" --chat-template ${CHAT_TEMPLATE}"
    fi
    
    if [[ "$ENABLE_PREFIX_CACHING" == "true" ]]; then
        cmd+=" --enable-prefix-caching"
    fi
    
    if [[ "$ENABLE_CHUNKED_PREFILL" == "true" ]]; then
        cmd+=" --enable-chunked-prefill"
        if [[ -n "$MAX_NUM_SCHEDULED_SPLITS" ]]; then
            cmd+=" --max-num-scheduled-splits ${MAX_NUM_SCHEDULED_SPLITS}"
        fi
    fi
    
    if [[ "$KV_CACHE_DTYPE" != "auto" ]]; then
        cmd+=" --kv-cache-dtype ${KV_CACHE_DTYPE}"
    fi
    
    if [[ -n "$QUANTIZATION_PARAM_PATH" ]]; then
        cmd+=" --quantization-param-path ${QUANTIZATION_PARAM_PATH}"
    fi
    
    echo "$cmd"
}

# Function to wait for server to be ready
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
        if [[ $((attempt % 10)) -eq 0 ]]; then
            log_info "Still waiting... (${attempt}/${max_attempts})"
        fi
        sleep 2
    done
    
    log_error "vLLM server failed to start after ${max_attempts} attempts"
    return 1
}

# Function to display server info
display_server_info() {
    log_info "==============================================="
    log_info "vLLM Server Started Successfully!"
    log_info "==============================================="
    log_info "Model: ${MODEL_ID}"
    log_info "Server URL: http://localhost:${VLLM_PORT}"
    log_info "Container: ${CONTAINER_NAME}"
    log_info "Tool Parser: ${TOOL_CALL_PARSER}"
    log_info "Auto Tool Choice: ${ENABLE_AUTO_TOOL_CHOICE}"
    log_info "Max Sequences: ${MAX_NUM_SEQS}"
    log_info "GPU Memory: ${GPU_MEMORY_UTILIZATION}"
    log_info "==============================================="
    
    # Test the API
    log_info "Testing API endpoint..."
    if curl -s "http://localhost:${VLLM_PORT}/v1/models" | grep -q "${MODEL_ID}"; then
        log_info "✅ API test successful!"
    else
        log_warn "⚠️  API test failed or returned unexpected response"
    fi
}

# Function to show example usage
show_usage_examples() {
    cat << EOF | tee -a ${LOG_FILE}

📚 Example Usage with Chat with Tools Framework:
================================================

1. Update your config.yaml:
   openrouter:
     base_url: "http://localhost:${VLLM_PORT}/v1"
     model: "${MODEL_ID}"

2. Test with curl:
   curl http://localhost:${VLLM_PORT}/v1/chat/completions \\
     -H "Content-Type: application/json" \\
     -d '{
       "model": "${MODEL_ID}",
       "messages": [{"role": "user", "content": "Hello!"}],
       "tools": [...]
     }'

3. View logs:
   docker logs -f ${CONTAINER_NAME}

4. Stop server:
   docker stop ${CONTAINER_NAME}

5. Remove container:
   docker rm ${CONTAINER_NAME}

EOF
}

# Main execution
main() {
    log_info "Starting vLLM server setup at $(date)"
    log_info "Configuration:"
    log_info "  Model: ${MODEL_ID}"
    log_info "  Port: ${VLLM_PORT}"
    log_info "  Image: vllm/vllm-openai:${IMAGE_TAG}"
    log_info "  Max model length: ${MODEL_LENGTH}"
    log_info "  Tool call parser: ${TOOL_CALL_PARSER}"
    
    # Pre-flight checks
    check_docker
    check_gpu
    check_existing_container
    pull_image
    
    # Build and execute Docker command
    local docker_cmd=$(build_docker_command)
    
    log_info "Starting container..."
    log_debug "Docker command: ${docker_cmd}"
    
    if container_id=$(eval "${docker_cmd}" 2>&1); then
        log_info "Container started with ID: ${container_id:0:12}"
        
        # Wait for server to be ready
        if wait_for_server; then
            display_server_info
            show_usage_examples
        else
            log_error "Server health check failed"
            log_info "Checking container logs..."
            docker logs --tail 50 "${CONTAINER_NAME}"
            exit 1
        fi
    else
        log_error "Failed to start container: ${container_id}"
        exit 1
    fi
    
    log_info "Setup completed at $(date)"
}

# Run main function
main "$@"
