#!/usr/bin/env python3
"""
Comprehensive diagnostic test for LLM fixes on Holy Calculator.

This script tests:
1. Query translation (natural language → symbolic math)
2. LLM answer extraction
3. Performance optimization
4. End-to-end cascade functionality

Run with: python3 test_llm_fixes.py
Run with debug: DEBUG_LLM=1 python3 test_llm_fixes.py
"""

import sys
import time
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from cascade.query_translator import QueryTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠ WARNING: Could not import query_translator: {e}")
    TRANSLATOR_AVAILABLE = False

try:
    from cascade.llm_handler import LLMHandler
    LLM_AVAILABLE = True
except ImportError as e:
    print(f"⚠ WARNING: Could not import llm_handler: {e}")
    LLM_AVAILABLE = False


def test_query_translation():
    """Test natural language query translation."""
    if not TRANSLATOR_AVAILABLE:
        print("\n✗ SKIP: QueryTranslator not available")
        return False

    print("\n" + "="*70)
    print("TEST 1: QUERY TRANSLATION")
    print("="*70)

    translator = QueryTranslator()

    test_cases = [
        ("derivative of x^2", "derivative", "diff(x**2, x)"),
        ("integrate cos(x)", "integral", "integrate(cos(x), x)"),
        ("solve 2x + 5 = 13", "solve", "solve(2*x + 5 = 13, x)"),
        ("second derivative of x^3", "second_derivative", "diff(x**3, x, 2)"),
        ("factor x^2 + 5x + 6", "factor", "factor(x**2 + 5*x + 6)"),
    ]

    passed = 0
    failed = 0

    for query, expected_op, expected_sympy_substr in test_cases:
        print(f"\n  Query: {query}")
        result = translator.translate(query)

        print(f"    Operation: {result['operation']}")
        print(f"    Expression: {result['expression']}")
        print(f"    SymPy: {result['sympy_format']}")
        print(f"    LLM: {result['llm_format'][:60]}...")

        # Validation
        if result['operation'] == expected_op:
            if expected_sympy_substr.replace(" ", "") in result['sympy_format'].replace(" ", ""):
                print(f"    ✓ PASS")
                passed += 1
            else:
                print(f"    ✗ FAIL - SymPy format incorrect")
                print(f"      Expected substring: {expected_sympy_substr}")
                failed += 1
        else:
            print(f"    ✗ FAIL - Operation mismatch")
            print(f"      Expected: {expected_op}, Got: {result['operation']}")
            failed += 1

    print(f"\n  Translation Tests: {passed}/{len(test_cases)} passed")
    return failed == 0


def test_llm_availability():
    """Test if LLM handler can be initialized."""
    if not LLM_AVAILABLE:
        print("\n✗ SKIP: LLMHandler not available")
        return False

    print("\n" + "="*70)
    print("TEST 2: LLM HANDLER AVAILABILITY")
    print("="*70)

    try:
        handler = LLMHandler()
        print(f"  ✓ LLM Handler initialized")
        print(f"    Model: {handler.model_path.name}")
        print(f"    Binary: {handler.llama_cli}")
        print(f"    Parameters:")
        print(f"      n_predict: {handler.default_params['n_predict']}")
        print(f"      temperature: {handler.default_params['temperature']}")
        print(f"      repeat_penalty: {handler.default_params['repeat_penalty']}")
        print(f"      threads: {handler.default_params['threads']}")
        return True
    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        return False


def test_llm_query():
    """Test LLM query execution with answer extraction."""
    if not LLM_AVAILABLE:
        print("\n✗ SKIP: LLMHandler not available")
        return False

    print("\n" + "="*70)
    print("TEST 3: LLM QUERY EXECUTION")
    print("="*70)
    print("  (This may take 10-60 seconds...)")

    try:
        handler = LLMHandler()

        # Simple test query
        test_query = (
            "Find the derivative of x^2 with respect to x. "
            "Show your work step by step. "
            "State the final answer clearly after 'The answer is:'"
        )

        print(f"\n  Query: {test_query[:60]}...")

        start_time = time.time()
        result = handler.query(test_query)
        elapsed = time.time() - start_time

        print(f"\n  Results:")
        print(f"    Success: {result['success']}")
        print(f"    Time: {elapsed:.1f}s")
        print(f"    Answer: {result.get('result', 'None')}")

        if result['success']:
            answer = result.get('result')
            if answer and answer != 'None' and len(str(answer).strip()) > 0:
                print(f"    ✓ PASS - Got valid answer")
                return True
            else:
                print(f"    ✗ FAIL - Answer is None or empty")
                return False
        else:
            print(f"    ✗ FAIL - Query failed: {result.get('error')}")
            return False

    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance():
    """Test that performance is within expected bounds."""
    if not LLM_AVAILABLE:
        print("\n✗ SKIP: LLMHandler not available")
        return False

    print("\n" + "="*70)
    print("TEST 4: PERFORMANCE CHECK")
    print("="*70)

    try:
        handler = LLMHandler()

        # Expected performance targets
        expected_n_predict = 256
        expected_temp_min = 0.2
        expected_temp_max = 0.5

        params = handler.default_params

        print(f"\n  Parameter Check:")
        print(f"    n_predict: {params['n_predict']} (target: {expected_n_predict})")
        print(f"    temperature: {params['temperature']} (target: {expected_temp_min}-{expected_temp_max})")
        print(f"    repeat_penalty: {params['repeat_penalty']} (target: ≥1.1)")

        checks_passed = 0
        checks_total = 3

        if params['n_predict'] <= expected_n_predict:
            print(f"      ✓ n_predict is optimized")
            checks_passed += 1
        else:
            print(f"      ✗ n_predict too high (may cause slow responses)")

        if expected_temp_min <= params['temperature'] <= expected_temp_max:
            print(f"      ✓ temperature in optimal range")
            checks_passed += 1
        else:
            print(f"      ✗ temperature out of optimal range")

        if params['repeat_penalty'] >= 1.1:
            print(f"      ✓ repeat_penalty set to prevent loops")
            checks_passed += 1
        else:
            print(f"      ✗ repeat_penalty too low")

        print(f"\n  Performance checks: {checks_passed}/{checks_total} passed")
        return checks_passed == checks_total

    except Exception as e:
        print(f"  ✗ FAIL: {e}")
        return False


def main():
    """Run all diagnostic tests."""
    print("\n" + "="*70)
    print("HOLY CALCULATOR - LLM FIX DIAGNOSTIC SUITE")
    print("="*70)
    print("\nThis script tests the LLM fixes for:")
    print("  1. Query translation (natural language → math)")
    print("  2. LLM handler availability")
    print("  3. LLM query execution and answer extraction")
    print("  4. Performance optimization")

    results = {}

    # Test 1: Query translation
    results['translation'] = test_query_translation()

    # Test 2: LLM availability
    results['llm_available'] = test_llm_availability()

    # Test 3: LLM query (only if LLM available)
    if results['llm_available']:
        results['llm_query'] = test_llm_query()
    else:
        results['llm_query'] = None

    # Test 4: Performance
    if results['llm_available']:
        results['performance'] = test_performance()
    else:
        results['performance'] = None

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    passed = sum(1 for v in results.values() if v is True)
    total = sum(1 for v in results.values() if v is not None)
    skipped = sum(1 for v in results.values() if v is None)

    print(f"\nTests passed: {passed}/{total}")
    if skipped > 0:
        print(f"Tests skipped: {skipped}")

    print(f"\nDetailed Results:")
    for test_name, result in results.items():
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "✗ FAIL"
        else:
            status = "- SKIP"
        print(f"  {test_name:20s}: {status}")

    print(f"\n{'='*70}")

    if passed == total and total > 0:
        print("✓ ALL TESTS PASSED - LLM fixes are working correctly!")
        return 0
    elif passed > 0:
        print(f"⚠ PARTIAL SUCCESS - {passed}/{total} tests passed")
        print("  Review failed tests above for issues to fix")
        return 1
    else:
        print("✗ ALL TESTS FAILED - Review errors above")
        return 2


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
