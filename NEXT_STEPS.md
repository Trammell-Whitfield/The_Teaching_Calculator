# Holy Calculator - Next Steps Guide

**Last Updated**: November 30, 2025
**Current Phase**: Phase 5 Complete ✅
**Ready For**: Phase 6 - Wolfram Alpha Integration

---

## 🎉 What's Been Accomplished

### ✅ Phase 0-2: LLM Infrastructure
- Environment setup complete
- llama.cpp built with optimizations
- DeepSeek-Math-7B-Instruct downloaded (12.9GB)
- Model quantized to Q4_K_M (3.93GB) - **READY FOR RASPBERRY PI!**
- Model quantized to Q5_K_M (4.6GB) - backup option

### ✅ Code Cleanup (November 28, 2025)
- **main.py**: Reorganized into clean CLI interface
- **requirements.txt**: Removed unnecessary transformers/torch dependencies
- **Directory structure**: Created proper Python package layout
- **Virtual environments**: Removed broken venvs (calc_env, main_calc_env)
- **Documentation**: Created comprehensive organization guides
- **Git**: Updated .gitignore to handle archives and multiple venvs

### ✅ Phase 5: SymPy Integration (November 30, 2025)
- **SymPyHandler**: Full implementation with 7 core methods (520 lines)
- **Test Cases**: 28 comprehensive test problems across 8 categories
- **Test Suite**: Automated testing framework with detailed reporting
- **Success Rate**: 92.9% (26/28 tests passing)
- **Performance**: 0.005s average response time
- **Coverage**: Handles 40-50% of mathematical queries instantly
- **Documentation**: Complete phase summary in docs/phase5-summary.md

---

## 🚀 Immediate Next Steps (Do This Now!)

### Step 1: Create Fresh Virtual Environment (5 minutes)

```bash
# Navigate to project
cd /Users/elhoyabembe/Documents/GitHub/Holy_Calculator

# Create new virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Verify Python version
python --version  # Should be 3.11+

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
python -c "import sympy, numpy, psutil, requests; print('✅ All dependencies installed')"
```

### Step 2: Verify Project Integrity (2 minutes)

```bash
# Test model file
python3 test_model.py

# Check llama.cpp
./llama.cpp/build/bin/llama-cli --version

# View project structure
ls -la

# Read current status
cat PROJECT_STATUS.md
```

### Step 3: Start Phase 5 - SymPy Integration (1-2 hours)

**Goal**: Implement Layer 1 of the cascade (fast, offline symbolic math)

#### 3a. Create Test Cases (15 minutes)

**File**: `data/test-cases/math-problems.yaml`

```yaml
basic_arithmetic:
  - problem: "Calculate: 123 + 456"
    expected_answer: 579
    category: "arithmetic"

basic_algebra:
  - problem: "Solve for x: 2x + 5 = 13"
    expected_answer: "x = 4"
    category: "algebra"

calculus_derivatives:
  - problem: "Find the derivative of f(x) = x^3 + 2x^2 - 5x + 1"
    expected_answer: "f'(x) = 3x^2 + 4x - 5"
    category: "calculus"

# Add 15-20 more test cases covering:
# - Systems of equations
# - Integration
# - Simplification
# - Trigonometry
```

#### 3b. Implement SymPy Handler (45 minutes)

**File**: `scripts/cascade/sympy_handler.py`

**Key Features to Implement:**
1. Natural language parsing (extract equations from queries)
2. SymPy problem detection (can_handle method)
3. Equation solving (solve_equation)
4. Derivatives (compute_derivative)
5. Integrals (compute_integral)
6. Simplification (simplify_expression)
7. Error handling and fallback

**Template structure** (see TODO document Phase 5.1 for full code)

#### 3c. Create Test Suite (30 minutes)

**File**: `scripts/testing/test_sympy_handler.py`

**Test Coverage:**
- Load YAML test cases
- Run each through SymPyHandler
- Track success/failure rates
- Generate test report
- Identify problem categories SymPy handles well

#### 3d. Run Tests and Document Results (15 minutes)

```bash
# Run SymPy test suite
python3 scripts/testing/test_sympy_handler.py > logs/sympy-test-results.txt

# Review results
cat logs/sympy-test-results.txt

# Document findings in docs/phase5-summary.md
```

---

## 📋 Phase 5 Success Criteria

By end of Phase 5, you should have:

- ✅ SymPyHandler class that can solve basic algebra
- ✅ YAML test case database (20+ problems)
- ✅ Test suite showing >80% success rate on basic problems
- ✅ Documentation of which problem types SymPy handles
- ✅ Clear understanding of SymPy's limitations (when to cascade to Layer 2/3)

**Key Metrics:**
- Time to solve: <1 second per problem
- Accuracy: >95% on algebra, calculus
- Coverage: 40-60% of all query types

---

## 🗺️ Future Phases Roadmap

### Phase 6: Wolfram Alpha Integration (2-3 hours)
**Prerequisites:** Phase 5 complete, Wolfram Alpha API key obtained

**Deliverables:**
- Wolfram Alpha API handler
- Rate limiting and caching
- Test suite for Wolfram layer
- API usage tracking

### Phase 7: Cascade Integration (3-4 hours)
**Prerequisites:** Phases 5 and 6 complete

**Deliverables:**
- LLM handler (wrapper for llama.cpp)
- CalculatorEngine orchestrator (manages cascade)
- End-to-end test suite
- Performance comparison (SymPy vs Wolfram vs LLM)
- Updated main.py with full cascade logic

### Phase 8: Hardware Integration (4-6 hours)
**Prerequisites:** Phase 7 complete, hardware available

**Deliverables:**
- TI-84 Plus CE serial interface
- ESP32 wireless bridge
- Power management system
- Hardware test suite

### Phase 9-13: UI, Testing, Optimization, Documentation
**Time Estimate:** 10-12 hours total

---

## 💡 Pro Tips for Phase 5

### 1. Start Simple
Don't try to parse every possible mathematical expression on day 1. Focus on:
- Basic algebra: `2x + 5 = 13`
- Simple derivatives: `x^2 + 3x`
- Simple integrals: `x^2 dx`

### 2. Use SymPy's Built-in Parsing
SymPy has `parse_expr()` - leverage it!
```python
from sympy.parsing.sympy_parser import parse_expr
expr = parse_expr("x**2 + 3*x + 2")
```

### 3. Test Incrementally
After implementing each method (solve, diff, integrate), test it immediately:
```python
if __name__ == "__main__":
    handler = SymPyHandler()
    print(handler.solve_equation("2*x + 5 = 13"))
```

### 4. Don't Overengineer Natural Language Parsing
You're not building GPT - simple regex patterns work well:
```python
if "solve" in query.lower() and "for" in query.lower():
    # Extract equation after colon
    equation = query.split(":")[-1].strip()
```

### 5. Document Limitations
Keep track of what SymPy CAN'T do:
- Word problems (need LLM)
- Proofs (need LLM)
- Complex multi-step reasoning (need LLM)
- Graph plotting (future feature)

This helps define when to cascade to Wolfram or LLM.

---

## 🐛 Troubleshooting

### If SymPy import fails:
```bash
pip install --upgrade sympy
python -c "import sympy; print(sympy.__version__)"
```

### If test cases won't load:
```bash
pip install pyyaml
python -c "import yaml; print('YAML ready')"
```

### If you need to restart:
```bash
deactivate  # Exit current venv
rm -rf venv  # Remove venv
# Then follow Step 1 again
```

---

## 📚 Resources for Phase 5

### SymPy Documentation
- **Tutorial**: https://docs.sympy.org/latest/tutorial/index.html
- **Solving Equations**: https://docs.sympy.org/latest/modules/solvers/solvers.html
- **Calculus**: https://docs.sympy.org/latest/modules/calculus/index.html
- **Parsing**: https://docs.sympy.org/latest/modules/parsing.html

### Example SymPy Code
```python
import sympy as sp

# Define symbol
x = sp.Symbol('x')

# Solve equation
eq = sp.Eq(2*x + 5, 13)
solution = sp.solve(eq, x)  # Returns [4]

# Derivative
f = x**3 + 2*x**2 - 5*x + 1
derivative = sp.diff(f, x)  # Returns 3*x**2 + 4*x - 5

# Integral
integral = sp.integrate(x**2, x)  # Returns x**3/3

# Simplify
expr = (x + 2)*(x - 3)
simplified = sp.expand(expr)  # Returns x**2 - x - 6
```

---

## ✅ Quick Checklist for Today's Session

Before you start coding Phase 5:

- [ ] Fresh virtual environment created (`venv/`)
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Model integrity verified (`python3 test_model.py`)
- [ ] Project structure reviewed (`docs/PROJECT_ORGANIZATION.md`)
- [ ] SymPy documentation reviewed
- [ ] Test case structure understood
- [ ] Text editor/IDE ready

---

## 🎯 End Goal Reminder

**Final Product:**
A portable, battery-powered mathematical problem-solving device that:
1. Takes input from TI-84 calculator
2. Solves problems using 3-layer cascade (SymPy → Wolfram → LLM)
3. Returns answers in <5 seconds for 80% of queries
4. Operates 6-8 hours on battery
5. Works 100% offline (SymPy + LLM)

**You're currently at:** 25% complete (Phases 0-5 done, 8 phases remaining)

**Phase 6 will bring you to:** 35% complete (90%+ of queries solvable with Wolfram!)

---

## 📞 Getting Help

### If You Get Stuck:
1. Check `docs/PROJECT_ORGANIZATION.md` for structure
2. Check `docs/CLEANUP_SUMMARY.md` for what changed
3. Check `PROJECT_STATUS.md` for current state
4. Review the comprehensive TODO document (Phase 5 section)
5. Check SymPy documentation
6. Test components in isolation (Python REPL)

### Debugging Strategy:
```python
# Test SymPy directly
import sympy as sp
x = sp.Symbol('x')
sp.solve(sp.Eq(2*x + 5, 13), x)  # Should return [4]

# Test parsing
from sympy.parsing.sympy_parser import parse_expr
parse_expr("2*x + 5")  # Should return 2*x + 5

# Test your handler
from scripts.cascade.sympy_handler import SymPyHandler
handler = SymPyHandler()
handler.solve_equation("2x + 5 = 13")  # Should work after implementation
```

---

**Ready to start? Run Step 1 (create venv) and dive into Phase 5!**

Good luck! 🚀
