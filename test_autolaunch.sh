#!/bin/bash
# Holy Calculator Auto-Launch Test Suite
# Comprehensive testing of auto-launch functionality

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVICE_NAME="holy-calculator.service"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

echo "=========================================="
echo "Holy Calculator Auto-Launch Test Suite"
echo "=========================================="
echo ""

# Test function
run_test() {
    local name="$1"
    local cmd="$2"
    local expected="$3"

    printf "  %-40s" "$name"

    if eval "$cmd" &>/dev/null; then
        if [ "$expected" = "pass" ]; then
            echo -e "${GREEN}PASS${NC}"
            ((PASS++))
        else
            echo -e "${RED}FAIL${NC} (expected to fail)"
            ((FAIL++))
        fi
    else
        if [ "$expected" = "fail" ]; then
            echo -e "${GREEN}PASS${NC} (expected failure)"
            ((PASS++))
        else
            echo -e "${RED}FAIL${NC}"
            ((FAIL++))
        fi
    fi
}

# Warning test (non-critical)
run_warn_test() {
    local name="$1"
    local cmd="$2"

    printf "  %-40s" "$name"

    if eval "$cmd" &>/dev/null; then
        echo -e "${GREEN}PASS${NC}"
        ((PASS++))
    else
        echo -e "${YELLOW}WARN${NC}"
        ((WARN++))
    fi
}

# Section 1: File System Tests
echo -e "${CYAN}[Section 1] File System Tests${NC}"
echo ""

run_test "Service file (local)" "[ -f '$SCRIPT_DIR/holy-calculator.service' ]" "pass"
run_test "Udev rule (local)" "[ -f '$SCRIPT_DIR/99-ti84-calculator.rules' ]" "pass"
run_test "Autolaunch script" "[ -f '$SCRIPT_DIR/autolaunch_main.py' ]" "pass"
run_test "Autolaunch executable" "[ -x '$SCRIPT_DIR/autolaunch_main.py' ]" "pass"
run_test "Install script" "[ -f '$SCRIPT_DIR/install_autolaunch.sh' ]" "pass"
run_test "Install script executable" "[ -x '$SCRIPT_DIR/install_autolaunch.sh' ]" "pass"

echo ""

# Section 2: Environment Tests
echo -e "${CYAN}[Section 2] Environment Tests${NC}"
echo ""

run_test "Virtual environment exists" "[ -d '$SCRIPT_DIR/PICALC_env' ]" "pass"
run_test "Python in venv" "[ -f '$SCRIPT_DIR/PICALC_env/bin/python' ]" "pass"
run_test "Python executable" "[ -x '$SCRIPT_DIR/PICALC_env/bin/python' ]" "pass"
run_warn_test "Python version >= 3.8" "'$SCRIPT_DIR/PICALC_env/bin/python' -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'"

echo ""

# Section 3: Dependency Tests
echo -e "${CYAN}[Section 3] Dependency Tests${NC}"
echo ""

run_test "lsusb available" "command -v lsusb" "pass"
run_test "systemctl available" "command -v systemctl" "pass"
run_test "udevadm available" "command -v udevadm" "pass"

echo ""

# Section 4: Python Module Tests
echo -e "${CYAN}[Section 4] Python Module Tests${NC}"
echo ""

PYTHON="$SCRIPT_DIR/PICALC_env/bin/python"
run_warn_test "Import cascade.calculator_engine" "$PYTHON -c 'import sys; sys.path.insert(0, \"$SCRIPT_DIR/scripts\"); from cascade.calculator_engine import CalculatorEngine'"
run_warn_test "Import hardware.ti84_interface" "$PYTHON -c 'import sys; sys.path.insert(0, \"$SCRIPT_DIR/scripts\"); from hardware.ti84_interface import TI84Interface'"
run_warn_test "Import cascade.pedagogical_wrapper" "$PYTHON -c 'import sys; sys.path.insert(0, \"$SCRIPT_DIR/scripts\"); from cascade.pedagogical_wrapper import PedagogicalWrapper'"

echo ""

# Section 5: Model Tests
echo -e "${CYAN}[Section 5] Model Tests${NC}"
echo ""

MODEL_DIR="$SCRIPT_DIR/models/quantized"
run_test "Model directory exists" "[ -d '$MODEL_DIR' ]" "pass"
run_warn_test "Qwen2.5-Math Q5_K_M model" "[ -f '$MODEL_DIR/qwen2.5-math-7b-instruct-q5km.gguf' ]"
run_warn_test "Qwen2.5-Math Q4_K_M model" "[ -f '$MODEL_DIR/qwen2.5-math-7b-instruct-q4km.gguf' ]"

# Check for any GGUF model
if ls "$MODEL_DIR"/*.gguf &>/dev/null; then
    printf "  %-40s" "Any GGUF model available"
    echo -e "${GREEN}PASS${NC}"
    ((PASS++))
    echo "     Found: $(ls -1 "$MODEL_DIR"/*.gguf | head -1 | xargs basename)"
else
    printf "  %-40s" "Any GGUF model available"
    echo -e "${RED}FAIL${NC}"
    ((FAIL++))
fi

echo ""

# Section 6: System Installation Tests
echo -e "${CYAN}[Section 6] System Installation Tests${NC}"
echo ""

run_warn_test "Service file installed" "[ -f '/etc/systemd/system/$SERVICE_NAME' ]"
run_warn_test "Udev rule installed" "[ -f '/etc/udev/rules.d/99-ti84-calculator.rules' ]"
run_warn_test "Service enabled" "systemctl is-enabled $SERVICE_NAME"

echo ""

# Section 7: USB Device Tests
echo -e "${CYAN}[Section 7] USB Device Tests${NC}"
echo ""

printf "  %-40s" "TI-84 Plus Silver connected"
if lsusb | grep -q "0451:e008"; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS++))
    DEVICE_INFO=$(lsusb | grep "0451:e008")
    echo "     $DEVICE_INFO"
else
    echo -e "${YELLOW}WARN${NC} (not currently connected)"
    ((WARN++))
fi

echo ""

# Section 8: Service Status (if installed)
if [ -f "/etc/systemd/system/$SERVICE_NAME" ]; then
    echo -e "${CYAN}[Section 8] Service Status${NC}"
    echo ""

    printf "  %-40s" "Service loaded"
    if systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
        echo -e "${GREEN}PASS${NC}"
        ((PASS++))
    else
        echo -e "${RED}FAIL${NC}"
        ((FAIL++))
    fi

    printf "  %-40s" "Service active"
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo -e "${GREEN}ACTIVE${NC}"
        ((PASS++))
    else
        echo -e "${YELLOW}INACTIVE${NC} (normal if TI-84 not connected)"
        ((WARN++))
    fi

    echo ""
fi

# Summary
echo "=========================================="
echo "Test Results Summary"
echo "=========================================="
echo ""
echo -e "  ${GREEN}Passed:${NC}   $PASS"
echo -e "  ${RED}Failed:${NC}   $FAIL"
echo -e "  ${YELLOW}Warnings:${NC} $WARN"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}All critical tests passed!${NC}"
    echo ""
    if [ $WARN -gt 0 ]; then
        echo "Some warnings exist but are not critical."
        echo "The auto-launch system should work correctly."
    fi
else
    echo -e "${RED}Some critical tests failed.${NC}"
    echo "Please fix the issues above before using auto-launch."
fi

echo ""
echo "=========================================="
echo "Manual Testing Instructions"
echo "=========================================="
echo ""
echo "1. Connect TI-84 via USB"
echo "2. Put calculator in USB mode (2nd + LINK)"
echo "3. Check service status:"
echo "   sudo systemctl status $SERVICE_NAME"
echo ""
echo "4. View live logs:"
echo "   journalctl -u $SERVICE_NAME -f"
echo ""
echo "5. Monitor USB events:"
echo "   udevadm monitor --environment | grep 0451"
echo ""
echo "6. Test disconnect/reconnect:"
echo "   - Unplug calculator"
echo "   - Wait 5 seconds"
echo "   - Plug back in"
echo "   - Service should auto-restart"
echo ""

exit $FAIL
