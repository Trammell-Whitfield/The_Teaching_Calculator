#!/usr/bin/env bash
################################################################################
# Holy Calculator - Transfer to Raspberry Pi
# Automates the rsync transfer process
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Transferring to Raspberry Pi${NC}"
echo -e "${BLUE}================================${NC}\n"

# Configuration
PI_USER="${PI_USER:-pi}"
PI_HOST="${PI_HOST:-raspberrypi.local}"
PI_DEST="/home/$PI_USER/Holy_Calculator"

# Get project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo -e "${YELLOW}Target: $PI_USER@$PI_HOST:$PI_DEST${NC}\n"

# Check if Pi is reachable
echo -e "${YELLOW}Testing connection to Pi...${NC}"
if ping -c 1 -W 2 "$PI_HOST" &> /dev/null; then
    echo -e "${GREEN}✓ Pi is reachable${NC}\n"
else
    echo -e "${RED}✗ Cannot reach $PI_HOST${NC}"
    echo -e "  Check that:"
    echo -e "    1. Pi is powered on and connected to network"
    echo -e "    2. SSH is enabled on the Pi"
    echo -e "    3. You can ping the Pi: ping $PI_HOST"
    exit 1
fi

# Create destination directory
echo -e "${YELLOW}Creating destination directory...${NC}"
ssh "$PI_USER@$PI_HOST" "mkdir -p $PI_DEST/models/quantized" || {
    echo -e "${RED}✗ Failed to create directory. Check SSH access.${NC}"
    exit 1
}
echo -e "${GREEN}✓ Directory ready${NC}\n"

# Transfer models (if they exist)
if [ -d "models/quantized" ]; then
    echo -e "${YELLOW}Transferring quantized models...${NC}"
    echo -e "${BLUE}This may take 10-30 minutes depending on your network.${NC}\n"

    rsync -avz --progress \
        --include='*q4km.gguf' \
        --include='*q5km.gguf' \
        --include='SHA256SUMS' \
        --exclude='*' \
        models/quantized/ \
        "$PI_USER@$PI_HOST:$PI_DEST/models/quantized/"

    echo -e "\n${GREEN}✓ Models transferred${NC}\n"
else
    echo -e "${YELLOW}⚠  No models directory found, skipping model transfer${NC}\n"
fi

# Transfer code
echo -e "${YELLOW}Transferring code...${NC}"
rsync -avz --progress \
    --exclude='venv' \
    --exclude='CALC_env' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='models/quantized/*.gguf' \
    --exclude='llama.cpp/build' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    . "$PI_USER@$PI_HOST:$PI_DEST/"

echo -e "\n${GREEN}✓ Code transferred${NC}\n"

# Show next steps
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Transfer Complete!${NC}"
echo -e "${BLUE}================================${NC}\n"

echo -e "${GREEN}Next steps:${NC}\n"
echo -e "1. SSH into your Pi:"
echo -e "   ${YELLOW}ssh $PI_USER@$PI_HOST${NC}\n"

echo -e "2. Navigate to the project:"
echo -e "   ${YELLOW}cd $PI_DEST${NC}\n"

echo -e "3. Run the Pi setup script:"
echo -e "   ${YELLOW}./scripts/deployment/pi_setup.sh${NC}\n"

echo -e "4. Or manually verify checksums:"
echo -e "   ${YELLOW}cd models/quantized && sha256sum -c SHA256SUMS${NC}\n"
