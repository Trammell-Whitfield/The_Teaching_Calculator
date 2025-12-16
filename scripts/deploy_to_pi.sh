#!/bin/bash
###############################################################################
# Deploy Holy Calculator to Raspberry Pi
# Transfers only necessary files (excludes docs, guides, test files)
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Header
echo ""
echo "======================================================================="
echo "  Deploy Holy Calculator to Raspberry Pi"
echo "======================================================================="
echo ""

# Check if we're in the project root
if [[ ! -f "main.py" ]] || [[ ! -f "requirements.txt" ]]; then
    log_error "Please run this script from the Holy-calc-pi directory"
    exit 1
fi

# Get Pi hostname/IP
PI_HOST="${1:-raspberrypi.local}"
PI_USER="${2:-tram}"

log_info "Target: $PI_USER@$PI_HOST"

# Test connection
log_info "Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 "$PI_USER@$PI_HOST" "echo Connected" &>/dev/null; then
    log_error "Cannot connect to $PI_HOST"
    echo ""
    echo "Usage: $0 [hostname] [user]"
    echo "Examples:"
    echo "  $0                          # Default: tram@raspberrypi.local"
    echo "  $0 192.168.1.100            # Use IP address"
    echo "  $0 raspberrypi.local tram   # Specify user"
    exit 1
fi
log_success "Connected to $PI_HOST"

# Create target directory on Pi
log_info "Creating directory on Pi..."
ssh "$PI_USER@$PI_HOST" "mkdir -p ~/Holy-calc-pi"

# ============================================================================
# RSYNC DEPLOYMENT (Selective Transfer)
# ============================================================================

log_info "Deploying files to Pi..."
echo ""

# Use rsync with filters to exclude unnecessary files
rsync -avz --progress \
    --exclude='.git/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='.DS_Store' \
    --exclude='venv/' \
    --exclude='env/' \
    --exclude='CALC_env/' \
    --exclude='.venv/' \
    --exclude='*.swp' \
    --exclude='*.swo' \
    --exclude='*.log' \
    --exclude='cache/' \
    --exclude='logs/' \
    --exclude='data/' \
    --exclude='models/base/' \
    --exclude='models/quantized/*-f16.gguf' \
    --exclude='models/quantized/deepseek-*.gguf' \
    --exclude='models/quantized/SHA256SUMS' \
    --exclude='llama.cpp/build/' \
    --exclude='llama.cpp/.git/' \
    --exclude='pi-stats-app/node_modules/' \
    --exclude='pi-stats-app/.next/' \
    --exclude='pi-stats-app/build/' \
    --exclude='*_SUMMARY.md' \
    --exclude='*_VERIFICATION.md' \
    --exclude='SESSION_SUMMARY.md' \
    --exclude='PROJECT_STATUS.md' \
    --exclude='RASPBERRY_PI_DEPLOYMENT.md' \
    --exclude='MQTT_QUICKSTART.md' \
    --exclude='ESP32_MQTT_SUMMARY.md' \
    --exclude='QUICKSTART_*.md' \
    --exclude='HOW_TO_*.md' \
    --exclude='*_OLD_PROTOTYPE.py' \
    --exclude='test_*.py' \
    --exclude='model_comparison_*.json' \
    --exclude='.env' \
    ./ "$PI_USER@$PI_HOST:~/Holy-calc-pi/"

log_success "Files transferred"

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo "======================================================================="
echo "  Deployment Summary"
echo "======================================================================="
echo ""
echo "✓ Files deployed to: $PI_USER@$PI_HOST:~/Holy-calc-pi/"
echo ""
echo "What was transferred:"
echo "  ✓ main.py (calculator entry point)"
echo "  ✓ requirements.txt & requirements_mqtt.txt"
echo "  ✓ scripts/ (cascade, monitoring, hardware)"
echo "  ✓ pi-stats-app/backend/ (Flask + MQTT)"
echo "  ✓ llama.cpp/ (source code, needs building on Pi)"
echo "  ✓ Qwen2.5-Math quantized model (~5GB Q5_K_M or Q4_K_M)"
echo "  ✓ docs/ESP32_CIRCUIT_DIAGRAM.md (hardware reference)"
echo "  ✓ docs/MQTT_SETUP_GUIDE.md (setup instructions)"
echo ""
echo "What was excluded (not needed on Pi):"
echo "  ✗ Personal notes/guides (*_SUMMARY.md, etc.)"
echo "  ✗ Test files (test_*.py)"
echo "  ✗ Development files (venv/, cache/, logs/)"
echo "  ✗ Base models (41GB original HuggingFace models)"
echo "  ✗ F16 intermediate models (14GB each)"
echo "  ✗ Old DeepSeek models (replaced by Qwen2.5-Math)"
echo "  ✗ Build artifacts (will be built on Pi)"
echo ""
echo "======================================================================="
echo "  Next Steps - Run on Raspberry Pi"
echo "======================================================================="
echo ""
echo "1. SSH to Raspberry Pi:"
echo "   ssh $PI_USER@$PI_HOST"
echo ""
echo "2. Navigate to project:"
echo "   cd ~/Holy-calc-pi"
echo ""
echo "3. Run setup script:"
echo "   ./scripts/setup_mqtt.sh"
echo ""
echo "4. Create Python environment:"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo ""
echo "5. Build llama.cpp:"
echo "   cd llama.cpp && mkdir build && cd build"
echo "   cmake .. -DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS"
echo "   cmake --build . --config Release -j 4"
echo ""
echo "6. Test calculator:"
echo "   python3 main.py --test"
echo ""
echo "7. Start monitoring dashboard:"
echo "   cd pi-stats-app/backend"
echo "   python3 app_mqtt.py"
echo ""
echo "   Access: http://$PI_HOST:5000"
echo ""
echo "======================================================================="
echo ""

log_success "Deployment complete!"
log_info "Follow the steps above to complete setup on the Pi"
echo ""
