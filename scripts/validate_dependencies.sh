#!/bin/bash
# Validate Dependencies for Holy Calculator
# Checks that all required dependencies are installed and functioning

set -e  # Exit on error

echo "========================================================================"
echo "HOLY CALCULATOR - DEPENDENCY VALIDATION"
echo "========================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
PASSED=0
FAILED=0
WARNINGS=0

# Function to test a dependency
test_dependency() {
    local name=$1
    local test_cmd=$2

    echo -n "Testing $name... "
    if eval "$test_cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC}"
        ((FAILED++))
        return 1
    fi
}

# Function to test Python import
test_python_import() {
    local module=$1
    local import_name=${2:-$module}

    test_dependency "$module" "python3 -c 'import $import_name'"
}

# 1. Python version
echo "1. Core Dependencies:"
echo "-------------------"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo -n "Python version ($python_version)... "
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo -e "${GREEN}✓${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ (Requires Python 3.8+)${NC}"
    ((FAILED++))
fi

# 2. Core Python packages
echo ""
echo "2. Python Packages:"
echo "-------------------"
test_python_import "sympy"
test_python_import "numpy"
test_python_import "psutil"
test_python_import "requests"
test_python_import "pyyaml" "yaml"
test_python_import "python-dotenv" "dotenv"

# 3. Optional packages
echo ""
echo "3. Optional Packages:"
echo "--------------------"
if python3 -c "import wolframalpha" 2>/dev/null; then
    echo -e "Wolfram Alpha client... ${GREEN}✓${NC}"
    ((PASSED++))
else
    echo -e "Wolfram Alpha client... ${YELLOW}⚠ (Optional - for Layer 2)${NC}"
    ((WARNINGS++))
fi

# 4. llama.cpp binary
echo ""
echo "4. LLM Infrastructure:"
echo "---------------------"
if [ -f "llama.cpp/build/bin/llama-cli" ]; then
    echo -e "llama-cli binary... ${GREEN}✓${NC}"
    ((PASSED++))

    # Test if it runs
    if ./llama.cpp/build/bin/llama-cli --version > /dev/null 2>&1; then
        echo -e "llama-cli executable... ${GREEN}✓${NC}"
        ((PASSED++))
    else
        echo -e "llama-cli executable... ${RED}✗ (Binary exists but won't run)${NC}"
        ((FAILED++))
    fi
else
    echo -e "llama-cli binary... ${RED}✗ (Run: cd llama.cpp && mkdir build && cd build && cmake .. && make)${NC}"
    ((FAILED++))
fi

# 5. Model files
echo ""
echo "5. Model Files:"
echo "--------------"
model_found=0

# Check for Qwen models (preferred)
if [ -f "models/quantized/qwen2.5-math-7b-instruct-q5km.gguf" ]; then
    echo -e "Qwen2.5-Math Q5_K_M... ${GREEN}✓${NC}"
    ((PASSED++))
    model_found=1
elif [ -f "models/quantized/qwen2.5-math-7b-instruct-q4km.gguf" ]; then
    echo -e "Qwen2.5-Math Q4_K_M... ${GREEN}✓${NC}"
    ((PASSED++))
    model_found=1
else
    echo -e "Qwen2.5-Math models... ${YELLOW}⚠ (Not found, checking fallback)${NC}"
    ((WARNINGS++))
fi

# Check for DeepSeek models (fallback)
if [ -f "models/quantized/deepseek-math-7b-q5km.gguf" ]; then
    echo -e "DeepSeek-Math Q5_K_M... ${GREEN}✓${NC}"
    ((PASSED++))
    model_found=1
elif [ -f "models/quantized/deepseek-math-7b-q4km.gguf" ]; then
    echo -e "DeepSeek-Math Q4_K_M... ${GREEN}✓${NC}"
    ((PASSED++))
    model_found=1
fi

if [ $model_found -eq 0 ]; then
    echo -e "${RED}✗ No quantized models found!${NC}"
    echo "   Run model download and quantization first."
    ((FAILED++))
fi

# 6. Directory structure
echo ""
echo "6. Directory Structure:"
echo "----------------------"
required_dirs=("scripts/cascade" "scripts/testing" "models/quantized" "data/test-cases" "logs")

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "$dir... ${GREEN}✓${NC}"
        ((PASSED++))
    else
        echo -e "$dir... ${RED}✗${NC}"
        ((FAILED++))
    fi
done

# 7. Test imports from cascade system
echo ""
echo "7. Cascade System Imports:"
echo "-------------------------"
test_dependency "SymPyHandler" "python3 -c 'import sys; sys.path.insert(0, \"scripts\"); from cascade.sympy_handler import SymPyHandler'"
test_dependency "WolframAlphaHandler" "python3 -c 'import sys; sys.path.insert(0, \"scripts\"); from cascade.wolfram_handler import WolframAlphaHandler'"
test_dependency "LLMHandler" "python3 -c 'import sys; sys.path.insert(0, \"scripts\"); from cascade.llm_handler import LLMHandler'"
test_dependency "CalculatorEngine" "python3 -c 'import sys; sys.path.insert(0, \"scripts\"); from cascade.calculator_engine import CalculatorEngine'"

# 8. Platform detection
echo ""
echo "8. Platform Configuration:"
echo "-------------------------"
if [ -f "scripts/platform_config.py" ]; then
    echo -e "platform_config.py... ${GREEN}✓${NC}"
    ((PASSED++))

    if python3 scripts/platform_config.py > /dev/null 2>&1; then
        echo -e "Platform detection... ${GREEN}✓${NC}"
        ((PASSED++))
    else
        echo -e "Platform detection... ${RED}✗${NC}"
        ((FAILED++))
    fi
else
    echo -e "platform_config.py... ${YELLOW}⚠ (Optional - for Pi optimization)${NC}"
    ((WARNINGS++))
fi

# Summary
echo ""
echo "========================================================================"
echo "VALIDATION SUMMARY"
echo "========================================================================"
echo -e "${GREEN}Passed:${NC}   $PASSED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "${RED}Failed:${NC}   $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All critical dependencies validated!${NC}"
    echo "  Ready to run tests and deploy."
    exit 0
elif [ $FAILED -le 2 ]; then
    echo -e "${YELLOW}⚠ Some dependencies missing.${NC}"
    echo "  Review failures above before deployment."
    exit 1
else
    echo -e "${RED}✗ Multiple dependencies missing!${NC}"
    echo "  Fix critical issues before proceeding."
    exit 2
fi
