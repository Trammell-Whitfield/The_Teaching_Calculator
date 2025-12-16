#!/bin/bash
###############################################################################
# MQTT Setup Script for Holy Calculator
# Installs and configures Mosquitto MQTT broker + Python dependencies
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Header
echo ""
echo "======================================================================="
echo "  Holy Calculator - MQTT Setup Script"
echo "======================================================================="
echo ""

# Check if running on Raspberry Pi or Linux
if [[ ! -f /etc/os-release ]]; then
    log_error "This script is designed for Linux/Raspberry Pi"
    exit 1
fi

log_info "Detected OS: $(grep PRETTY_NAME /etc/os-release | cut -d '"' -f 2)"

###############################################################################
# 1. INSTALL MOSQUITTO MQTT BROKER
###############################################################################

echo ""
log_info "Step 1: Installing Mosquitto MQTT Broker..."

if command -v mosquitto &> /dev/null; then
    MOSQUITTO_VERSION=$(mosquitto -h 2>&1 | head -1 | awk '{print $3}')
    log_warning "Mosquitto already installed (version $MOSQUITTO_VERSION)"
    read -p "Reinstall/upgrade? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Skipping Mosquitto installation"
    else
        sudo apt update
        sudo apt install -y mosquitto mosquitto-clients
        log_success "Mosquitto upgraded"
    fi
else
    log_info "Installing Mosquitto..."
    sudo apt update
    sudo apt install -y mosquitto mosquitto-clients
    log_success "Mosquitto installed"
fi

# Check installation
if ! command -v mosquitto &> /dev/null; then
    log_error "Mosquitto installation failed"
    exit 1
fi

MOSQUITTO_VERSION=$(mosquitto -h 2>&1 | head -1 | awk '{print $3}')
log_success "Mosquitto $MOSQUITTO_VERSION is installed"

###############################################################################
# 2. CONFIGURE MOSQUITTO
###############################################################################

echo ""
log_info "Step 2: Configuring Mosquitto..."

MOSQUITTO_CONF="/etc/mosquitto/conf.d/holy-calc.conf"

if [[ -f $MOSQUITTO_CONF ]]; then
    log_warning "Configuration already exists: $MOSQUITTO_CONF"
    read -p "Overwrite? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Keeping existing configuration"
        SKIP_CONFIG=true
    fi
fi

if [[ ! $SKIP_CONFIG ]]; then
    log_info "Creating configuration file..."

    sudo tee $MOSQUITTO_CONF > /dev/null <<EOF
# Holy Calculator MQTT Configuration
# Generated on $(date)

# Allow anonymous connections (for local network)
# Set to false and configure password_file for production
allow_anonymous true

# Listen on all interfaces
listener 1883 0.0.0.0

# Persistent storage
persistence true
persistence_location /var/lib/mosquitto/

# Logging
log_dest file /var/log/mosquitto/mosquitto.log
log_type all
log_timestamp true

# QoS settings
max_queued_messages 1000
max_inflight_messages 20

# Connection limits
max_connections 100

# Message size limit (10MB)
message_size_limit 10485760
EOF

    log_success "Configuration created: $MOSQUITTO_CONF"

    # Create log directory if needed
    sudo mkdir -p /var/log/mosquitto
    sudo chown mosquitto:mosquitto /var/log/mosquitto
fi

###############################################################################
# 3. START MOSQUITTO SERVICE
###############################################################################

echo ""
log_info "Step 3: Starting Mosquitto service..."

# Enable and start
sudo systemctl enable mosquitto
sudo systemctl restart mosquitto

# Wait for service to start
sleep 2

# Check status
if sudo systemctl is-active --quiet mosquitto; then
    log_success "Mosquitto service is running"
else
    log_error "Mosquitto service failed to start"
    sudo systemctl status mosquitto
    exit 1
fi

###############################################################################
# 4. INSTALL PYTHON DEPENDENCIES
###############################################################################

echo ""
log_info "Step 4: Installing Python dependencies..."

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    log_info "Installing pip3..."
    sudo apt install -y python3-pip
fi

# Install paho-mqtt
log_info "Installing paho-mqtt..."
pip3 install --user paho-mqtt

log_success "Python dependencies installed"

###############################################################################
# 5. TEST MQTT BROKER
###############################################################################

echo ""
log_info "Step 5: Testing MQTT broker..."

# Test publish/subscribe
TEST_TOPIC="holy-calc/test"
TEST_MESSAGE="Hello from setup script - $(date +%s)"

log_info "Publishing test message..."
mosquitto_pub -h localhost -t "$TEST_TOPIC" -m "$TEST_MESSAGE" &

sleep 1

log_info "Subscribing to test topic..."
RECEIVED=$(timeout 3 mosquitto_sub -h localhost -t "$TEST_TOPIC" -C 1 2>/dev/null || echo "")

if [[ "$RECEIVED" == "$TEST_MESSAGE" ]]; then
    log_success "MQTT pub/sub test passed ✓"
else
    log_warning "MQTT pub/sub test failed (this may be normal)"
fi

###############################################################################
# 6. CONFIGURE FIREWALL (if UFW is active)
###############################################################################

echo ""
log_info "Step 6: Configuring firewall..."

if command -v ufw &> /dev/null && sudo ufw status | grep -q "Status: active"; then
    log_info "UFW is active, adding MQTT rule..."
    sudo ufw allow 1883/tcp comment "MQTT Mosquitto"
    log_success "Firewall rule added"
else
    log_info "UFW not active, skipping firewall configuration"
fi

###############################################################################
# 7. CREATE SYSTEMD SERVICE FOR MQTT MONITOR
###############################################################################

echo ""
log_info "Step 7: Creating systemd service for MQTT monitor..."

SERVICE_FILE="/etc/systemd/system/holy-calc-mqtt.service"

if [[ -f $SERVICE_FILE ]]; then
    log_warning "Service already exists: $SERVICE_FILE"
    read -p "Overwrite? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Keeping existing service"
        SKIP_SERVICE=true
    fi
fi

if [[ ! $SKIP_SERVICE ]]; then
    # Detect project directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

    log_info "Project directory: $PROJECT_DIR"

    sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Holy Calculator MQTT Monitor
After=network.target mosquitto.service
Requires=mosquitto.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR/pi-stats-app/backend
ExecStart=/usr/bin/python3 app_mqtt.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    log_success "Service file created: $SERVICE_FILE"

    # Reload systemd
    sudo systemctl daemon-reload
    log_info "Systemd reloaded"

    # Ask to enable service
    read -p "Enable service to start on boot? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl enable holy-calc-mqtt
        log_success "Service enabled (will start on boot)"
    fi

    # Ask to start service now
    read -p "Start service now? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl start holy-calc-mqtt
        sleep 2
        if sudo systemctl is-active --quiet holy-calc-mqtt; then
            log_success "Service is running"
        else
            log_error "Service failed to start"
            sudo systemctl status holy-calc-mqtt
        fi
    fi
fi

###############################################################################
# 8. SUMMARY
###############################################################################

echo ""
echo "======================================================================="
echo "  MQTT Setup Complete!"
echo "======================================================================="
echo ""
echo "✓ Mosquitto MQTT broker installed and running"
echo "✓ Configuration: $MOSQUITTO_CONF"
echo "✓ Python dependencies installed (paho-mqtt)"
echo "✓ Systemd service created: $SERVICE_FILE"
echo ""
echo "MQTT Broker Status:"
sudo systemctl status mosquitto --no-pager -l | head -10
echo ""
echo "Next Steps:"
echo "-----------------------------------------------------------------------"
echo "1. Upload ESP32 firmware:"
echo "   - Open: scripts/hardware/esp32_mqtt_monitor.ino"
echo "   - Configure WiFi and MQTT broker address"
echo "   - Upload to ESP32"
echo ""
echo "2. Start Flask backend with MQTT:"
echo "   cd $PROJECT_DIR/pi-stats-app/backend"
echo "   python3 app_mqtt.py"
echo ""
echo "3. Access dashboard:"
echo "   http://localhost:5000"
echo "   http://$(hostname).local:5000"
echo ""
echo "4. Monitor MQTT traffic:"
echo "   mosquitto_sub -h localhost -t 'holy-calc/#' -v"
echo ""
echo "5. Check service status:"
echo "   sudo systemctl status holy-calc-mqtt"
echo ""
echo "Logs:"
echo "  Mosquitto:  sudo tail -f /var/log/mosquitto/mosquitto.log"
echo "  Service:    sudo journalctl -u holy-calc-mqtt -f"
echo "======================================================================="
echo ""

# Final check
log_info "Testing connection..."
if nc -z localhost 1883 2>/dev/null; then
    log_success "MQTT broker is listening on port 1883 ✓"
else
    log_warning "Cannot connect to MQTT broker on port 1883"
fi

echo ""
log_success "Setup script completed successfully!"
echo ""
