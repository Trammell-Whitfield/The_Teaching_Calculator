#!/bin/bash
# Pre-Deployment Check Script
# Quick verification before deploying to Raspberry Pi

set -e

echo "========================================================================"
echo "HOLY CALCULATOR - PRE-DEPLOYMENT CHECK"
echo "========================================================================"
echo ""
echo "This script performs a quick health check before Pi deployment."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CHECKS_PASSED=0
CHECKS_FAILED=0

# Helper function for checks
check() {
    local description=$1
    local command=$2

    echo -n "  [$description]... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC}"
        ((CHECKS_FAILED++))
        return 1
    fi
}

# 1. Dependencies
echo -e "${BLUE}1. Checking Dependencies${NC}"
./scripts/validate_dependencies.sh > /tmp/holy_calc_deps.log 2>&1
if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}✓ All dependencies validated${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "   ${RED}✗ Dependency issues found (see /tmp/holy_calc_deps.log)${NC}"
    ((CHECKS_FAILED++))
fi
echo ""

# 2. Model verification
echo -e "${BLUE}2. Verifying Models${NC}"
model_exists=0

for model in models/quantized/*.gguf; do
    if [ -f "$model" ]; then
        size=$(du -h "$model" | cut -f1)
        echo -e "   ${GREEN}✓${NC} $(basename $model) ($size)"
        ((CHECKS_PASSED++))
        model_exists=1
    fi
done

if [ $model_exists -eq 0 ]; then
    echo -e "   ${RED}✗ No .gguf models found${NC}"
    ((CHECKS_FAILED++))
fi
echo ""

# 3. Run quick tests
echo -e "${BLUE}3. Running Quick Tests${NC}"

# Test SymPy layer
echo -n "   Testing SymPy layer... "
if python3 -c "
import sys
sys.path.insert(0, 'scripts')
from cascade.sympy_handler import SymPyHandler
handler = SymPyHandler()
result = handler.process_query('Solve: x + 1 = 2')
assert result['success'], 'SymPy test failed'
" 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC}"
    ((CHECKS_FAILED++))
fi

# Test LLM handler initialization (without loading model)
echo -n "   Testing LLM handler init... "
if python3 -c "
import sys
sys.path.insert(0, 'scripts')
from cascade.llm_handler import LLMHandler
# Just test that class can be imported
" 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC}"
    ((CHECKS_FAILED++))
fi

# Test calculator engine import
echo -n "   Testing CalculatorEngine... "
if python3 -c "
import sys
sys.path.insert(0, 'scripts')
from cascade.calculator_engine import CalculatorEngine, MathQueryRouter
# Just test that classes can be imported
" 2>/dev/null; then
    echo -e "${GREEN}✓${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "${RED}✗${NC}"
    ((CHECKS_FAILED++))
fi

echo ""

# 4. Check disk space
echo -e "${BLUE}4. Disk Space Check${NC}"
available=$(df -h . | awk 'NR==2 {print $4}')
echo -e "   Available space: $available"

# Check if we have at least 1GB free
available_kb=$(df -k . | awk 'NR==2 {print $4}')
if [ $available_kb -gt 1048576 ]; then
    echo -e "   ${GREEN}✓ Sufficient disk space${NC}"
    ((CHECKS_PASSED++))
else
    echo -e "   ${YELLOW}⚠ Low disk space (<1GB free)${NC}"
    ((CHECKS_FAILED++))
fi
echo ""

# 5. Git status
echo -e "${BLUE}5. Git Repository Status${NC}"
if [ -d .git ]; then
    # Check for uncommitted changes
    if git diff-index --quiet HEAD -- 2>/dev/null; then
        echo -e "   ${GREEN}✓ No uncommitted changes${NC}"
        ((CHECKS_PASSED++))
    else
        echo -e "   ${YELLOW}⚠ Uncommitted changes present${NC}"
        echo "   Consider committing before deployment"
    fi

    # Show current branch
    branch=$(git branch --show-current)
    echo -e "   Current branch: ${BLUE}$branch${NC}"
else
    echo -e "   ${YELLOW}⚠ Not a git repository${NC}"
fi
echo ""

# 6. Check for .env file (Wolfram Alpha)
echo -e "${BLUE}6. Configuration Files${NC}"
if [ -f .env ]; then
    if grep -q "WOLFRAM_ALPHA_APP_ID" .env 2>/dev/null; then
        echo -e "   ${GREEN}✓ Wolfram Alpha API key configured${NC}"
        ((CHECKS_PASSED++))
    else
        echo -e "   ${YELLOW}⚠ .env exists but no Wolfram key${NC}"
    fi
else
    echo -e "   ${YELLOW}⚠ No .env file (Wolfram Alpha disabled)${NC}"
fi
echo ""

# 7. Platform detection test
echo -e "${BLUE}7. Platform Detection${NC}"
if [ -f scripts/platform_config.py ]; then
    platform_info=$(python3 scripts/platform_config.py 2>/dev/null || echo "unknown")
    echo "   Current platform: $platform_info"
    ((CHECKS_PASSED++))
else
    echo -e "   ${YELLOW}⚠ Platform detection not available${NC}"
fi
echo ""

# Summary
echo "========================================================================"
echo "SUMMARY"
echo "========================================================================"
echo -e "${GREEN}Passed:${NC} $CHECKS_PASSED"
echo -e "${RED}Failed:${NC} $CHECKS_FAILED"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL CHECKS PASSED!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run full test suite: python3 scripts/testing/test_integration.py"
    echo "  2. Prepare for Pi: ./scripts/deployment/prepare_for_pi.sh"
    echo "  3. Transfer to Pi: ./scripts/deployment/transfer_to_pi.sh"
    echo ""
    exit 0
else
    echo -e "${YELLOW}⚠️  SOME CHECKS FAILED${NC}"
    echo ""
    echo "Review failures above before deployment."
    echo "You may still proceed, but address critical issues first."
    echo ""
    exit 1
fi
