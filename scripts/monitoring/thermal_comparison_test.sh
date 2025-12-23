#!/bin/bash

################################################################################
# Thermal Comparison Test Script
# Purpose: Document temperature behavior with active cooling vs passive cooling
# Duration: ~10 minutes (5 min baseline + optional 5 min stress test)
#
# Usage:
#   ./thermal_comparison_test.sh [output_file]
#
# Example:
#   ./thermal_comparison_test.sh results/thermal_comparison.csv
################################################################################

set -euo pipefail

# Configuration
DURATION_BASELINE=300      # 5 minutes baseline monitoring
SAMPLE_INTERVAL=2          # Sample every 2 seconds
OUTPUT_FILE="${1:-thermal_comparison_$(date +%Y%m%d_%H%M%S).csv}"
STRESS_TEST="${2:-no}"     # Set to "stress" to run LLM load test

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ensure output directory exists
mkdir -p "$(dirname "$OUTPUT_FILE")"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

get_cpu_temp() {
    # Returns temperature in Celsius (numeric only)
    vcgencmd measure_temp | grep -o "[0-9.]*"
}

get_cpu_freq() {
    # Returns frequency in MHz
    vcgencmd measure_clock arm | cut -d= -f2 | awk '{print $1/1000000}'
}

get_throttle_status() {
    # Returns throttle hex value
    vcgencmd get_throttled | cut -d= -f2
}

decode_throttle() {
    local hex_value="$1"
    local dec_value=$((hex_value))

    # Bit flags:
    # Bit 0: Under-voltage detected
    # Bit 1: ARM frequency capped
    # Bit 2: Currently throttled
    # Bit 3: Soft temperature limit active
    # Bit 16: Under-voltage has occurred
    # Bit 17: ARM frequency capping has occurred
    # Bit 18: Throttling has occurred
    # Bit 19: Soft temperature limit has occurred

    if [ "$dec_value" -eq 0 ]; then
        echo "OK"
    else
        local flags=""
        [ $((dec_value & 0x1)) -ne 0 ] && flags="${flags}UNDER_VOLTAGE_NOW "
        [ $((dec_value & 0x2)) -ne 0 ] && flags="${flags}FREQ_CAPPED_NOW "
        [ $((dec_value & 0x4)) -ne 0 ] && flags="${flags}THROTTLED_NOW "
        [ $((dec_value & 0x8)) -ne 0 ] && flags="${flags}SOFT_TEMP_LIMIT_NOW "
        [ $((dec_value & 0x10000)) -ne 0 ] && flags="${flags}UNDER_VOLTAGE_PAST "
        [ $((dec_value & 0x20000)) -ne 0 ] && flags="${flags}FREQ_CAPPED_PAST "
        [ $((dec_value & 0x40000)) -ne 0 ] && flags="${flags}THROTTLED_PAST "
        [ $((dec_value & 0x80000)) -ne 0 ] && flags="${flags}SOFT_TEMP_LIMIT_PAST "
        echo "$flags"
    fi
}

################################################################################
# Main Test
################################################################################

print_header "Thermal Comparison Test Starting"

# Check if vcgencmd is available
if ! command -v vcgencmd &> /dev/null; then
    print_error "vcgencmd not found. This script requires Raspberry Pi OS."
    exit 1
fi

# Initial system info
print_info "System Information:"
echo "  - Date/Time: $(date)"
echo "  - Hostname: $(hostname)"
echo "  - Kernel: $(uname -r)"
echo "  - Current Temperature: $(get_cpu_temp)°C"
echo "  - Current CPU Frequency: $(get_cpu_freq) MHz"
echo "  - Throttle Status: $(get_throttle_status)"
echo ""

# Create CSV header
echo "timestamp,elapsed_sec,temp_celsius,cpu_freq_mhz,throttle_hex,throttle_status,test_phase,notes" > "$OUTPUT_FILE"

print_info "Output file: $OUTPUT_FILE"
print_info "Sample interval: ${SAMPLE_INTERVAL}s"
print_info "Baseline duration: ${DURATION_BASELINE}s ($(($DURATION_BASELINE / 60)) minutes)"
echo ""

################################################################################
# Phase 1: Baseline Monitoring (with active cooling)
################################################################################

print_header "Phase 1: Baseline Monitoring (Active Cooling ON)"
print_info "Monitoring idle temperature for $((DURATION_BASELINE / 60)) minutes..."
print_info "This establishes your current thermal baseline with the fan running."
echo ""

START_TIME=$(date +%s)
SAMPLES=0
TEMP_SUM=0
TEMP_MIN=999
TEMP_MAX=0

for ((i=0; i<DURATION_BASELINE; i+=SAMPLE_INTERVAL)); do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))

    TEMP=$(get_cpu_temp)
    FREQ=$(get_cpu_freq)
    THROTTLE=$(get_throttle_status)
    THROTTLE_STATUS=$(decode_throttle "$THROTTLE")

    # CSV output
    echo "$(date +%Y-%m-%d\ %H:%M:%S),$ELAPSED,$TEMP,$FREQ,$THROTTLE,$THROTTLE_STATUS,baseline_idle,fan_on" >> "$OUTPUT_FILE"

    # Statistics
    TEMP_SUM=$(echo "$TEMP_SUM + $TEMP" | bc)
    SAMPLES=$((SAMPLES + 1))

    if (( $(echo "$TEMP < $TEMP_MIN" | bc -l) )); then
        TEMP_MIN=$TEMP
    fi
    if (( $(echo "$TEMP > $TEMP_MAX" | bc -l) )); then
        TEMP_MAX=$TEMP
    fi

    # Progress indicator
    PROGRESS=$((i * 100 / DURATION_BASELINE))
    printf "\r[%3d%%] Temp: %5.1f°C | Freq: %4.0f MHz | Throttle: %s   " "$PROGRESS" "$TEMP" "$FREQ" "$THROTTLE_STATUS"

    sleep "$SAMPLE_INTERVAL"
done

echo ""  # New line after progress indicator
print_info "Baseline monitoring complete."

# Calculate baseline statistics
TEMP_AVG=$(echo "scale=2; $TEMP_SUM / $SAMPLES" | bc)

echo ""
print_info "Baseline Statistics (Active Cooling):"
echo "  - Average Temperature: ${TEMP_AVG}°C"
echo "  - Minimum Temperature: ${TEMP_MIN}°C"
echo "  - Maximum Temperature: ${TEMP_MAX}°C"
echo "  - Samples Collected: $SAMPLES"
echo ""

################################################################################
# Phase 2: Optional Stress Test
################################################################################

if [ "$STRESS_TEST" = "stress" ]; then
    print_header "Phase 2: Stress Test (Simulating LLM Load)"
    print_warning "This will generate CPU load to simulate LLM inference."
    print_info "Monitoring for 5 minutes under load..."
    echo ""

    # Start CPU stress in background
    # Using 'yes' command piped to /dev/null to generate CPU load
    # Start on all cores
    STRESS_PIDS=()
    for cpu in {0..3}; do
        taskset -c "$cpu" yes > /dev/null &
        STRESS_PIDS+=($!)
    done

    STRESS_START=$(date +%s)
    STRESS_DURATION=300  # 5 minutes
    STRESS_SAMPLES=0
    STRESS_TEMP_SUM=0
    STRESS_TEMP_MIN=999
    STRESS_TEMP_MAX=0

    for ((i=0; i<STRESS_DURATION; i+=SAMPLE_INTERVAL)); do
        CURRENT_TIME=$(date +%s)
        ELAPSED=$((CURRENT_TIME - START_TIME))

        TEMP=$(get_cpu_temp)
        FREQ=$(get_cpu_freq)
        THROTTLE=$(get_throttle_status)
        THROTTLE_STATUS=$(decode_throttle "$THROTTLE")

        # CSV output
        echo "$(date +%Y-%m-%d\ %H:%M:%S),$ELAPSED,$TEMP,$FREQ,$THROTTLE,$THROTTLE_STATUS,stress_test,cpu_load_100pct" >> "$OUTPUT_FILE"

        # Statistics
        STRESS_TEMP_SUM=$(echo "$STRESS_TEMP_SUM + $TEMP" | bc)
        STRESS_SAMPLES=$((STRESS_SAMPLES + 1))

        if (( $(echo "$TEMP < $STRESS_TEMP_MIN" | bc -l) )); then
            STRESS_TEMP_MIN=$TEMP
        fi
        if (( $(echo "$TEMP > $STRESS_TEMP_MAX" | bc -l) )); then
            STRESS_TEMP_MAX=$TEMP
        fi

        # Progress indicator
        PROGRESS=$((i * 100 / STRESS_DURATION))
        printf "\r[%3d%%] Temp: %5.1f°C | Freq: %4.0f MHz | Throttle: %s   " "$PROGRESS" "$TEMP" "$FREQ" "$THROTTLE_STATUS"

        sleep "$SAMPLE_INTERVAL"
    done

    # Stop stress test
    for pid in "${STRESS_PIDS[@]}"; do
        kill "$pid" 2>/dev/null || true
    done

    echo ""  # New line after progress indicator
    print_info "Stress test complete."

    # Calculate stress statistics
    STRESS_TEMP_AVG=$(echo "scale=2; $STRESS_TEMP_SUM / $STRESS_SAMPLES" | bc)

    echo ""
    print_info "Stress Test Statistics (Active Cooling):"
    echo "  - Average Temperature: ${STRESS_TEMP_AVG}°C"
    echo "  - Minimum Temperature: ${STRESS_TEMP_MIN}°C"
    echo "  - Maximum Temperature: ${STRESS_TEMP_MAX}°C"
    echo "  - Samples Collected: $STRESS_SAMPLES"
    echo ""
fi

################################################################################
# Final Summary
################################################################################

print_header "Test Complete - Summary"

echo "Output File: $OUTPUT_FILE"
echo ""

print_info "Baseline (Idle with Active Cooling):"
echo "  - Average: ${TEMP_AVG}°C"
echo "  - Range: ${TEMP_MIN}°C - ${TEMP_MAX}°C"

if [ "$STRESS_TEST" = "stress" ]; then
    echo ""
    print_info "Stress Test (100% CPU with Active Cooling):"
    echo "  - Average: ${STRESS_TEMP_AVG}°C"
    echo "  - Range: ${STRESS_TEMP_MIN}°C - ${STRESS_TEMP_MAX}°C"
    echo ""

    TEMP_INCREASE=$(echo "scale=2; $STRESS_TEMP_AVG - $TEMP_AVG" | bc)
    print_info "Temperature Increase Under Load: +${TEMP_INCREASE}°C"
fi

echo ""
print_info "Thermal Status:"
FINAL_THROTTLE=$(get_throttle_status)
FINAL_THROTTLE_STATUS=$(decode_throttle "$FINAL_THROTTLE")

if [ "$FINAL_THROTTLE" = "0x0" ]; then
    echo -e "  ${GREEN}✓ No throttling detected${NC}"
else
    echo -e "  ${RED}✗ Throttling events detected: $FINAL_THROTTLE_STATUS${NC}"
fi

echo ""
print_header "Documentation Notes"
echo ""
echo "For your UChicago essay, you can now cite:"
echo ""
echo "1. Active Cooling Performance (Idle):"
echo "   \"With the fan running, idle temperatures averaged ${TEMP_AVG}°C\""
echo ""

if [ "$STRESS_TEST" = "stress" ]; then
    echo "2. Active Cooling Performance (Under Load):"
    echo "   \"Under sustained CPU load simulating LLM inference, temperatures"
    echo "    averaged ${STRESS_TEMP_AVG}°C with a peak of ${STRESS_TEMP_MAX}°C\""
    echo ""
fi

echo "3. Throttling Status:"
if [ "$FINAL_THROTTLE" = "0x0" ]; then
    echo "   \"No thermal throttling occurred with active cooling\""
else
    echo "   \"Some throttling was detected: $FINAL_THROTTLE_STATUS\""
fi

echo ""
print_info "To compare with passive cooling (if you want to recreate that test):"
echo ""
echo "   1. Turn off your fan (if safe to do so)"
echo "   2. Wait 5 minutes for temperature to stabilize"
echo "   3. Run: ./thermal_comparison_test.sh passive_cooling.csv stress"
echo "   4. This will show how much hotter the system gets without active cooling"
echo ""
print_warning "Only run passive test if your system has proper heatsink installed!"
echo ""

print_header "Test Complete"
print_info "Data saved to: $OUTPUT_FILE"

exit 0
