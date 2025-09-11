#!/bin/bash
# Quick test script for vLLM ROCm setup with AMD's Docker images

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

VLLM_PORT="${VLLM_PORT:-8081}"
CONTAINER_NAME="${CONTAINER_NAME:-vllm-rocm-server}"

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}    vLLM ROCm Server Test Script${NC}"
echo -e "${CYAN}========================================${NC}"
echo

# Check if container is running
check_container() {
    echo -e "${CYAN}1. Checking container status...${NC}"
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${GREEN}✓ Container '${CONTAINER_NAME}' is running${NC}"
        
        # Show container details
        echo -e "\n${CYAN}Container Details:${NC}"
        docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.ID}}\t{{.Status}}\t{{.Ports}}"
        return 0
    else
        echo -e "${RED}✗ Container '${CONTAINER_NAME}' is not running${NC}"
        
        # Check if container exists but stopped
        if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
            echo -e "${YELLOW}Container exists but is stopped. Showing last logs:${NC}"
            docker logs --tail 20 "${CONTAINER_NAME}"
        fi
        return 1
    fi
}

# Check health endpoint
check_health() {
    echo -e "\n${CYAN}2. Checking health endpoint...${NC}"
    
    local health_url="http://localhost:${VLLM_PORT}/health"
    echo "   Testing: $health_url"
    
    if response=$(curl -s -o /dev/null -w "%{http_code}" "$health_url" 2>/dev/null); then
        if [[ "$response" == "200" ]]; then
            echo -e "${GREEN}✓ Health check passed (HTTP $response)${NC}"
            return 0
        else
            echo -e "${RED}✗ Health check failed (HTTP $response)${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ Cannot connect to server${NC}"
        return 1
    fi
}

# Check models endpoint
check_models() {
    echo -e "\n${CYAN}3. Checking models endpoint...${NC}"
    
    local models_url="http://localhost:${VLLM_PORT}/v1/models"
    echo "   Testing: $models_url"
    
    if response=$(curl -s "$models_url" 2>/dev/null); then
        if echo "$response" | grep -q '"object":"list"'; then
            echo -e "${GREEN}✓ Models endpoint working${NC}"
            
            # Extract and display model info
            if command -v python3 &>/dev/null; then
                echo -e "\n${CYAN}Loaded Models:${NC}"
                echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for model in data.get('data', []):
        print(f\"  - {model.get('id', 'unknown')} (created: {model.get('created', 'unknown')})\")
except:
    print('  Could not parse model data')
" 2>/dev/null || echo "  Could not parse model data"
            else
                echo "$response" | grep -o '"id":"[^"]*"' | sed 's/"id":"//;s/"//' | while read model; do
                    echo "  - $model"
                done
            fi
            return 0
        else
            echo -e "${YELLOW}⚠ Models endpoint returned unexpected data${NC}"
            echo "Response: $response"
            return 1
        fi
    else
        echo -e "${RED}✗ Cannot connect to models endpoint${NC}"
        return 1
    fi
}

# Test completion
test_completion() {
    echo -e "\n${CYAN}4. Testing text completion...${NC}"
    
    local api_url="http://localhost:${VLLM_PORT}/v1/completions"
    
    # Get model name from models endpoint
    local model_id=$(curl -s "http://localhost:${VLLM_PORT}/v1/models" 2>/dev/null | \
                     grep -o '"id":"[^"]*"' | head -1 | sed 's/"id":"//;s/"//')
    
    if [[ -z "$model_id" ]]; then
        echo -e "${YELLOW}⚠ Could not determine model ID, using default${NC}"
        model_id="model"
    else
        echo "   Using model: $model_id"
    fi
    
    echo "   Sending test prompt..."
    
    local response=$(curl -s -X POST "$api_url" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"$model_id\",
            \"prompt\": \"Once upon a time\",
            \"max_tokens\": 50,
            \"temperature\": 0.7
        }" 2>/dev/null)
    
    if echo "$response" | grep -q '"choices"'; then
        echo -e "${GREEN}✓ Completion test successful${NC}"
        
        # Extract and display the completion
        if command -v python3 &>/dev/null; then
            echo -e "\n${CYAN}Generated Text:${NC}"
            echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    text = data['choices'][0]['text']
    print(f'  \"{text.strip()}\"')
except:
    print('  Could not parse completion')
" 2>/dev/null || echo "  Could not parse completion"
        fi
        return 0
    else
        echo -e "${RED}✗ Completion test failed${NC}"
        echo "Response: $response"
        return 1
    fi
}

# Test chat completion (if supported)
test_chat() {
    echo -e "\n${CYAN}5. Testing chat completion...${NC}"
    
    local api_url="http://localhost:${VLLM_PORT}/v1/chat/completions"
    
    # Get model name
    local model_id=$(curl -s "http://localhost:${VLLM_PORT}/v1/models" 2>/dev/null | \
                     grep -o '"id":"[^"]*"' | head -1 | sed 's/"id":"//;s/"//')
    
    [[ -z "$model_id" ]] && model_id="model"
    
    echo "   Sending chat message..."
    
    local response=$(curl -s -X POST "$api_url" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"$model_id\",
            \"messages\": [{\"role\": \"user\", \"content\": \"Hello! How are you?\"}],
            \"max_tokens\": 50,
            \"temperature\": 0.7
        }" 2>/dev/null)
    
    if echo "$response" | grep -q '"choices"'; then
        echo -e "${GREEN}✓ Chat completion test successful${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Chat completion not available or failed${NC}"
        return 1
    fi
}

# Show GPU stats
show_gpu_stats() {
    echo -e "\n${CYAN}6. GPU Statistics:${NC}"
    
    if command -v rocm-smi &>/dev/null; then
        echo -e "\n${CYAN}Temperature:${NC}"
        rocm-smi -t 2>/dev/null | grep -E "GPU\[|Temperature" | head -5
        
        echo -e "\n${CYAN}Memory Usage:${NC}"
        rocm-smi --showmeminfo vram 2>/dev/null | grep -E "GPU\[|Used|Free" | head -10
        
        echo -e "\n${CYAN}Power:${NC}"
        rocm-smi -P 2>/dev/null | grep -E "GPU\[|Average" | head -5
    else
        echo -e "${YELLOW}rocm-smi not available${NC}"
    fi
}

# Show container logs
show_logs() {
    echo -e "\n${CYAN}7. Recent Container Logs:${NC}"
    docker logs --tail 10 "${CONTAINER_NAME}" 2>&1 | sed 's/^/  /'
}

# Main test flow
main() {
    local all_passed=true
    
    # Run tests
    if ! check_container; then
        echo -e "\n${RED}Container is not running. Please start it first:${NC}"
        echo "  ./vllm_start_rocm_fixed.sh"
        exit 1
    fi
    
    check_health || all_passed=false
    check_models || all_passed=false
    test_completion || all_passed=false
    test_chat || true  # Don't fail if chat isn't supported
    show_gpu_stats
    
    # Summary
    echo -e "\n${CYAN}========================================${NC}"
    if $all_passed; then
        echo -e "${GREEN}✓ All tests passed!${NC}"
        echo -e "${GREEN}Your vLLM ROCm server is working correctly.${NC}"
    else
        echo -e "${YELLOW}⚠ Some tests failed${NC}"
        echo -e "${YELLOW}Check the logs for more details:${NC}"
        echo "  docker logs ${CONTAINER_NAME}"
    fi
    echo -e "${CYAN}========================================${NC}"
    
    # Show tips
    echo -e "\n${CYAN}Useful Commands:${NC}"
    echo "  Monitor GPU:     watch -n 1 rocm-smi"
    echo "  Container logs:  docker logs -f ${CONTAINER_NAME}"
    echo "  Stop server:     docker stop ${CONTAINER_NAME}"
    echo "  Remove server:   docker rm ${CONTAINER_NAME}"
}

# Run main
main "$@"
