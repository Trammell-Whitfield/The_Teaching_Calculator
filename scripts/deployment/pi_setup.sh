#!/usr/bin/env bash
################################################################################
# Holy Calculator - Raspberry Pi Setup Script
# Run this ON the Raspberry Pi after transferring files
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Holy Calculator - Raspberry Pi Setup${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Verify we're on a Raspberry Pi
ARCH=$(uname -m)
if [[ "$ARCH" != "aarch64" && "$ARCH" != "armv7l" ]]; then
    echo -e "${RED}✗ This script is designed for Raspberry Pi (ARM)${NC}"
    echo -e "  Detected architecture: $ARCH"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "${GREEN}✓ Detected ARM architecture: $ARCH${NC}\n"

# Get project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

# Phase 1: System Updates
echo -e "${YELLOW}[1/9] Updating system packages...${NC}"
sudo apt update
sudo apt upgrade -y
echo -e "${GREEN}✓ System updated${NC}\n"

# Phase 2: Install build dependencies
echo -e "${YELLOW}[2/9] Installing build dependencies...${NC}"
sudo apt install -y \
    build-essential \
    cmake \
    git \
    wget \
    python3-dev \
    python3-pip \
    python3-venv \
    libopenblas-dev \
    pkg-config

echo -e "${GREEN}✓ Build tools installed${NC}\n"

# Phase 3: Configure swap (important for 8GB models)
echo -e "${YELLOW}[3/9] Configuring swap space...${NC}"

CURRENT_SWAP=$(swapon --show=SIZE --noheadings | head -1 | tr -d ' ')
echo -e "Current swap: ${CURRENT_SWAP:-none}"

if [ -z "$CURRENT_SWAP" ] || [ "$CURRENT_SWAP" != "4G" ]; then
    echo -e "Increasing swap to 4GB for model loading..."
    sudo dphys-swapfile swapoff 2>/dev/null || true
    sudo sed -i 's/^CONF_SWAPSIZE=.*/CONF_SWAPSIZE=4096/' /etc/dphys-swapfile
    sudo dphys-swapfile setup
    sudo dphys-swapfile swapon
    echo -e "${GREEN}✓ Swap configured to 4GB${NC}\n"
else
    echo -e "${GREEN}✓ Swap already configured${NC}\n"
fi

# Phase 4: Set CPU governor
echo -e "${YELLOW}[4/9] Configuring CPU governor...${NC}"
echo "performance" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor > /dev/null
echo -e "${GREEN}✓ CPU governor set to 'performance'${NC}\n"

# Phase 5: Create Python virtual environment
echo -e "${YELLOW}[5/9] Creating Python virtual environment...${NC}"

if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠  venv already exists, removing...${NC}"
    rm -rf venv
fi

python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip wheel setuptools

echo -e "${GREEN}✓ Virtual environment created${NC}\n"

# Phase 6: Install Python dependencies
echo -e "${YELLOW}[6/9] Installing Python dependencies...${NC}"
echo -e "${BLUE}This may take 15-30 minutes...${NC}\n"

# Try standard installation first
if pip install -r requirements.txt; then
    echo -e "${GREEN}✓ Dependencies installed${NC}\n"
else
    echo -e "${YELLOW}⚠  Standard installation failed, trying ARM-specific build...${NC}"

    # Install dependencies one by one, with special handling for llama-cpp-python
    pip install sympy numpy requests pyyaml python-dotenv psutil huggingface-hub filelock tqdm packaging pyserial

    # Build llama-cpp-python from source with OpenBLAS
    echo -e "${YELLOW}Building llama-cpp-python with OpenBLAS acceleration...${NC}"
    CMAKE_ARGS="-DLLAMA_BLAS=ON -DLLAMA_BLAS_VENDOR=OpenBLAS" \
        pip install llama-cpp-python --no-cache-dir

    echo -e "${GREEN}✓ Dependencies installed (with custom build)${NC}\n"
fi

# Phase 7: Build llama.cpp
echo -e "${YELLOW}[7/9] Building llama.cpp for ARM...${NC}"

if [ ! -d "llama.cpp" ]; then
    echo -e "${RED}✗ llama.cpp directory not found!${NC}"
    echo -e "  The repository should include llama.cpp as a submodule."
    exit 1
fi

cd llama.cpp

# Clean previous builds
rm -rf build/
mkdir build
cd build

# Build with OpenBLAS acceleration
cmake .. \
    -DLLAMA_BLAS=ON \
    -DLLAMA_BLAS_VENDOR=OpenBLAS \
    -DLLAMA_NATIVE=OFF \
    -DCMAKE_BUILD_TYPE=Release

cmake --build . --config Release -j4

# Verify binaries
if [ -f "bin/llama-cli" ]; then
    echo -e "${GREEN}✓ llama.cpp built successfully${NC}"
    ./bin/llama-cli --version
else
    echo -e "${RED}✗ llama-cli binary not found after build!${NC}"
    exit 1
fi

cd "$PROJECT_ROOT"
echo

# Phase 8: Verify model checksums
echo -e "${YELLOW}[8/9] Verifying model checksums...${NC}"

if [ -f "models/quantized/SHA256SUMS" ]; then
    cd models/quantized
    if sha256sum -c SHA256SUMS 2>/dev/null; then
        echo -e "${GREEN}✓ All model checksums valid${NC}\n"
    else
        echo -e "${RED}✗ Model checksum verification failed!${NC}"
        echo -e "  Models may be corrupted. Re-transfer recommended."
        exit 1
    fi
    cd "$PROJECT_ROOT"
else
    echo -e "${YELLOW}⚠  No SHA256SUMS file found, skipping verification${NC}\n"
fi

# Phase 9: Run smoke tests
echo -e "${YELLOW}[9/9] Running smoke tests...${NC}"

# Test SymPy layer
echo -e "\n${BLUE}Testing SymPy layer...${NC}"
if python scripts/cascade/sympy_handler.py; then
    echo -e "${GREEN}✓ SymPy layer OK${NC}"
else
    echo -e "${RED}✗ SymPy layer failed${NC}"
    exit 1
fi

# Test model loading (quick test)
echo -e "\n${BLUE}Testing LLM model loading...${NC}"
echo -e "${YELLOW}This will take 15-30 seconds...${NC}"

if python -c "from scripts.cascade.llm_handler import LLMHandler; h = LLMHandler(); print('✓ Model loaded:', h.model_path.name)"; then
    echo -e "${GREEN}✓ LLM model loaded successfully${NC}"
else
    echo -e "${RED}✗ Failed to load LLM model${NC}"
    exit 1
fi

# Final summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${GREEN}Your Holy Calculator is ready to use!${NC}\n"

echo -e "${YELLOW}Quick start:${NC}"
echo -e "  1. Activate virtual environment:"
echo -e "     ${BLUE}source venv/bin/activate${NC}\n"

echo -e "  2. Run a test query:"
echo -e "     ${BLUE}python main.py --query \"Solve x^2 = 4\"${NC}\n"

echo -e "  3. Run the test suite:"
echo -e "     ${BLUE}python main.py --test --verbose${NC}\n"

echo -e "  4. Interactive mode:"
echo -e "     ${BLUE}python main.py --interactive${NC}\n"

# Show system info
echo -e "${YELLOW}System info:${NC}"
echo -e "  CPU: $(nproc) cores"
echo -e "  RAM: $(free -h | awk '/^Mem:/ {print $2}')"
echo -e "  Swap: $(free -h | awk '/^Swap:/ {print $2}')"
echo -e "  Temp: $(vcgencmd measure_temp 2>/dev/null || echo 'N/A')"
echo

echo -e "${GREEN}Happy calculating! 🧮${NC}\n"
