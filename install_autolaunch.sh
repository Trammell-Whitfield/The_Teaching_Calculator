#!/bin/bash
# Holy Calculator Auto-Launch Installer
# Installs systemd service and udev rules for USB-triggered auto-start

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVICE_NAME="holy-calculator.service"
SERVICE_SOURCE="$SCRIPT_DIR/holy-calculator.service"
SERVICE_DEST="/etc/systemd/system/$SERVICE_NAME"
UDEV_SOURCE="$SCRIPT_DIR/99-ti84-calculator.rules"
UDEV_DEST="/etc/udev/rules.d/99-ti84-calculator.rules"
AUTOLAUNCH_SCRIPT="$SCRIPT_DIR/autolaunch_main.py"
VENV_PATH="$SCRIPT_DIR/PICALC_env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Holy Calculator Auto-Launch Installer"
echo "=========================================="
echo ""

# Check if running as root for system operations
check_sudo() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${YELLOW}Note: This script requires sudo for system configuration${NC}"
        echo "You will be prompted for your password."
        echo ""
    fi
}

# Check if running on Raspberry Pi
check_platform() {
    echo "[1/8] Checking platform..."
    if [ -f /proc/device-tree/model ]; then
        MODEL=$(cat /proc/device-tree/model | tr -d '\0')
        if echo "$MODEL" | grep -q "Raspberry Pi"; then
            echo -e "  ${GREEN}✓${NC} Running on: $MODEL"
        else
            echo -e "  ${YELLOW}⚠${NC} Not a Raspberry Pi: $MODEL"
            read -p "  Continue anyway? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    else
        echo -e "  ${YELLOW}⚠${NC} Cannot detect platform (not Raspberry Pi)"
        read -p "  Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Check for required packages
check_dependencies() {
    echo "[2/8] Checking dependencies..."

    # Check for lsusb
    if ! command -v lsusb &> /dev/null; then
        echo "  Installing usbutils..."
        sudo apt update
        sudo apt install -y usbutils
    fi
    echo -e "  ${GREEN}✓${NC} usbutils installed"

    # Check for systemctl
    if ! command -v systemctl &> /dev/null; then
        echo -e "  ${RED}✗${NC} systemd not found - cannot continue"
        exit 1
    fi
    echo -e "  ${GREEN}✓${NC} systemd available"
}

# Check for required files
check_files() {
    echo "[3/8] Checking required files..."

    # Check service file
    if [ ! -f "$SERVICE_SOURCE" ]; then
        echo -e "  ${RED}✗${NC} Service file not found: $SERVICE_SOURCE"
        exit 1
    fi
    echo -e "  ${GREEN}✓${NC} Service file found"

    # Check udev rule
    if [ ! -f "$UDEV_SOURCE" ]; then
        echo -e "  ${RED}✗${NC} Udev rule not found: $UDEV_SOURCE"
        exit 1
    fi
    echo -e "  ${GREEN}✓${NC} Udev rule found"

    # Check autolaunch script
    if [ ! -f "$AUTOLAUNCH_SCRIPT" ]; then
        echo -e "  ${RED}✗${NC} Autolaunch script not found: $AUTOLAUNCH_SCRIPT"
        exit 1
    fi
    echo -e "  ${GREEN}✓${NC} Autolaunch script found"

    # Check virtual environment
    if [ ! -f "$VENV_PATH/bin/python" ]; then
        echo -e "  ${RED}✗${NC} Virtual environment not found: $VENV_PATH"
        echo "     Please create it with: python3 -m venv $VENV_PATH"
        exit 1
    fi
    echo -e "  ${GREEN}✓${NC} Virtual environment found"
}

# Check for TI-84 connection
check_calculator() {
    echo "[4/8] Checking for TI-84 connection..."

    if lsusb | grep -q "0451:e008"; then
        DEVICE_INFO=$(lsusb | grep "0451:e008")
        echo -e "  ${GREEN}✓${NC} TI-84 Plus Silver detected"
        echo "     $DEVICE_INFO"
    else
        echo -e "  ${YELLOW}⚠${NC} TI-84 not currently connected"
        echo "     The service will auto-start when connected"
        echo ""
        echo "  To connect TI-84:"
        echo "    1. Connect USB cable to calculator"
        echo "    2. On calculator: Press 2nd + LINK"
        echo "    3. Select USB mode if prompted"
        echo ""
        read -p "  Press Enter to continue installation..."
    fi
}

# Install systemd service
install_service() {
    echo "[5/8] Installing systemd service..."

    # Make autolaunch script executable
    chmod +x "$AUTOLAUNCH_SCRIPT"

    # Copy service file
    sudo cp "$SERVICE_SOURCE" "$SERVICE_DEST"
    sudo chmod 644 "$SERVICE_DEST"

    echo -e "  ${GREEN}✓${NC} Service file installed to $SERVICE_DEST"
}

# Install udev rule
install_udev() {
    echo "[6/8] Installing udev rule..."

    # Copy udev rule
    sudo cp "$UDEV_SOURCE" "$UDEV_DEST"
    sudo chmod 644 "$UDEV_DEST"

    echo -e "  ${GREEN}✓${NC} Udev rule installed to $UDEV_DEST"
}

# Reload system daemons
reload_daemons() {
    echo "[7/8] Reloading system daemons..."

    # Reload systemd
    sudo systemctl daemon-reload
    echo -e "  ${GREEN}✓${NC} Systemd daemon reloaded"

    # Reload udev rules
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    echo -e "  ${GREEN}✓${NC} Udev rules reloaded"
}

# Enable and optionally start service
enable_service() {
    echo "[8/8] Enabling service..."

    # Enable service for auto-start
    sudo systemctl enable "$SERVICE_NAME"
    echo -e "  ${GREEN}✓${NC} Service enabled for auto-start"

    # Check if TI-84 is connected and offer to start
    if lsusb | grep -q "0451:e008"; then
        echo ""
        read -p "  TI-84 detected. Start service now? (Y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
            sudo systemctl start "$SERVICE_NAME"
            sleep 2
            if systemctl is-active --quiet "$SERVICE_NAME"; then
                echo -e "  ${GREEN}✓${NC} Service started successfully"
            else
                echo -e "  ${YELLOW}⚠${NC} Service may still be initializing"
                echo "     Check status: sudo systemctl status $SERVICE_NAME"
            fi
        fi
    fi
}

# Print success message and instructions
print_success() {
    echo ""
    echo "=========================================="
    echo -e "${GREEN}Installation Complete!${NC}"
    echo "=========================================="
    echo ""
    echo "The Holy Calculator will now auto-start when"
    echo "TI-84 Plus Silver (VID:0451 PID:e008) is connected."
    echo ""
    echo "Testing commands:"
    echo "  1. Manual start:   sudo systemctl start $SERVICE_NAME"
    echo "  2. Check status:   sudo systemctl status $SERVICE_NAME"
    echo "  3. View logs:      journalctl -u $SERVICE_NAME -f"
    echo "  4. Auto-test:      Unplug calculator, wait 5s, plug back in"
    echo ""
    echo "Monitoring commands:"
    echo "  - USB events:      udevadm monitor --environment | grep 0451"
    echo "  - System logs:     tail -f /var/log/syslog | grep TI-84"
    echo "  - App logs:        tail -f $SCRIPT_DIR/calculator.log"
    echo ""
    echo "Management commands:"
    echo "  - Stop service:    sudo systemctl stop $SERVICE_NAME"
    echo "  - Disable:         sudo systemctl disable $SERVICE_NAME"
    echo "  - Uninstall:       $SCRIPT_DIR/uninstall_autolaunch.sh"
    echo ""
}

# Main installation flow
main() {
    check_sudo
    check_platform
    check_dependencies
    check_files
    check_calculator
    install_service
    install_udev
    reload_daemons
    enable_service
    print_success
}

# Run main
main
