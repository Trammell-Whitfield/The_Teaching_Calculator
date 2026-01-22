#!/bin/bash
# Holy Calculator Auto-Launch Uninstaller
# Removes systemd service and udev rules

set -e  # Exit on error

SERVICE_NAME="holy-calculator.service"
SERVICE_DEST="/etc/systemd/system/$SERVICE_NAME"
UDEV_DEST="/etc/udev/rules.d/99-ti84-calculator.rules"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "Holy Calculator Auto-Launch Uninstaller"
echo "=========================================="
echo ""

# Confirm uninstall
read -p "This will remove the auto-launch configuration. Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""

# Stop service if running
echo "[1/5] Stopping service..."
if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    sudo systemctl stop "$SERVICE_NAME"
    echo -e "  ${GREEN}✓${NC} Service stopped"
else
    echo -e "  ${YELLOW}○${NC} Service not running"
fi

# Disable service
echo "[2/5] Disabling service..."
if systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
    sudo systemctl disable "$SERVICE_NAME"
    echo -e "  ${GREEN}✓${NC} Service disabled"
else
    echo -e "  ${YELLOW}○${NC} Service not enabled"
fi

# Remove service file
echo "[3/5] Removing service file..."
if [ -f "$SERVICE_DEST" ]; then
    sudo rm "$SERVICE_DEST"
    echo -e "  ${GREEN}✓${NC} Removed $SERVICE_DEST"
else
    echo -e "  ${YELLOW}○${NC} Service file not found"
fi

# Remove udev rule
echo "[4/5] Removing udev rule..."
if [ -f "$UDEV_DEST" ]; then
    sudo rm "$UDEV_DEST"
    echo -e "  ${GREEN}✓${NC} Removed $UDEV_DEST"
else
    echo -e "  ${YELLOW}○${NC} Udev rule not found"
fi

# Reload daemons
echo "[5/5] Reloading system daemons..."
sudo systemctl daemon-reload
sudo udevadm control --reload-rules
sudo udevadm trigger
echo -e "  ${GREEN}✓${NC} Daemons reloaded"

echo ""
echo "=========================================="
echo -e "${GREEN}Uninstallation Complete!${NC}"
echo "=========================================="
echo ""
echo "Auto-launch has been removed."
echo "You can still run the calculator manually:"
echo "  cd $(dirname "$0")"
echo "  ./PICALC_env/bin/python autolaunch_main.py"
echo ""
