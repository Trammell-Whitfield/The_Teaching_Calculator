#!/usr/bin/env python3
"""
Quick test script to verify calculator functionality
"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from cascade.sympy_handler import SymPyHandler
from cascade.query_translator import QueryTranslator

def test_sympy_directly():
    """Test SymPy handler with various queries."""
    print("="*70)
    print("TESTING SYMPY HANDLER DIRECTLY")
    print("="*70)

    handler = SymPyHandler()
    translator = QueryTranslator()

    test_queries = [
        "derivative of x^3",
        "d/dx(sin(x))",
        "differentiate x^2 + 3x + 5",
        "what is the derivative of e^x?",
        "find d/dx of cos(2x)",
        "d/dx(ln(x))",
        "solve 2x + 5 = 13",
        "simplify (x^2 - 1)/(x - 1)",
    ]

    results = []

    for query in test_queries:
        print(f"\nQuery: '{query}'")

        # Step 1: Translate natural language to SymPy expression
        translated = translator.translate(query)
        print(f"  Translated: {translated}")

        # Step 2: Solve with SymPy
        result = handler.process_query(query)
        print(f"  Result: {result}")

        success = result is not None and result.get('success', False)
        results.append({
            'query': query,
            'translated': translated,
            'result': result.get('formatted') if result else None,
            'success': success,
            'error': None if result else 'No result returned'
        })
        print(f"  Success: {success}")

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    successful = sum(1 for r in results if r['success'])
    print(f"Successful: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")

    print("\nFailed queries:")
    for r in results:
        if not r['success']:
            print(f"  - '{r['query']}': {r['error']}")

    return results

if __name__ == '__main__':
    results = test_sympy_directly()
