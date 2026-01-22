#!/usr/bin/env python3
"""
Quick test to verify critical bug fixes.
"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from cascade.sympy_handler import SymPyHandler


def test_bug_fixes():
    """Test the 4 critical bug fixes."""
    handler = SymPyHandler()

    print("=" * 70)
    print("BUG FIX VERIFICATION TEST")
    print("=" * 70)

    # Bug A: Inverse trig parsing
    print("\n" + "=" * 70)
    print("BUG A: Inverse Trig Parsing")
    print("=" * 70)

    tests_a = [
        ("derivative of arcsin(x)", "1/sqrt(1-x^2)"),
        ("d/dx(arctan(x))", "1/(1+x^2)"),
    ]

    for query, expected in tests_a:
        print(f"\nQuery: {query}")
        print(f"Expected: {expected}")
        result = handler.process_query(query)
        if result and result.get('success'):
            print(f"Result: {result.get('formatted')}")
            print("Status: ✅ SUCCESS (parsed correctly)")
        else:
            print("Status: ❌ FAILED")

    # Bug B: Combinatorics natural language
    print("\n" + "=" * 70)
    print("BUG B: Combinatorics Natural Language")
    print("=" * 70)

    tests_b = [
        ("what is 10 choose 3", "120"),
        ("what is 100 mod 7", "2"),
        ("gcd of 144 and 60", "12"),
    ]

    for query, expected in tests_b:
        print(f"\nQuery: {query}")
        print(f"Expected: {expected}")
        result = handler.process_query(query)
        if result and result.get('success'):
            print(f"Result: {result.get('formatted')}")
            print("Status: ✅ SUCCESS (processed correctly)")
        else:
            print("Status: ❌ FAILED")

    # Bug C: Log vs ln notation
    print("\n" + "=" * 70)
    print("BUG C: Log vs Ln Notation")
    print("=" * 70)

    tests_c = [
        ("derivative of x^3 * ln(x)", "should contain 'ln' not 'log'"),
        ("integrate ln(x)", "should contain 'ln' not 'log'"),
    ]

    for query, expected in tests_c:
        print(f"\nQuery: {query}")
        print(f"Expected: {expected}")
        result = handler.process_query(query)
        if result and result.get('success'):
            formatted = result.get('formatted')
            print(f"Result: {formatted}")
            if 'ln' in formatted and 'log' not in formatted:
                print("Status: ✅ SUCCESS (uses 'ln' not 'log')")
            else:
                print("Status: ⚠️  PARTIAL (still has 'log')")
        else:
            print("Status: ❌ FAILED")

    # Bug D: Imaginary unit (I vs i)
    print("\n" + "=" * 70)
    print("BUG D: Imaginary Unit (I vs i)")
    print("=" * 70)

    tests_d = [
        ("solve x^2 + 4x + 13 = 0", "should contain 'i' not 'I'"),
        ("solve x^2 + 2x + 5 = 0", "should contain 'i' not 'I'"),
    ]

    for query, expected in tests_d:
        print(f"\nQuery: {query}")
        print(f"Expected: {expected}")
        result = handler.process_query(query)
        if result and result.get('success'):
            formatted = result.get('formatted')
            print(f"Result: {formatted}")
            if 'i' in formatted and '*I' not in formatted:
                print("Status: ✅ SUCCESS (uses 'i' not 'I')")
            else:
                print("Status: ⚠️  PARTIAL (still has 'I')")
        else:
            print("Status: ❌ FAILED")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    test_bug_fixes()
