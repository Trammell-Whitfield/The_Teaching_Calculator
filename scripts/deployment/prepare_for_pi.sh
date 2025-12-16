#!/usr/bin/env bash
################################################################################
# Holy Calculator - Raspberry Pi Deployment Preparation Script
# Run this on your development machine BEFORE transferring to the Pi
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Holy Calculator Pi Deployment Prep${NC}"
echo -e "${BLUE}================================${NC}\n"

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

# Step 1: Verify quantized models exist
echo -e "${YELLOW}[1/6] Verifying quantized models...${NC}"
MODELS_DIR="$PROJECT_ROOT/models/quantized"

if [ ! -d "$MODELS_DIR" ]; then
    echo -e "${RED}✗ models/quantized/ directory not found!${NC}"
    exit 1
fi

# Check for at least one Q4 or Q5 model
Q4_COUNT=$(find "$MODELS_DIR" -name "*q4km.gguf" | wc -l)
Q5_COUNT=$(find "$MODELS_DIR" -name "*q5km.gguf" | wc -l)

if [ "$Q4_COUNT" -eq 0 ] && [ "$Q5_COUNT" -eq 0 ]; then
    echo -e "${RED}✗ No Q4_K_M or Q5_K_M quantized models found!${NC}"
    echo -e "  Run quantization first or download pre-quantized models."
    exit 1
fi

echo -e "${GREEN}✓ Found $Q4_COUNT Q4_K_M and $Q5_COUNT Q5_K_M models${NC}"

# Show model sizes
echo -e "\n${BLUE}Available models:${NC}"
du -h "$MODELS_DIR"/*.gguf 2>/dev/null | grep -E "(q4km|q5km)" | while read size file; do
    basename_file=$(basename "$file")
    echo "  $size - $basename_file"
done

# Step 2: Check for F16 models (warn if present - too large for Pi)
echo -e "\n${YELLOW}[2/6] Checking for F16 models (will be excluded)...${NC}"
F16_COUNT=$(find "$MODELS_DIR" -name "*f16.gguf" | wc -l)

if [ "$F16_COUNT" -gt 0 ]; then
    echo -e "${YELLOW}⚠  Found $F16_COUNT F16 models (13-14GB each)${NC}"
    echo -e "  These will NOT be transferred to Pi (too large)"
    F16_TOTAL_SIZE=$(du -sh "$MODELS_DIR"/*f16.gguf 2>/dev/null | awk '{sum+=$1} END {print sum}')
    echo -e "  F16 models total size: ~27GB (excluded from transfer)"
fi

# Step 3: Calculate transfer size
echo -e "\n${YELLOW}[3/6] Calculating deployment size...${NC}"

# Only Q4/Q5 models
Q_MODELS_SIZE=$(du -ch "$MODELS_DIR"/*q4km.gguf "$MODELS_DIR"/*q5km.gguf 2>/dev/null | tail -1 | awk '{print $1}')
echo -e "${BLUE}Models to transfer: ${Q_MODELS_SIZE}${NC}"

# Code size (excluding venv, __pycache__, etc.)
CODE_SIZE=$(du -sh --exclude='venv' --exclude='CALC_env' --exclude='__pycache__' \
    --exclude='.git' --exclude='models' --exclude='llama.cpp/build' \
    "$PROJECT_ROOT" 2>/dev/null | awk '{print $1}')
echo -e "${BLUE}Code size: ${CODE_SIZE}${NC}"

echo -e "${GREEN}✓ Total transfer size: ~${Q_MODELS_SIZE} (models only)${NC}"

# Step 4: Create freeze of working dependencies
echo -e "\n${YELLOW}[4/6] Freezing current Python dependencies...${NC}"

# Check if virtual environment is active
if [ -n "$VIRTUAL_ENV" ]; then
    pip freeze > "$PROJECT_ROOT/requirements_dev_frozen.txt"
    echo -e "${GREEN}✓ Saved current dependencies to requirements_dev_frozen.txt${NC}"
else
    echo -e "${YELLOW}⚠  No virtual environment active${NC}"
    echo -e "  Skipping dependency freeze. Consider activating venv and re-running."
fi

# Step 5: Generate model checksums
echo -e "\n${YELLOW}[5/6] Generating model checksums...${NC}"
CHECKSUM_FILE="$PROJECT_ROOT/models/quantized/SHA256SUMS"

# Generate checksums for Q4/Q5 models only
(cd "$MODELS_DIR" && sha256sum *q4km.gguf *q5km.gguf 2>/dev/null > SHA256SUMS)

if [ -f "$CHECKSUM_FILE" ]; then
    echo -e "${GREEN}✓ Checksums saved to models/quantized/SHA256SUMS${NC}"
    echo -e "  Verify on Pi with: cd models/quantized && sha256sum -c SHA256SUMS"
else
    echo -e "${RED}✗ Failed to generate checksums${NC}"
fi

# Step 6: Show transfer instructions
echo -e "\n${YELLOW}[6/6] Preparing transfer command...${NC}"

PI_USER="${PI_USER:-pi}"
PI_HOST="${PI_HOST:-raspberrypi.local}"
PI_DEST="/home/$PI_USER/Holy_Calculator"

echo -e "\n${BLUE}================================${NC}"
echo -e "${BLUE}READY FOR TRANSFER${NC}"
echo -e "${BLUE}================================${NC}\n"

echo -e "${GREEN}To transfer the project to your Raspberry Pi:${NC}\n"

echo -e "${YELLOW}1. Transfer models (one-time, ~18-20GB):${NC}"
echo -e "   rsync -avz --progress models/quantized/*.gguf models/quantized/SHA256SUMS \\"
echo -e "     $PI_USER@$PI_HOST:$PI_DEST/models/quantized/\n"

echo -e "${YELLOW}2. Transfer code (quick, ~few MB):${NC}"
echo -e "   rsync -avz --progress --exclude='venv' --exclude='CALC_env' \\"
echo -e "     --exclude='__pycache__' --exclude='.git' --exclude='models' \\"
echo -e "     --exclude='llama.cpp/build' --exclude='*.pyc' \\"
echo -e "     . $PI_USER@$PI_HOST:$PI_DEST/\n"

echo -e "${YELLOW}3. Or use this helper command (both steps):${NC}"
echo -e "   PI_USER=$PI_USER PI_HOST=$PI_HOST ./scripts/deployment/transfer_to_pi.sh\n"

echo -e "${BLUE}Environment variables you can set:${NC}"
echo -e "  PI_USER=$PI_USER (default: pi)"
echo -e "  PI_HOST=$PI_HOST (default: raspberrypi.local)\n"

echo -e "${GREEN}✓ Preparation complete!${NC}\n"
