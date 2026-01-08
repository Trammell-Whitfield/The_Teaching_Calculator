# Holy Calculator - Test Suite

This directory contains comprehensive tests for the Holy Calculator system.

## Test Files

### Unit Tests
- **`test_sympy_handler.py`** - Tests for SymPy layer (Layer 1)
  - 28 test cases across algebra, calculus, trigonometry, etc.
  - 92.9% success rate
  - Run: `python3 scripts/testing/test_sympy_handler.py`

- **`test_wolfram_handler.py`** - Tests for Wolfram Alpha layer (Layer 2)
  - Requires API key in `.env`
  - Tests API communication, rate limiting, caching
  - Run: `python3 scripts/testing/test_wolfram_handler.py`

### Integration Tests
- **`test_cascade.py`** - Tests cascade orchestration (Phase 7)
  - Router logic testing
  - Cascade fallback mechanism
  - Performance benchmarks
  - Statistics tracking
  - Run: `python3 scripts/testing/test_cascade.py [--enable-wolfram]`

- **`test_integration.py`** - **NEW** Comprehensive integration tests
  - End-to-end system validation
  - Error handling and edge cases
  - Performance targets
  - 8 test suites covering:
    - Basic arithmetic
    - Algebra
    - Calculus
    - Cascade routing
    - Error handling
    - Performance targets
    - Cascade fallback
    - Statistics tracking
  - Run: `python3 scripts/testing/test_integration.py [--enable-wolfram]`

### Model Comparison
- **`compare_llm_models.py`** - Compare different LLM models (Phase 7.5)
  - Tested Qwen2.5-Math vs DeepSeek-Math
  - Result: Qwen2.5-Math selected (83.6% accuracy on MATH benchmark)

## Validation Scripts

### Dependency Validation
- **`../validate_dependencies.sh`** - **NEW** Validates all dependencies
  - Checks Python version (3.8+)
  - Verifies Python packages
  - Checks llama.cpp build
  - Validates model files
  - Tests cascade system imports
  - Platform detection
  - Run: `./scripts/validate_dependencies.sh`

### Pre-Deployment Check
- **`../pre_deployment_check.sh`** - **NEW** Quick pre-deployment validation
  - Runs dependency validation
  - Verifies models exist
  - Runs quick smoke tests
  - Checks disk space
  - Git status check
  - Platform detection test
  - Run: `./scripts/pre_deployment_check.sh`

## Quick Start

### Run All Tests (Fast - No LLM)
```bash
# Just SymPy and cascade tests (< 1 minute)
python3 scripts/testing/test_cascade.py
```

### Run Comprehensive Tests (Slow - Includes LLM)
```bash
# Full integration test suite (3-5 minutes)
python3 scripts/testing/test_integration.py
```

### Pre-Deployment Checklist
```bash
# 1. Validate dependencies
./scripts/validate_dependencies.sh

# 2. Run quick checks
./scripts/pre_deployment_check.sh

# 3. Run integration tests
python3 scripts/testing/test_integration.py

# 4. If all pass, you're ready for Pi deployment!
```

## Test Results

### Expected Results (on macOS/Desktop)

**SymPy Layer:**
- Success rate: 92.9% (26/28 tests)
- Average response time: 0.005s

**Cascade System:**
- Router accuracy: ~90%
- Overall success rate: ~95% (all layers enabled)
- Average response time: <5s

**Integration Tests:**
- All 8 test suites should pass
- Performance targets: SymPy queries < 1s

### Expected Results (on Raspberry Pi 5)

**Model Performance:**
- Q5_K_M (16GB): 1-2 tokens/sec
- Q4_K_M (8GB): 2-3 tokens/sec
- Model load time: 10-25 seconds

**System Performance:**
- SymPy: Same as desktop (~0.005s)
- LLM: Slower than desktop (5-15s for simple queries)
- Overall: Still functional, battery-optimized

## Troubleshooting

### Import Errors
```bash
# Ensure you're running from project root
cd /path/to/Holy-calc-pi
python3 scripts/testing/test_integration.py
```

### Model Not Found
```bash
# Check models directory
ls -lh models/quantized/*.gguf

# If missing, download and quantize models first
```

### LLM Tests Timeout
```bash
# Normal on first run (model loading takes 10-25s)
# Subsequent queries should be faster
```

### Wolfram Tests Fail
```bash
# Check API key is set
cat .env | grep WOLFRAM_ALPHA_APP_ID

# Run with Wolfram disabled
python3 scripts/testing/test_integration.py
```

## Adding New Tests

### Unit Test Template
```python
def test_new_feature(engine):
    """Test description."""
    test_cases = [
        ("query1", "expected_result1"),
        ("query2", "expected_result2"),
    ]

    passed = 0
    for query, expected in test_cases:
        result = engine.solve(query)
        if result['success']:
            passed += 1

    return passed == len(test_cases)
```

### Integration Test Template
```python
def test_new_integration(self) -> bool:
    """Test new integration scenario."""
    print("\nTEST X: New Integration")
    print("="*70)

    # Your test logic here
    passed, failed = self._run_test_cases(test_cases)

    print(f"\n✓ Passed: {passed}/{len(test_cases)}")
    return failed == 0
```

## Continuous Integration

When CI/CD is set up, tests will run automatically on:
- Every commit (fast tests only)
- Pull requests (full test suite)
- Before deployment (pre-deployment checks)

## Performance Benchmarks

Track these metrics:
- **SymPy success rate**: Target 90%+
- **Overall success rate**: Target 95%+
- **SymPy response time**: Target <1s
- **LLM response time**: Target <30s (Pi), <10s (desktop)
- **Cascade efficiency**: Target 80%+ solved in Layer 1-2

## Next Steps

1. Run tests on your development machine ✓
2. Transfer to Raspberry Pi
3. Run tests on Pi (benchmark Pi performance)
4. Compare results (desktop vs Pi)
5. Optimize based on Pi results
6. Deploy to production!
