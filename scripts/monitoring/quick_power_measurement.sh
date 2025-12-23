#!/bin/bash
# Quick 30-Minute Power & Thermal Test
# Gets you the key measurements for your essay
#
# Prerequisites:
# - ESP32 with INA219 running and accessible
# - Raspberry Pi 5 with Holy Calculator set up
#
# This script will:
# 1. Measure idle power (5 min)
# 2. Measure light load (SymPy queries)
# 3. Measure heavy load (LLM query)
# 4. Track thermal behavior
# 5. Calculate battery life estimate

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ESP32_URL="${ESP32_URL:-http://localhost:5000/api/esp32/data}"
OUTPUT_DIR="power_measurements_$(date +%Y%m%d_%H%M%S)"
BATTERY_CAPACITY_MAH=5000

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Holy Calculator - Quick Power & Thermal Measurement     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "This will take ~30 minutes and give you all the data you need"
echo "for your UChicago essay hardware narrative."
echo ""
echo -e "${YELLOW}Output directory: ${OUTPUT_DIR}${NC}"
echo ""

mkdir -p "$OUTPUT_DIR"

# Helper function to get ESP32 data
get_power_data() {
    if command -v jq &> /dev/null; then
        curl -s "$ESP32_URL" | jq '{voltage: .battery.voltage, current: .battery.current, power: .battery.power}'
    else
        curl -s "$ESP32_URL"
    fi
}

# Helper function to get temperature
get_temp() {
    if command -v vcgencmd &> /dev/null; then
        vcgencmd measure_temp | cut -d'=' -f2 | cut -d"'" -f1
    else
        echo "N/A"
    fi
}

# Helper function to check throttling
get_throttle_status() {
    if command -v vcgencmd &> /dev/null; then
        vcgencmd get_throttled | cut -d'=' -f2
    else
        echo "N/A"
    fi
}

# Check if ESP32 is accessible
echo "Checking ESP32 connection..."
if curl -s --max-time 3 "$ESP32_URL" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ ESP32 accessible at $ESP32_URL${NC}"
else
    echo -e "${RED}✗ Cannot reach ESP32 at $ESP32_URL${NC}"
    echo ""
    echo "Options:"
    echo "  1. Start the ESP32 Flask server: python pi-stats-app/backend/app_esp32.py"
    echo "  2. Set ESP32_URL env var: export ESP32_URL=http://raspberrypi.local:5000/api/esp32/data"
    echo "  3. Use MQTT instead (not yet implemented in this script)"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Test 1: IDLE BASELINE (5 minutes)${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Measuring power consumption at idle..."
echo "Please don't use the Pi during this test."
echo ""

IDLE_START=$(date +%s)
IDLE_LOG="$OUTPUT_DIR/idle_baseline.log"

{
    echo "IDLE BASELINE TEST"
    echo "Started: $(date)"
    echo "Duration: 5 minutes"
    echo "==========================================="
    echo ""
} > "$IDLE_LOG"

echo "Time,Temp(°C),Voltage(V),Current(mA),Power(W),Throttled" >> "$IDLE_LOG"

for i in {1..300}; do
    TEMP=$(get_temp)
    THROTTLE=$(get_throttle_status)

    # Get power data
    POWER_DATA=$(get_power_data 2>/dev/null || echo "{}")

    VOLTAGE=$(echo "$POWER_DATA" | grep -o '"voltage"[^,]*' | cut -d':' -f2 | tr -d ' "' || echo "N/A")
    CURRENT=$(echo "$POWER_DATA" | grep -o '"current"[^,]*' | cut -d':' -f2 | tr -d ' "' || echo "N/A")
    POWER=$(echo "$POWER_DATA" | grep -o '"power"[^,]*' | cut -d':' -f2 | tr -d ' "' || echo "N/A")

    echo "$i,$TEMP,$VOLTAGE,$CURRENT,$POWER,$THROTTLE" >> "$IDLE_LOG"

    # Print status every 30 seconds
    if [ $((i % 30)) -eq 0 ]; then
        ELAPSED=$((i / 60))
        echo -e "  ${BLUE}[$ELAPSED min]${NC} Temp: ${TEMP}°C, Power: ${POWER}W"
    fi

    sleep 1
done

echo ""
echo -e "${GREEN}✓ Idle baseline complete${NC}"
echo "  Log: $IDLE_LOG"

# Calculate idle stats
IDLE_AVG_POWER=$(tail -n +2 "$IDLE_LOG" | cut -d',' -f5 | awk '{sum+=$1; count++} END {if(count>0) print sum/count; else print "N/A"}')
IDLE_AVG_TEMP=$(tail -n +2 "$IDLE_LOG" | cut -d',' -f2 | awk '{sum+=$1; count++} END {if(count>0) print sum/count; else print "N/A"}')

echo "  Average power: ${IDLE_AVG_POWER}W"
echo "  Average temp: ${IDLE_AVG_TEMP}°C"
echo ""

echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Test 2: LIGHT LOAD (SymPy queries)${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Running 10 SymPy queries and measuring power..."
echo ""

LIGHT_LOG="$OUTPUT_DIR/light_load.log"

{
    echo "LIGHT LOAD TEST (SymPy)"
    echo "Started: $(date)"
    echo "Test: 10 algebraic queries"
    echo "==========================================="
    echo ""
} > "$LIGHT_LOG"

echo "Query,Time(s),Temp(°C),Voltage(V),Current(mA),Power(W)" >> "$LIGHT_LOG"

for i in {1..10}; do
    echo -e "  ${BLUE}Query $i/10:${NC} solve x^2 + ${i}x + $((i+1)) = 0"

    START_TIME=$(date +%s.%N)
    TEMP_BEFORE=$(get_temp)

    # Run query
    python3 main.py --query "solve x^2 + ${i}x + $((i+1)) = 0" > /dev/null 2>&1 || true

    END_TIME=$(date +%s.%N)
    ELAPSED=$(echo "$END_TIME - $START_TIME" | bc)

    # Measure power immediately after
    TEMP=$(get_temp)
    POWER_DATA=$(get_power_data 2>/dev/null || echo "{}")
    VOLTAGE=$(echo "$POWER_DATA" | grep -o '"voltage"[^,]*' | cut -d':' -f2 | tr -d ' "' || echo "N/A")
    CURRENT=$(echo "$POWER_DATA" | grep -o '"current"[^,]*' | cut -d':' -f2 | tr -d ' "' || echo "N/A")
    POWER=$(echo "$POWER_DATA" | grep -o '"power"[^,]*' | cut -d':' -f2 | tr -d ' "' || echo "N/A")

    echo "$i,$ELAPSED,$TEMP,$VOLTAGE,$CURRENT,$POWER" >> "$LIGHT_LOG"
    echo "    ✓ ${ELAPSED}s, ${TEMP}°C, ${POWER}W"

    sleep 2
done

echo ""
echo -e "${GREEN}✓ Light load test complete${NC}"
echo "  Log: $LIGHT_LOG"

LIGHT_AVG_POWER=$(tail -n +2 "$LIGHT_LOG" | cut -d',' -f6 | awk '{sum+=$1; count++} END {if(count>0) print sum/count; else print "N/A"}')
LIGHT_AVG_TEMP=$(tail -n +2 "$LIGHT_LOG" | cut -d',' -f3 | awk '{sum+=$1; count++} END {if(count>0) print sum/count; else print "N/A"}')

echo "  Average power: ${LIGHT_AVG_POWER}W"
echo "  Average temp: ${LIGHT_AVG_TEMP}°C"
echo ""

echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Test 3: HEAVY LOAD (LLM query)${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Running LLM query and tracking power/thermal..."
echo "This will take 15-30 seconds..."
echo ""

HEAVY_LOG="$OUTPUT_DIR/heavy_load.log"

{
    echo "HEAVY LOAD TEST (LLM)"
    echo "Started: $(date)"
    echo "Test: Single complex LLM query with thermal tracking"
    echo "==========================================="
    echo ""
} > "$HEAVY_LOG"

echo "Time(s),Temp(°C),Voltage(V),Current(mA),Power(W),Throttled" >> "$HEAVY_LOG"

# Start LLM query in background
QUERY="Explain the Pythagorean theorem with a proof"
echo -e "  ${BLUE}Query:${NC} $QUERY"
echo ""

python3 main.py --query "$QUERY" > "$OUTPUT_DIR/llm_query_output.txt" 2>&1 &
LLM_PID=$!

# Monitor power and thermal while query runs
SAMPLE=0
while kill -0 $LLM_PID 2>/dev/null; do
    TEMP=$(get_temp)
    THROTTLE=$(get_throttle_status)
    POWER_DATA=$(get_power_data 2>/dev/null || echo "{}")
    VOLTAGE=$(echo "$POWER_DATA" | grep -o '"voltage"[^,]*' | cut -d':' -f2 | tr -d ' "' || echo "N/A")
    CURRENT=$(echo "$POWER_DATA" | grep -o '"current"[^,]*' | cut -d':' -f2 | tr -d ' "' || echo "N/A")
    POWER=$(echo "$POWER_DATA" | grep -o '"power"[^,]*' | cut -d':' -f2 | tr -d ' "' || echo "N/A")

    echo "$SAMPLE,$TEMP,$VOLTAGE,$CURRENT,$POWER,$THROTTLE" >> "$HEAVY_LOG"

    echo -e "    ${BLUE}[$SAMPLE s]${NC} Temp: ${TEMP}°C, Power: ${POWER}W, Throttle: ${THROTTLE}"

    SAMPLE=$((SAMPLE + 1))
    sleep 1
done

wait $LLM_PID

echo ""
echo -e "${GREEN}✓ Heavy load test complete${NC}"
echo "  Log: $HEAVY_LOG"
echo "  LLM output: $OUTPUT_DIR/llm_query_output.txt"

# Calculate heavy load stats
HEAVY_AVG_POWER=$(tail -n +2 "$HEAVY_LOG" | cut -d',' -f5 | awk '{sum+=$1; count++} END {if(count>0) print sum/count; else print "N/A"}')
HEAVY_PEAK_POWER=$(tail -n +2 "$HEAVY_LOG" | cut -d',' -f5 | awk 'BEGIN{max=0} {if($1+0>max) max=$1} END {print max}')
HEAVY_AVG_TEMP=$(tail -n +2 "$HEAVY_LOG" | cut -d',' -f2 | awk '{sum+=$1; count++} END {if(count>0) print sum/count; else print "N/A"}')
HEAVY_PEAK_TEMP=$(tail -n +2 "$HEAVY_LOG" | cut -d',' -f2 | awk 'BEGIN{max=0} {if($1+0>max) max=$1} END {print max}')
THROTTLED=$(tail -n +2 "$HEAVY_LOG" | cut -d',' -f6 | grep -v "0x0" | wc -l || echo "0")

echo "  Average power: ${HEAVY_AVG_POWER}W"
echo "  Peak power: ${HEAVY_PEAK_POWER}W"
echo "  Average temp: ${HEAVY_AVG_TEMP}°C"
echo "  Peak temp: ${HEAVY_PEAK_TEMP}°C"
if [ "$THROTTLED" -gt 0 ]; then
    echo -e "  ${RED}⚠ Thermal throttling detected ${THROTTLED} times!${NC}"
else
    echo -e "  ${GREEN}✓ No thermal throttling${NC}"
fi
echo ""

echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Test 4: SUSTAINED LOAD (10 minutes)${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Running LLM queries for 10 minutes to test thermal stability..."
echo "This will take a while. You can Ctrl+C to skip if needed."
echo ""

read -p "Continue with sustained load test? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    SUSTAINED_LOG="$OUTPUT_DIR/sustained_load.log"

    {
        echo "SUSTAINED LOAD TEST"
        echo "Started: $(date)"
        echo "Duration: 10 minutes of continuous LLM queries"
        echo "==========================================="
        echo ""
    } > "$SUSTAINED_LOG"

    echo "Time(s),Temp(°C),Power(W),Throttled" >> "$SUSTAINED_LOG"

    SUSTAINED_START=$(date +%s)
    QUERY_COUNT=0

    while [ $(($(date +%s) - SUSTAINED_START)) -lt 600 ]; do
        QUERY_COUNT=$((QUERY_COUNT + 1))
        ELAPSED=$(($(date +%s) - SUSTAINED_START))
        MIN=$((ELAPSED / 60))
        SEC=$((ELAPSED % 60))

        echo -e "  ${BLUE}[$MIN:$(printf "%02d" $SEC)] Query $QUERY_COUNT${NC}"

        # Run LLM query
        python3 main.py --query "What is the derivative of x^${QUERY_COUNT}?" > /dev/null 2>&1 &
        LLM_PID=$!

        # Monitor while query runs
        while kill -0 $LLM_PID 2>/dev/null; do
            TEMP=$(get_temp)
            THROTTLE=$(get_throttle_status)
            POWER_DATA=$(get_power_data 2>/dev/null || echo "{}")
            POWER=$(echo "$POWER_DATA" | grep -o '"power"[^,]*' | cut -d':' -f2 | tr -d ' "' || echo "N/A")

            echo "$ELAPSED,$TEMP,$POWER,$THROTTLE" >> "$SUSTAINED_LOG"
            echo -e "    Temp: ${TEMP}°C, Power: ${POWER}W"

            sleep 2
        done

        wait $LLM_PID

        # Small break between queries
        sleep 5
    done

    echo ""
    echo -e "${GREEN}✓ Sustained load test complete${NC}"
    echo "  Queries run: $QUERY_COUNT"
    echo "  Log: $SUSTAINED_LOG"

    # Calculate sustained stats
    SUSTAINED_AVG_TEMP=$(tail -n +2 "$SUSTAINED_LOG" | cut -d',' -f2 | awk '{sum+=$1; count++} END {if(count>0) print sum/count; else print "N/A"}')
    SUSTAINED_PEAK_TEMP=$(tail -n +2 "$SUSTAINED_LOG" | cut -d',' -f2 | awk 'BEGIN{max=0} {if($1+0>max) max=$1} END {print max}')
    SUSTAINED_THROTTLED=$(tail -n +2 "$SUSTAINED_LOG" | cut -d',' -f4 | grep -v "0x0" | wc -l || echo "0")

    echo "  Average temp: ${SUSTAINED_AVG_TEMP}°C"
    echo "  Peak temp: ${SUSTAINED_PEAK_TEMP}°C"
    if [ "$SUSTAINED_THROTTLED" -gt 0 ]; then
        echo -e "  ${RED}⚠ Thermal throttling: ${SUSTAINED_THROTTLED} samples${NC}"
    else
        echo -e "  ${GREEN}✓ No thermal throttling${NC}"
    fi
else
    echo "Skipping sustained load test."
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  SUMMARY & BATTERY LIFE ESTIMATE${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

SUMMARY_FILE="$OUTPUT_DIR/SUMMARY.txt"

{
    echo "HOLY CALCULATOR - POWER & THERMAL TEST SUMMARY"
    echo "=============================================="
    echo "Date: $(date)"
    echo "Battery capacity: ${BATTERY_CAPACITY_MAH}mAh"
    echo ""
    echo "POWER CONSUMPTION"
    echo "-----------------"
    echo "Idle:       ${IDLE_AVG_POWER}W"
    echo "Light load: ${LIGHT_AVG_POWER}W (SymPy queries)"
    echo "Heavy load: ${HEAVY_AVG_POWER}W average, ${HEAVY_PEAK_POWER}W peak (LLM query)"
    echo ""
    echo "THERMAL PERFORMANCE"
    echo "-------------------"
    echo "Idle:       ${IDLE_AVG_TEMP}°C"
    echo "Light load: ${LIGHT_AVG_TEMP}°C"
    echo "Heavy load: ${HEAVY_AVG_TEMP}°C average, ${HEAVY_PEAK_TEMP}°C peak"

    if [ "${SUSTAINED_AVG_TEMP:-N/A}" != "N/A" ]; then
        echo "Sustained:  ${SUSTAINED_AVG_TEMP}°C average, ${SUSTAINED_PEAK_TEMP}°C peak"
    fi

    echo ""
    echo "THERMAL THROTTLING"
    echo "------------------"
    if [ "$THROTTLED" -gt 0 ]; then
        echo "⚠ Throttling detected during heavy load"
    else
        echo "✓ No throttling during tests"
    fi

    if [ "${SUSTAINED_THROTTLED:-0}" -gt 0 ]; then
        echo "⚠ Throttling detected during sustained load"
    fi

    echo ""
    echo "BATTERY LIFE ESTIMATES"
    echo "----------------------"

    # Calculate battery life for each scenario
    if [ "$IDLE_AVG_POWER" != "N/A" ] && [ "$(echo "$IDLE_AVG_POWER > 0" | bc)" -eq 1 ]; then
        IDLE_CURRENT=$(echo "$IDLE_AVG_POWER * 1000 / 5" | bc)
        IDLE_HOURS=$(echo "scale=1; $BATTERY_CAPACITY_MAH / $IDLE_CURRENT" | bc)
        echo "Idle only:     ${IDLE_HOURS} hours"
    fi

    if [ "$LIGHT_AVG_POWER" != "N/A" ] && [ "$(echo "$LIGHT_AVG_POWER > 0" | bc)" -eq 1 ]; then
        LIGHT_CURRENT=$(echo "$LIGHT_AVG_POWER * 1000 / 5" | bc)
        LIGHT_HOURS=$(echo "scale=1; $BATTERY_CAPACITY_MAH / $LIGHT_CURRENT" | bc)
        echo "Light load:    ${LIGHT_HOURS} hours"
    fi

    if [ "$HEAVY_AVG_POWER" != "N/A" ] && [ "$(echo "$HEAVY_AVG_POWER > 0" | bc)" -eq 1 ]; then
        HEAVY_CURRENT=$(echo "$HEAVY_AVG_POWER * 1000 / 5" | bc)
        HEAVY_HOURS=$(echo "scale=1; $BATTERY_CAPACITY_MAH / $HEAVY_CURRENT" | bc)
        echo "Heavy load:    ${HEAVY_HOURS} hours"
    fi

    # Mixed workload estimate (70% idle, 20% light, 10% heavy)
    if [ "$IDLE_AVG_POWER" != "N/A" ] && [ "$LIGHT_AVG_POWER" != "N/A" ] && [ "$HEAVY_AVG_POWER" != "N/A" ]; then
        MIXED_POWER=$(echo "scale=2; $IDLE_AVG_POWER * 0.7 + $LIGHT_AVG_POWER * 0.2 + $HEAVY_AVG_POWER * 0.1" | bc)
        MIXED_CURRENT=$(echo "$MIXED_POWER * 1000 / 5" | bc)
        MIXED_HOURS=$(echo "scale=1; $BATTERY_CAPACITY_MAH / $MIXED_CURRENT" | bc)
        echo ""
        echo "Mixed (70/20/10): ${MIXED_HOURS} hours at ${MIXED_POWER}W average"
    fi

    echo ""
    echo "RECOMMENDATIONS FOR ESSAY"
    echo "-------------------------"
    echo "Use these measured values instead of estimates!"
    echo ""
    echo "Data files saved in: $OUTPUT_DIR"

} | tee "$SUMMARY_FILE"

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ALL TESTS COMPLETE! ${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Results saved in: ${BLUE}$OUTPUT_DIR${NC}"
echo ""
echo "Next steps:"
echo "  1. Review $SUMMARY_FILE"
echo "  2. Fill in docs/ESSAY_HARDWARE_NARRATIVE.md with these measurements"
echo "  3. Use this data for your UChicago essay"
echo ""
