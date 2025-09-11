#!/bin/bash
# vLLM Server Monitoring Script
# Monitor health, performance, and logs of vLLM server

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
CONTAINER_NAME="${CONTAINER_NAME:-vllm-server}"
VLLM_PORT="${VLLM_PORT:-8081}"
REFRESH_INTERVAL="${REFRESH_INTERVAL:-5}"

# Functions for colored output
print_header() { echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"; }
print_section() { echo -e "${BLUE}▶ $1${NC}"; }
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }

# Check if container is running
check_container_status() {
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        return 0
    else
        return 1
    fi
}

# Get container stats
get_container_stats() {
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" "${CONTAINER_NAME}" 2>/dev/null || echo "N/A"
}

# Check API health
check_api_health() {
    local health_url="http://localhost:${VLLM_PORT}/health"
    local models_url="http://localhost:${VLLM_PORT}/v1/models"
    
    # Check health endpoint
    if curl -s -o /dev/null -w "%{http_code}" "$health_url" | grep -q "200"; then
        print_success "Health endpoint: OK"
    else
        print_error "Health endpoint: Failed"
    fi
    
    # Check models endpoint
    local models_response=$(curl -s "$models_url" 2>/dev/null)
    if [[ -n "$models_response" ]]; then
        local model_count=$(echo "$models_response" | grep -o '"id"' | wc -l)
        print_success "Models endpoint: OK ($model_count model(s) loaded)"
        
        # Extract and display model names
        echo "$models_response" | grep -o '"id":"[^"]*"' | sed 's/"id":"//;s/"$//' | while read -r model; do
            echo "  - $model"
        done
    else
        print_error "Models endpoint: Failed"
    fi
}

# Get GPU utilization
get_gpu_stats() {
    if command -v nvidia-smi &> /dev/null; then
        nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu \
                   --format=csv,noheader,nounits 2>/dev/null | while IFS=',' read -r idx name util mem_used mem_total temp; do
            local mem_percent=$(awk "BEGIN {printf \"%.1f\", ($mem_used/$mem_total)*100}")
            echo "  GPU $idx: $name"
            echo "    Utilization: ${util}%"
            echo "    Memory: ${mem_used}MB / ${mem_total}MB (${mem_percent}%)"
            echo "    Temperature: ${temp}°C"
        done
    else
        echo "  nvidia-smi not available"
    fi
}

# Get recent logs
get_recent_logs() {
    docker logs --tail 10 --timestamps "${CONTAINER_NAME}" 2>&1 | sed 's/^/  /'
}

# Get error logs
get_error_logs() {
    docker logs "${CONTAINER_NAME}" 2>&1 | grep -i -E "error|exception|failed|critical" | tail -5 | sed 's/^/  /'
}

# Test inference
test_inference() {
    local test_prompt="Hello, how are you?"
    local api_url="http://localhost:${VLLM_PORT}/v1/chat/completions"
    
    local response=$(curl -s -X POST "$api_url" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"${MODEL_ID:-model}\",
            \"messages\": [{\"role\": \"user\", \"content\": \"$test_prompt\"}],
            \"max_tokens\": 50,
            \"temperature\": 0.7
        }" 2>/dev/null)
    
    if echo "$response" | grep -q "choices"; then
        print_success "Inference test: OK"
        local content=$(echo "$response" | grep -o '"content":"[^"]*"' | head -1 | sed 's/"content":"//;s/"$//')
        echo "  Response: ${content:0:100}..."
    else
        print_error "Inference test: Failed"
        echo "  Error: $response"
    fi
}

# Monitor mode
monitor_mode() {
    while true; do
        clear
        print_header
        echo -e "${CYAN}vLLM Server Monitor - $(date)${NC}"
        print_header
        echo
        
        if check_container_status; then
            print_success "Container Status: Running"
            echo
            
            print_section "Container Stats"
            get_container_stats
            echo
            
            print_section "API Health"
            check_api_health
            echo
            
            print_section "GPU Stats"
            get_gpu_stats
            echo
            
            print_section "Recent Logs"
            get_recent_logs
            echo
            
            if [[ "${SHOW_ERRORS:-false}" == "true" ]]; then
                print_section "Recent Errors"
                get_error_logs
                echo
            fi
            
            if [[ "${TEST_INFERENCE:-false}" == "true" ]]; then
                print_section "Inference Test"
                test_inference
                echo
            fi
        else
            print_error "Container Status: Not Running"
            echo
            print_warning "Container '${CONTAINER_NAME}' is not running"
            echo "Start it with: ./vllm_start_enhanced.sh"
        fi
        
        print_header
        echo "Refreshing in ${REFRESH_INTERVAL} seconds... (Press Ctrl+C to exit)"
        sleep "${REFRESH_INTERVAL}"
    done
}

# Dashboard mode (single run)
dashboard_mode() {
    print_header
    echo -e "${CYAN}vLLM Server Status - $(date)${NC}"
    print_header
    echo
    
    if check_container_status; then
        print_success "Container Status: Running"
        echo
        
        print_section "Container Stats"
        get_container_stats
        echo
        
        print_section "API Health"
        check_api_health
        echo
        
        print_section "GPU Stats"
        get_gpu_stats
        echo
        
        print_section "Recent Logs (last 5 entries)"
        docker logs --tail 5 --timestamps "${CONTAINER_NAME}" 2>&1 | sed 's/^/  /'
        echo
    else
        print_error "Container Status: Not Running"
        echo
        print_warning "Container '${CONTAINER_NAME}' is not running"
    fi
    
    print_header
}

# Performance benchmark
benchmark_mode() {
    print_header
    echo -e "${CYAN}vLLM Performance Benchmark${NC}"
    print_header
    echo
    
    if ! check_container_status; then
        print_error "Container is not running"
        exit 1
    fi
    
    local api_url="http://localhost:${VLLM_PORT}/v1/chat/completions"
    local num_requests="${1:-10}"
    local total_time=0
    local successful=0
    local failed=0
    
    print_section "Running $num_requests inference requests..."
    echo
    
    for i in $(seq 1 "$num_requests"); do
        local start_time=$(date +%s.%N)
        
        local response=$(curl -s -X POST "$api_url" \
            -H "Content-Type: application/json" \
            -d "{
                \"model\": \"${MODEL_ID:-model}\",
                \"messages\": [{\"role\": \"user\", \"content\": \"Generate a random sentence about AI.\"}],
                \"max_tokens\": 50,
                \"temperature\": 0.9
            }" 2>/dev/null)
        
        local end_time=$(date +%s.%N)
        local duration=$(awk "BEGIN {printf \"%.3f\", $end_time - $start_time}")
        
        if echo "$response" | grep -q "choices"; then
            echo -e "  Request $i: ${GREEN}Success${NC} (${duration}s)"
            successful=$((successful + 1))
            total_time=$(awk "BEGIN {printf \"%.3f\", $total_time + $duration}")
        else
            echo -e "  Request $i: ${RED}Failed${NC}"
            failed=$((failed + 1))
        fi
    done
    
    echo
    print_section "Benchmark Results"
    echo "  Total Requests: $num_requests"
    echo "  Successful: $successful"
    echo "  Failed: $failed"
    
    if [[ $successful -gt 0 ]]; then
        local avg_time=$(awk "BEGIN {printf \"%.3f\", $total_time / $successful}")
        local throughput=$(awk "BEGIN {printf \"%.2f\", $successful / $total_time}")
        echo "  Average Response Time: ${avg_time}s"
        echo "  Throughput: ${throughput} req/s"
    fi
    
    echo
    print_header
}

# Show usage
show_usage() {
    cat << EOF
vLLM Server Monitor - Monitor and manage your vLLM server

Usage: $0 [OPTIONS] [COMMAND]

Commands:
  monitor     Continuous monitoring mode (default)
  dashboard   Show current status and exit
  benchmark   Run performance benchmark
  logs        Show container logs
  errors      Show error logs only
  restart     Restart the container
  stop        Stop the container
  help        Show this help message

Options:
  -c, --container NAME    Container name (default: vllm-server)
  -p, --port PORT        Server port (default: 8081)
  -r, --refresh SECONDS  Refresh interval for monitor (default: 5)
  -t, --test             Include inference test in monitoring
  -e, --errors           Show error logs in monitoring

Examples:
  $0                     # Start monitoring with defaults
  $0 dashboard           # Show current status
  $0 benchmark 20        # Run 20 benchmark requests
  $0 -t monitor          # Monitor with inference testing
  $0 logs                # Show container logs

Environment Variables:
  CONTAINER_NAME         Override container name
  VLLM_PORT             Override server port
  REFRESH_INTERVAL      Override refresh interval
  TEST_INFERENCE        Enable inference testing
  SHOW_ERRORS          Show error logs

EOF
}

# Parse command line arguments
COMMAND="monitor"
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--container)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        -p|--port)
            VLLM_PORT="$2"
            shift 2
            ;;
        -r|--refresh)
            REFRESH_INTERVAL="$2"
            shift 2
            ;;
        -t|--test)
            TEST_INFERENCE="true"
            shift
            ;;
        -e|--errors)
            SHOW_ERRORS="true"
            shift
            ;;
        monitor|dashboard|benchmark|logs|errors|restart|stop|help)
            COMMAND="$1"
            shift
            ;;
        *)
            if [[ "$COMMAND" == "benchmark" ]]; then
                # Assume it's the number of requests for benchmark
                BENCHMARK_REQUESTS="$1"
            fi
            shift
            ;;
    esac
done

# Execute command
case "$COMMAND" in
    monitor)
        monitor_mode
        ;;
    dashboard)
        dashboard_mode
        ;;
    benchmark)
        benchmark_mode "${BENCHMARK_REQUESTS:-10}"
        ;;
    logs)
        docker logs -f "${CONTAINER_NAME}"
        ;;
    errors)
        docker logs "${CONTAINER_NAME}" 2>&1 | grep -i -E "error|exception|failed|critical"
        ;;
    restart)
        print_warning "Restarting container '${CONTAINER_NAME}'..."
        docker restart "${CONTAINER_NAME}"
        print_success "Container restarted"
        ;;
    stop)
        print_warning "Stopping container '${CONTAINER_NAME}'..."
        docker stop "${CONTAINER_NAME}"
        print_success "Container stopped"
        ;;
    help)
        show_usage
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac
