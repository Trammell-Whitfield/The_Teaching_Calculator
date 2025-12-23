#!/bin/bash
# Power Testing and Analysis Script for Holy Calculator
# Collects system information needed for power analysis documentation
#
# Usage: ./power_test.sh [output_file]
#
# This script gathers:
# - CPU configuration (frequency, governor, voltage)
# - Thermal status (temperature, throttling)
# - Peripheral status (HDMI, Bluetooth, USB)
# - System power estimates (if available)
#
# Run this script during different workloads:
# 1. Idle (just booted, nothing running)
# 2. Light load (running SymPy queries)
# 3. Heavy load (running sustained LLM inference)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Output file
OUTPUT_FILE="${1:-power_test_$(date +%Y%m%d_%H%M%S).txt}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Holy Calculator - Power Analysis Data Collection      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Output file: ${GREEN}${OUTPUT_FILE}${NC}"
echo ""

# Start output file
{
    echo "========================================="
    echo "Holy Calculator - Power Analysis Report"
    echo "========================================="
    echo "Generated: $(date)"
    echo "Hostname: $(hostname)"
    echo ""
} > "$OUTPUT_FILE"

# Function to print and log
log() {
    echo -e "$1"
    echo -e "$1" | sed 's/\x1b\[[0-9;]*m//g' >> "$OUTPUT_FILE"
}

section() {
    echo ""
    log "${BLUE}═══ $1 ═══${NC}"
    echo ""
}

# Check if running on Pi
section "PLATFORM DETECTION"

PI_MODEL="Unknown"
if [ -f /proc/device-tree/model ]; then
    PI_MODEL=$(tr -d '\0' < /proc/device-tree/model)
    log "✓ Detected: ${GREEN}${PI_MODEL}${NC}"
else
    log "${YELLOW}⚠ Not running on Raspberry Pi (or /proc/device-tree/model not found)${NC}"
fi

log "Architecture: $(uname -m)"
log "Kernel: $(uname -r)"
log "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '"')"

# CPU Information
section "CPU CONFIGURATION"

CPU_COUNT=$(nproc)
log "CPU Cores: ${CPU_COUNT}"

if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
    GOVERNOR=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)
    log "Governor: ${GREEN}${GOVERNOR}${NC}"
else
    log "${YELLOW}⚠ CPU governor info not available${NC}"
fi

if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq ]; then
    CUR_FREQ=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq)
    CUR_FREQ_MHZ=$((CUR_FREQ / 1000))
    log "Current Frequency: ${GREEN}${CUR_FREQ_MHZ} MHz${NC}"
else
    log "${YELLOW}⚠ Current frequency info not available${NC}"
fi

if [ -f /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq ]; then
    MAX_FREQ=$(cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq)
    MAX_FREQ_MHZ=$((MAX_FREQ / 1000))
    log "Max Frequency: ${GREEN}${MAX_FREQ_MHZ} MHz${NC}"

    if [ "$MAX_FREQ_MHZ" -eq 2400 ]; then
        log "  → ${GREEN}Running at stock frequency (no underclocking)${NC}"
    else
        log "  → ${YELLOW}Non-standard max frequency (underclocked or different model?)${NC}"
    fi
else
    log "${YELLOW}⚠ Max frequency info not available${NC}"
fi

# All core frequencies
echo ""
log "Per-Core Frequencies:"
for cpu in /sys/devices/system/cpu/cpu[0-9]*; do
    if [ -f "$cpu/cpufreq/scaling_cur_freq" ]; then
        CORE=$(basename "$cpu")
        FREQ=$(cat "$cpu/cpufreq/scaling_cur_freq")
        FREQ_MHZ=$((FREQ / 1000))
        log "  ${CORE}: ${FREQ_MHZ} MHz"
    fi
done

# Thermal Information
section "THERMAL STATUS"

if command -v vcgencmd &> /dev/null; then
    TEMP=$(vcgencmd measure_temp | cut -d'=' -f2 | cut -d"'" -f1)
    TEMP_FLOAT=$(echo $TEMP | tr -d '.')

    if [ "${TEMP_FLOAT}" -lt 6000 ]; then
        log "Temperature: ${GREEN}${TEMP}°C${NC} ✓ Good"
    elif [ "${TEMP_FLOAT}" -lt 7000 ]; then
        log "Temperature: ${YELLOW}${TEMP}°C${NC} ⚠ Warm"
    elif [ "${TEMP_FLOAT}" -lt 8000 ]; then
        log "Temperature: ${YELLOW}${TEMP}°C${NC} ⚠ Hot - approaching warning threshold"
    else
        log "Temperature: ${RED}${TEMP}°C${NC} 🔥 Very Hot!"
    fi

    # Check throttling
    THROTTLED=$(vcgencmd get_throttled)
    THROTTLE_HEX=$(echo "$THROTTLED" | cut -d'=' -f2)

    log ""
    log "Throttling Status: ${THROTTLE_HEX}"

    if [ "$THROTTLE_HEX" = "0x0" ]; then
        log "  → ${GREEN}No throttling detected ✓${NC}"
    else
        log "  → ${RED}⚠ THROTTLING DETECTED!${NC}"
        log "  → This indicates the system has been throttled due to:"
        log "    - Under-voltage (insufficient power supply)"
        log "    - Over-temperature (cooling inadequate)"
        log "    - OR has been throttled in the past since boot"
        log ""
        log "  Hex value breakdown:"
        log "    0x50000 = Currently throttled"
        log "    0x50005 = Currently throttled + under-voltage"
        log "    See: https://www.raspberrypi.com/documentation/computers/os.html#get_throttled"
    fi

    # Voltage
    VOLTAGE=$(vcgencmd measure_volts core | cut -d'=' -f2)
    log ""
    log "Core Voltage: ${GREEN}${VOLTAGE}${NC}"

else
    log "${YELLOW}⚠ vcgencmd not available (not on Raspberry Pi?)${NC}"
fi

# Check for thermal files
if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
    SYS_TEMP=$(cat /sys/class/thermal/thermal_zone0/temp)
    SYS_TEMP_C=$(echo "scale=1; $SYS_TEMP / 1000" | bc)
    log "System Thermal: ${SYS_TEMP_C}°C (from thermal_zone0)"
fi

# Peripheral Status
section "PERIPHERAL STATUS"

# HDMI
if command -v tvservice &> /dev/null; then
    HDMI_STATUS=$(tvservice -s)
    if echo "$HDMI_STATUS" | grep -q "0x120002"; then
        log "HDMI: ${GREEN}Enabled${NC} (display detected)"
        log "  → Disabling could save ~0.5-1W"
        log "  → To disable: tvservice -o"
    elif echo "$HDMI_STATUS" | grep -q "0x120001"; then
        log "HDMI: ${YELLOW}Disabled${NC}"
        log "  → Power saved: ~0.5-1W"
    else
        log "HDMI: ${YELLOW}Status unknown: ${HDMI_STATUS}${NC}"
    fi
else
    log "${YELLOW}⚠ tvservice not available${NC}"
fi

# Bluetooth/WiFi
echo ""
log "Wireless Devices:"
if command -v rfkill &> /dev/null; then
    rfkill list | while IFS= read -r line; do
        if echo "$line" | grep -q "Soft blocked: yes"; then
            log "  ${YELLOW}${line}${NC}"
        elif echo "$line" | grep -q "Soft blocked: no"; then
            log "  ${GREEN}${line}${NC}"
        else
            log "  ${line}"
        fi
    done
else
    log "${YELLOW}⚠ rfkill not available${NC}"
fi

# USB devices
echo ""
log "USB Devices:"
if command -v lsusb &> /dev/null; then
    lsusb | while IFS= read -r line; do
        log "  ${line}"
    done
else
    log "${YELLOW}⚠ lsusb not available${NC}"
fi

# Memory Status
section "MEMORY STATUS"

TOTAL_MEM=$(free -h | awk '/^Mem:/ {print $2}')
USED_MEM=$(free -h | awk '/^Mem:/ {print $3}')
FREE_MEM=$(free -h | awk '/^Mem:/ {print $4}')
AVAILABLE_MEM=$(free -h | awk '/^Mem:/ {print $7}')

log "Total:     ${GREEN}${TOTAL_MEM}${NC}"
log "Used:      ${USED_MEM}"
log "Free:      ${FREE_MEM}"
log "Available: ${GREEN}${AVAILABLE_MEM}${NC}"

# Process Information
section "TOP PROCESSES (by CPU)"

log "$(ps aux --sort=-%cpu | head -6)"

echo ""
log "TOP PROCESSES (by Memory)"
log "$(ps aux --sort=-%mem | head -6)"

# Disk Usage
section "DISK USAGE"

DISK_INFO=$(df -h / | tail -1)
DISK_USED=$(echo "$DISK_INFO" | awk '{print $3}')
DISK_TOTAL=$(echo "$DISK_INFO" | awk '{print $2}')
DISK_PERCENT=$(echo "$DISK_INFO" | awk '{print $5}')

log "Root partition:"
log "  Used: ${DISK_USED} / ${DISK_TOTAL} (${DISK_PERCENT})"

# Network Status
section "NETWORK STATUS"

log "WiFi Status:"
if command -v iwconfig &> /dev/null; then
    WIFI_INFO=$(iwconfig 2>&1 | grep -A 10 "^wlan0" || echo "wlan0 not found")

    if echo "$WIFI_INFO" | grep -q "ESSID"; then
        SSID=$(echo "$WIFI_INFO" | grep ESSID | cut -d':' -f2 | tr -d '"')
        log "  SSID: ${GREEN}${SSID}${NC}"

        if echo "$WIFI_INFO" | grep -q "Signal level"; then
            SIGNAL=$(echo "$WIFI_INFO" | grep "Signal level" | sed 's/.*Signal level=\([^ ]*\).*/\1/')
            log "  Signal: ${GREEN}${SIGNAL}${NC}"
        fi
    else
        log "  ${YELLOW}Not connected${NC}"
    fi
else
    log "${YELLOW}⚠ iwconfig not available${NC}"
fi

# IP Address
echo ""
log "IP Addresses:"
ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | while read -r ip; do
    if [ "$ip" != "127.0.0.1" ]; then
        log "  ${GREEN}${ip}${NC}"
    fi
done

# Platform Config Detection
section "HOLY CALCULATOR CONFIG"

if [ -f "scripts/platform_config.py" ]; then
    log "${GREEN}✓ platform_config.py found${NC}"

    # Run platform config to get Holy Calculator settings
    if command -v python3 &> /dev/null; then
        log ""
        log "Platform Configuration:"
        python3 scripts/platform_config.py 2>/dev/null | while IFS= read -r line; do
            log "  ${line}"
        done
    fi
else
    log "${YELLOW}⚠ platform_config.py not found (not in Holy Calculator directory?)${NC}"
fi

# Check for running Holy Calculator processes
echo ""
log "Holy Calculator Processes:"
if pgrep -f "main.py" > /dev/null; then
    log "  ${GREEN}✓ main.py is running${NC}"
    ps aux | grep -E "main.py|llama" | grep -v grep | while IFS= read -r line; do
        log "    ${line}"
    done
else
    log "  ${YELLOW}✗ main.py not running${NC}"
fi

# ESP32 Monitoring
section "ESP32 MONITOR STATUS"

# Check if ESP32 Flask API is running
if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
    log "${GREEN}✓ ESP32 API responding on port 5000${NC}"

    # Try to get battery data
    BATTERY_DATA=$(curl -s http://localhost:5000/api/esp32/data 2>/dev/null || echo "")

    if [ -n "$BATTERY_DATA" ]; then
        log ""
        log "Latest Battery Data from ESP32:"
        echo "$BATTERY_DATA" | python3 -m json.tool 2>/dev/null | while IFS= read -r line; do
            log "  ${line}"
        done || log "  ${YELLOW}(Unable to parse JSON response)${NC}"
    fi
else
    log "${YELLOW}✗ ESP32 API not responding${NC}"
    log "  → Start with: python pi-stats-app/backend/app_esp32.py"
fi

# Check MQTT if available
if command -v mosquitto_sub &> /dev/null; then
    if pgrep mosquitto > /dev/null; then
        log ""
        log "${GREEN}✓ MQTT broker (mosquitto) is running${NC}"
        log "  → Monitor with: mosquitto_sub -h localhost -t \"holy-calc/#\" -v"
    else
        log ""
        log "${YELLOW}✗ MQTT broker not running${NC}"
    fi
fi

# Recommendations
section "POWER OPTIMIZATION RECOMMENDATIONS"

RECOMMENDATIONS=""

# Check HDMI
if command -v tvservice &> /dev/null; then
    if tvservice -s | grep -q "0x120002"; then
        RECOMMENDATIONS="${RECOMMENDATIONS}\n  ⚡ Disable HDMI if running headless: tvservice -o (~0.5-1W savings)"
    fi
fi

# Check Bluetooth
if rfkill list bluetooth 2>/dev/null | grep -q "Soft blocked: no"; then
    RECOMMENDATIONS="${RECOMMENDATIONS}\n  ⚡ Disable Bluetooth if not used: sudo rfkill block bluetooth (~0.1-0.2W savings)"
fi

# Check CPU governor
if [ -f /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
    CURRENT_GOV=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)
    if [ "$CURRENT_GOV" = "performance" ]; then
        RECOMMENDATIONS="${RECOMMENDATIONS}\n  ⚡ Consider 'ondemand' governor for better battery life"
    fi
fi

# Check temperature
if command -v vcgencmd &> /dev/null; then
    TEMP_NUM=$(vcgencmd measure_temp | cut -d'=' -f2 | cut -d'.' -f1)
    if [ "$TEMP_NUM" -ge 80 ]; then
        RECOMMENDATIONS="${RECOMMENDATIONS}\n  🔥 Temperature high (${TEMP_NUM}°C) - improve cooling or reduce CPU freq"
    fi
fi

if [ -n "$RECOMMENDATIONS" ]; then
    echo -e "$RECOMMENDATIONS" | while IFS= read -r line; do
        log "$line"
    done
else
    log "${GREEN}✓ No obvious optimization opportunities found${NC}"
fi

# Summary for power analysis doc
section "FOR YOUR POWER ANALYSIS DOCUMENT"

log "Copy these values to ${GREEN}docs/power-analysis.md${NC}:"
echo ""
log "CPU Configuration:"
if [ -n "${GOVERNOR:-}" ]; then
    log "  Governor: ${GOVERNOR}"
fi
if [ -n "${CUR_FREQ_MHZ:-}" ]; then
    log "  Current Frequency: ${CUR_FREQ_MHZ} MHz"
fi
if [ -n "${MAX_FREQ_MHZ:-}" ]; then
    log "  Max Frequency: ${MAX_FREQ_MHZ} MHz"
fi

echo ""
log "Thermal:"
if command -v vcgencmd &> /dev/null; then
    TEMP=$(vcgencmd measure_temp | cut -d'=' -f2 | cut -d"'" -f1)
    VOLTAGE=$(vcgencmd measure_volts core | cut -d'=' -f2)
    THROTTLED=$(vcgencmd get_throttled | cut -d'=' -f2)

    log "  Temperature: ${TEMP}°C"
    log "  Voltage: ${VOLTAGE}"
    log "  Throttled: ${THROTTLED}"
fi

echo ""
log "Memory:"
log "  Total: ${TOTAL_MEM}"
log "  Available: ${AVAILABLE_MEM}"

echo ""
log ""
log "${BLUE}════════════════════════════════════════${NC}"
log "${GREEN}✓ Data collection complete!${NC}"
log "Report saved to: ${GREEN}${OUTPUT_FILE}${NC}"
log "${BLUE}════════════════════════════════════════${NC}"
log ""

echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  1. Run this script during ${GREEN}idle${NC}, ${YELLOW}light load${NC}, and ${RED}heavy load${NC}"
echo -e "  2. Monitor ESP32 INA219 readings during each test"
echo -e "  3. Fill in the power measurements in ${GREEN}docs/power-analysis.md${NC}"
echo -e ""
echo -e "${BLUE}Testing Commands:${NC}"
echo -e "  ${GREEN}Idle:${NC}        ./power_test.sh idle_test.txt"
echo -e "  ${YELLOW}Light Load:${NC}  python main.py --query 'solve x^2 = 4' & ./power_test.sh light_test.txt"
echo -e "  ${RED}Heavy Load:${NC}  python main.py --interactive & ./power_test.sh heavy_test.txt"
echo ""
