#!/bin/bash
# GPU Detection Test Script
# Tests GPU detection logic for vLLM setup

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

echo -e "${CYAN}===============================================${NC}"
echo -e "${CYAN}       GPU Detection Test for vLLM${NC}"
echo -e "${CYAN}===============================================${NC}"
echo

# Test NVIDIA detection
test_nvidia() {
    echo -e "${BLUE}Testing NVIDIA GPU detection...${NC}"
    
    if command -v nvidia-smi &> /dev/null; then
        echo -e "${GREEN}✓ nvidia-smi found${NC}"
        
        if nvidia-smi &> /dev/null; then
            echo -e "${GREEN}✓ NVIDIA GPU(s) detected${NC}"
            
            # Get GPU details
            echo -e "${CYAN}  GPU Information:${NC}"
            nvidia-smi --query-gpu=index,name,memory.total,driver_version,cuda_version \
                      --format=csv,noheader | while IFS=',' read -r idx name mem driver cuda; do
                echo "    GPU $idx: $name"
                echo "      Memory: $mem"
                echo "      Driver: $driver"
                echo "      CUDA: $cuda"
            done
            
            # Get count
            local count=$(nvidia-smi --query-gpu=count --format=csv,noheader | head -1)
            echo -e "${GREEN}  Total NVIDIA GPUs: $count${NC}"
            
            return 0
        else
            echo -e "${YELLOW}⚠ nvidia-smi found but no GPUs accessible${NC}"
        fi
    else
        echo -e "${YELLOW}✗ nvidia-smi not found${NC}"
    fi
    
    return 1
}

# Test AMD detection
test_amd() {
    echo -e "${BLUE}Testing AMD GPU detection...${NC}"
    
    local amd_detected=false
    
    # Method 1: rocm-smi
    if command -v rocm-smi &> /dev/null; then
        echo -e "${GREEN}✓ rocm-smi found${NC}"
        
        if rocm-smi --showid &> /dev/null; then
            echo -e "${GREEN}✓ AMD GPU(s) detected via rocm-smi${NC}"
            
            # Get GPU details
            echo -e "${MAGENTA}  GPU Information:${NC}"
            rocm-smi --showproductname 2>/dev/null | grep -v "^===" | grep -v "^$" | while read line; do
                echo "    $line"
            done
            
            # Get count
            local count=$(rocm-smi --showid | grep -c "GPU" || echo "0")
            echo -e "${GREEN}  Total AMD GPUs: $count${NC}"
            
            amd_detected=true
        else
            echo -e "${YELLOW}⚠ rocm-smi found but no GPUs accessible${NC}"
        fi
    else
        echo -e "${YELLOW}✗ rocm-smi not found${NC}"
    fi
    
    # Method 2: rocminfo
    if command -v rocminfo &> /dev/null; then
        echo -e "${GREEN}✓ rocminfo found${NC}"
        
        if rocminfo 2>/dev/null | grep -q "Device Type.*GPU"; then
            echo -e "${GREEN}✓ AMD GPU(s) detected via rocminfo${NC}"
            
            # Get GPU names
            echo -e "${MAGENTA}  GPU Details:${NC}"
            rocminfo 2>/dev/null | grep -E "Marketing Name:|Name:" | head -6 | while read line; do
                echo "    $line"
            done
            
            amd_detected=true
        fi
    else
        echo -e "${YELLOW}✗ rocminfo not found${NC}"
    fi
    
    # Method 3: Check kernel module
    if lsmod | grep -q amdgpu; then
        echo -e "${GREEN}✓ amdgpu kernel module loaded${NC}"
        amd_detected=true
    else
        echo -e "${YELLOW}✗ amdgpu kernel module not loaded${NC}"
    fi
    
    # Method 4: Check devices
    if [[ -e /dev/kfd ]]; then
        echo -e "${GREEN}✓ /dev/kfd exists (AMD compute)${NC}"
        amd_detected=true
    else
        echo -e "${YELLOW}✗ /dev/kfd not found${NC}"
    fi
    
    if [[ -d /dev/dri ]]; then
        local card_count=$(ls /dev/dri/card* 2>/dev/null | wc -l)
        if [[ $card_count -gt 0 ]]; then
            echo -e "${GREEN}✓ Found $card_count DRI card device(s)${NC}"
            ls /dev/dri/card* | while read card; do
                echo "    $card"
            done
        fi
    fi
    
    # Check ROCm installation
    if [[ -d /opt/rocm ]]; then
        echo -e "${GREEN}✓ ROCm installation found at /opt/rocm${NC}"
        if [[ -f /opt/rocm/.info/version ]]; then
            local rocm_version=$(cat /opt/rocm/.info/version)
            echo "    Version: $rocm_version"
        fi
    else
        echo -e "${YELLOW}✗ ROCm not installed at /opt/rocm${NC}"
    fi
    
    if $amd_detected; then
        return 0
    else
        return 1
    fi
}

# Test Intel detection (experimental)
test_intel() {
    echo -e "${BLUE}Testing Intel GPU detection...${NC}"
    
    local intel_detected=false
    
    # Check for Intel GPU via sysfs
    if [[ -d /sys/class/drm ]]; then
        for card in /sys/class/drm/card*/device/vendor; do
            if [[ -f "$card" ]]; then
                vendor=$(cat "$card")
                if [[ "$vendor" == "0x8086" ]]; then
                    echo -e "${GREEN}✓ Intel GPU detected${NC}"
                    intel_detected=true
                    break
                fi
            fi
        done
    fi
    
    # Check for Intel GPU tools
    if command -v intel_gpu_top &> /dev/null; then
        echo -e "${GREEN}✓ intel_gpu_top found${NC}"
        intel_detected=true
    else
        echo -e "${YELLOW}✗ intel_gpu_top not found${NC}"
    fi
    
    # Check for Level Zero
    if command -v clinfo &> /dev/null; then
        if clinfo 2>/dev/null | grep -q "Intel"; then
            echo -e "${GREEN}✓ Intel GPU detected via OpenCL${NC}"
            intel_detected=true
        fi
    fi
    
    if $intel_detected; then
        echo -e "${YELLOW}⚠ Intel GPU support is experimental in vLLM${NC}"
        return 0
    else
        return 1
    fi
}

# Check Docker GPU runtime
test_docker() {
    echo -e "${BLUE}Testing Docker GPU support...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker not installed${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓ Docker found${NC}"
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        echo -e "${RED}✗ Docker daemon not running or no permission${NC}"
        echo "  Try: sudo usermod -aG docker $USER"
        return 1
    fi
    
    echo -e "${GREEN}✓ Docker daemon accessible${NC}"
    
    # Check for GPU runtime
    if docker info 2>/dev/null | grep -q "nvidia"; then
        echo -e "${GREEN}✓ NVIDIA Docker runtime detected${NC}"
    fi
    
    if docker info 2>/dev/null | grep -q "rocm"; then
        echo -e "${GREEN}✓ ROCm Docker runtime detected${NC}"
    fi
    
    # Check Docker version
    local docker_version=$(docker --version | grep -oP '\d+\.\d+\.\d+')
    echo "  Docker version: $docker_version"
    
    return 0
}

# Test vLLM image availability
test_vllm_images() {
    echo -e "${BLUE}Testing vLLM Docker images...${NC}"
    
    # Check for NVIDIA image
    echo -n "  Checking vllm/vllm-openai:latest... "
    if docker manifest inspect vllm/vllm-openai:latest &> /dev/null; then
        echo -e "${GREEN}Available${NC}"
    else
        echo -e "${YELLOW}Not cached${NC}"
    fi
    
    # Check for ROCm image
    echo -n "  Checking rocm/vllm:latest... "
    if docker manifest inspect rocm/vllm:latest &> /dev/null; then
        echo -e "${GREEN}Available${NC}"
    else
        echo -e "${YELLOW}Not cached${NC}"
    fi
}

# Main detection logic (same as in universal script)
detect_gpu_type() {
    local gpu_type="none"
    
    # Check NVIDIA first
    if command -v nvidia-smi &> /dev/null && nvidia-smi &> /dev/null; then
        gpu_type="nvidia"
    # Check AMD
    elif command -v rocm-smi &> /dev/null && rocm-smi --showid &> /dev/null; then
        gpu_type="amd"
    elif command -v rocminfo &> /dev/null && rocminfo | grep -q "Device Type.*GPU"; then
        gpu_type="amd"
    elif [[ -e /dev/kfd ]]; then
        gpu_type="amd"
    # Check Intel
    elif [[ -d /sys/class/drm ]]; then
        for card in /sys/class/drm/card*/device/vendor; do
            if [[ -f "$card" ]] && [[ "$(cat $card)" == "0x8086" ]]; then
                gpu_type="intel"
                break
            fi
        done
    fi
    
    echo "$gpu_type"
}

# Summary and recommendations
print_summary() {
    echo
    echo -e "${CYAN}===============================================${NC}"
    echo -e "${CYAN}                 SUMMARY${NC}"
    echo -e "${CYAN}===============================================${NC}"
    
    local gpu_type=$(detect_gpu_type)
    
    case "$gpu_type" in
        nvidia)
            echo -e "${GREEN}✅ NVIDIA GPU detected and ready${NC}"
            echo
            echo "Recommended script: ./vllm_start_enhanced.sh"
            echo "Alternative: ./vllm_start_universal.sh"
            echo
            echo "Docker image: vllm/vllm-openai:v0.11.0"
            echo "Config file: /opt/inference/config/vllm.conf"
            ;;
        amd)
            echo -e "${MAGENTA}✅ AMD GPU detected and ready${NC}"
            echo
            echo "Recommended script: ./vllm_start_rocm.sh"
            echo "Alternative: ./vllm_start_universal.sh"
            echo
            echo "Docker image: rocm/vllm:rocm-v0.11.0"
            echo "Config file: /opt/inference/config/vllm_rocm.conf"
            
            # Check if override might be needed
            if ! command -v rocm-smi &> /dev/null; then
                echo
                echo -e "${YELLOW}⚠ Note: You may need to set HSA_OVERRIDE_GFX_VERSION${NC}"
                echo "  Check GPU_SUPPORT_GUIDE.md for your GPU model"
            fi
            ;;
        intel)
            echo -e "${BLUE}⚠ Intel GPU detected (experimental)${NC}"
            echo
            echo "Script: ./vllm_start_universal.sh --force-intel"
            echo
            echo "Note: Intel GPU support is experimental in vLLM"
            ;;
        none)
            echo -e "${RED}❌ No supported GPU detected${NC}"
            echo
            echo "Please ensure you have:"
            echo "  - NVIDIA GPU with CUDA drivers, or"
            echo "  - AMD GPU with ROCm drivers, or"
            echo "  - Intel GPU with Level Zero drivers"
            echo
            echo "For cloud/remote GPUs, you may need to:"
            echo "  - Install appropriate drivers"
            echo "  - Configure GPU passthrough"
            echo "  - Check container runtime settings"
            ;;
    esac
    
    # User permissions check
    echo
    echo -e "${CYAN}User Permissions:${NC}"
    
    # Check docker group
    if groups | grep -q docker; then
        echo -e "${GREEN}✓ User in docker group${NC}"
    else
        echo -e "${YELLOW}✗ User not in docker group${NC}"
        echo "  Run: sudo usermod -aG docker $USER"
    fi
    
    # Check video group (for AMD)
    if groups | grep -q video; then
        echo -e "${GREEN}✓ User in video group${NC}"
    else
        echo -e "${YELLOW}✗ User not in video group${NC}"
        if [[ "$gpu_type" == "amd" ]]; then
            echo "  Run: sudo usermod -aG video $USER"
        fi
    fi
    
    # Check render group (for AMD)
    if groups | grep -q render; then
        echo -e "${GREEN}✓ User in render group${NC}"
    elif [[ "$gpu_type" == "amd" ]]; then
        echo -e "${YELLOW}✗ User not in render group${NC}"
        echo "  Run: sudo usermod -aG render $USER"
    fi
}

# Run all tests
main() {
    echo -e "${CYAN}Running GPU detection tests...${NC}"
    echo
    
    # Test GPU detection
    nvidia_found=false
    amd_found=false
    intel_found=false
    
    if test_nvidia; then
        nvidia_found=true
    fi
    echo
    
    if test_amd; then
        amd_found=true
    fi
    echo
    
    if test_intel; then
        intel_found=true
    fi
    echo
    
    # Test Docker
    test_docker
    echo
    
    # Test images
    test_vllm_images
    echo
    
    # Print summary
    print_summary
    
    echo
    echo -e "${CYAN}===============================================${NC}"
    echo -e "${CYAN}Test complete! Check the summary above.${NC}"
    echo -e "${CYAN}===============================================${NC}"
}

# Run main
main "$@"
