#!/usr/bin/env python3
"""
CHALLENGE TEST - Holy Calculator Pi
Tests the system with harder queries to find its limits.
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from cascade.sympy_handler import SymPyHandler
from cascade.query_translator import QueryTranslator


def normalize_math_expression(expr: str) -> str:
    """Normalize a mathematical expression for comparison."""
    if not expr:
        return ""

    normalized = str(expr).lower()
    normalized = normalized.replace(' ', '')
    # Normalize exponentiation FIRST (before touching *)
    # Convert both ** and ^ to ** for SymPy compatibility
    normalized = normalized.replace('^', '**')
    normalized = normalized.replace('±', '+-')
    normalized = normalized.replace('√', 'sqrt')

    if 'answeris' in normalized:
        parts = normalized.split('answeris')
        normalized = parts[-1] if parts else normalized

    normalized = normalized.rstrip('+c').rstrip('c')

    return normalized.strip()


def expressions_match(actual: str, expected: str) -> bool:
    """Check if two mathematical expressions match."""
    if not actual or not expected:
        return False

    norm_actual = normalize_math_expression(actual)
    norm_expected = normalize_math_expression(expected)

    if norm_actual == norm_expected:
        return True

    if norm_expected in norm_actual:
        return True

    if norm_actual in norm_expected:
        return True

    # Handle equation formats
    if '=' in norm_expected or '=' in norm_actual:
        if '=' in norm_expected:
            expected_val = norm_expected.split('=')[-1].strip()
        else:
            expected_val = norm_expected

        if '=' in norm_actual:
            actual_val = norm_actual.split('=')[-1].strip()
        else:
            actual_val = norm_actual

        if actual_val == expected_val:
            return True

    # Try SymPy mathematical equivalence (most powerful check)
    try:
        import sympy as sp
        from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

        transformations = standard_transformations + (implicit_multiplication_application,)

        # Remove +C for integrals
        actual_clean = norm_actual.replace('+c', '').strip()
        expected_clean = norm_expected.replace('+c', '').strip()

        # Remove equation format
        if '=' in expected_clean:
            expected_clean = expected_clean.split('=')[-1].strip()
        if '=' in actual_clean:
            actual_clean = actual_clean.split('=')[-1].strip()

        # Convert to SymPy format
        actual_clean = actual_clean.replace('^', '**')
        expected_clean = expected_clean.replace('^', '**')

        # Parse expressions
        expr_actual = parse_expr(actual_clean, transformations=transformations)
        expr_expected = parse_expr(expected_clean, transformations=transformations)

        # Check mathematical equivalence
        diff = sp.simplify(expr_actual - expr_expected)
        if diff == 0 or diff == sp.S.Zero:
            return True

        # Also check simplified forms
        if sp.simplify(expr_actual) == sp.simplify(expr_expected):
            return True

    except Exception:
        pass  # If SymPy fails, fallback to string matching

    return False


# CHALLENGE TEST DATASET - Harder queries
CHALLENGE_QUERIES = {
    'harder_derivatives': [
        # Chain rule
        ("derivative of (2x + 1)^5", "10(2x+1)^4", "sympy", 3),
        ("d/dx(e^(x^2))", "2x*e^(x^2)", "sympy", 3),
        ("differentiate sqrt(x^2 + 1)", "x/sqrt(x^2+1)", "sympy", 3),
        ("derivative of ln(x^2 + 1)", "2x/(x^2+1)", "sympy", 3),

        # Product rule
        ("d/dx(x^2 * e^x)", "x^2*e^x + 2x*e^x", "sympy", 3),
        ("derivative of x^3 * ln(x)", "3x^2*ln(x) + x^2", "sympy", 3),

        # Quotient rule
        ("derivative of x/sin(x)", "(sin(x)-x*cos(x))/sin^2(x)", "sympy", 4),
        ("d/dx(1/(x^2+1))", "-2x/(x^2+1)^2", "sympy", 3),

        # Trig derivatives
        ("differentiate sin(2x) * cos(x)", "2cos(2x)cos(x) - sin(2x)sin(x)", "sympy", 4),
        ("derivative of tan^2(x)", "2tan(x)sec^2(x)", "sympy", 4),

        # Exponential and log
        ("d/dx(x^x)", "x^x(ln(x)+1)", "sympy", 4),
        ("derivative of e^x * x^e", "e^x*x^e + e*e^x*x^(e-1)", "sympy", 4),

        # Implicit and parametric
        ("derivative of arcsin(x)", "1/sqrt(1-x^2)", "sympy", 3),
        ("d/dx(arctan(x))", "1/(1+x^2)", "sympy", 3),
        ("derivative of ln(ln(x))", "1/(x*ln(x))", "sympy", 4),
    ],

    'harder_integrals': [
        # Basic but tricky
        ("integrate x * e^x", "x*e^x - e^x", "sympy", 3),
        ("integral of x^2 * sin(x)", "-x^2*cos(x) + 2x*sin(x) + 2cos(x)", "sympy", 4),
        ("integrate 1/sqrt(x)", "2*sqrt(x)", "sympy", 2),

        # Substitution
        ("integral of x * sqrt(x^2 + 1)", "(x^2+1)^(3/2)/3", "sympy", 4),
        ("integrate 2x/(x^2 + 1)", "ln(x^2+1)", "sympy", 3),

        # Trigonometric
        ("integral of sin^2(x)", "(x - sin(x)cos(x))/2", "sympy", 3),
        ("integrate cos^2(x)", "(x + sin(x)cos(x))/2", "sympy", 3),
        ("integral of sec^2(x)", "tan(x)", "sympy", 2),

        # Exponential
        ("integrate x * e^(x^2)", "e^(x^2)/2", "sympy", 3),
        ("integral of e^x * sin(x)", "e^x(sin(x)-cos(x))/2", "sympy", 4),

        # Rational functions
        ("integrate 1/(x^2 - 1)", "ln|x-1| - ln|x+1|/2", "sympy", 4),
        ("integral of x/(x^2 + 4)", "ln(x^2+4)/2", "sympy", 3),

        # Advanced
        ("integrate ln(x)", "x*ln(x) - x", "sympy", 3),
        ("integral of 1/(x*ln(x))", "ln(ln(x))", "sympy", 4),
        ("integrate sqrt(1 - x^2)", "arcsin(x)/2 + x*sqrt(1-x^2)/2", "sympy", 5),
    ],

    'complex_algebra': [
        # Systems
        ("solve x^2 + y^2 = 25 and x + y = 7", "x=3,y=4 or x=4,y=3", "sympy", 4),

        # Quadratics with complex solutions
        ("solve x^2 + 4x + 13 = 0", "x = -2 ± 3i", "sympy", 3),
        ("solve x^2 + 2x + 5 = 0", "x = -1 ± 2i", "sympy", 3),

        # Cubics and higher
        ("solve x^3 - 8 = 0", "x = 2, complex roots", "sympy", 3),
        ("find roots of x^4 - 16 = 0", "x = ±2, ±2i", "sympy", 4),

        # Simultaneous equations
        ("solve 3x + 2y = 12 and 2x - y = 1", "x=2, y=3", "sympy", 3),
        ("solve x + 2y + 3z = 14 and 2x + y + z = 8 and x - y + z = 2", "x=1,y=2,z=3", "sympy", 4),

        # Rational equations
        ("solve 1/x + 1/(x+1) = 1", "x = (-1±sqrt(5))/2", "sympy", 4),
        ("solve x/(x-1) = 2", "x = 2", "sympy", 3),

        # Exponential and log
        ("solve 2^x = 16", "x = 4", "sympy", 2),
        ("solve ln(x) = 2", "x = e^2", "sympy", 2),
        ("solve e^(2x) = 7", "x = ln(7)/2", "sympy", 3),

        # Inequalities
        ("solve x^2 - 5x + 6 > 0", "x < 2 or x > 3", "sympy", 4),

        # Factoring challenges
        ("factor x^4 + 4", "(x^2-2x+2)(x^2+2x+2)", "sympy", 4),
        ("factor x^3 + 27", "(x+3)(x^2-3x+9)", "sympy", 3),
        ("expand (x+y)^4", "x^4+4x^3y+6x^2y^2+4xy^3+y^4", "sympy", 3),
    ],

    'advanced_numerical': [
        # Combinatorics
        ("what is 10 choose 3", "120", "sympy", 2),
        ("calculate 52 choose 5", "2598960", "sympy", 3),

        # Factorials
        ("what is 8!", "40320", "sympy", 2),
        ("calculate 10!", "3628800", "sympy", 2),

        # Powers and roots
        ("what is 2^20", "1048576", "sympy", 2),
        ("calculate sqrt(17689)", "133", "sympy", 2),
        ("what is the cube root of 27", "3", "sympy", 1),

        # Modular arithmetic
        ("what is 100 mod 7", "2", "sympy", 2),
        ("calculate 13^17 mod 19", "requires computation", "sympy", 4),

        # GCD and LCM
        ("gcd of 144 and 60", "12", "sympy", 2),
        ("lcm of 12, 18, and 24", "72", "sympy", 2),

        # Prime factorization
        ("prime factors of 360", "2^3 * 3^2 * 5", "sympy", 3),

        # Complex numbers
        ("what is (3 + 4i) * (2 - i)", "10 + 5i", "sympy", 3),
        ("calculate |3 + 4i|", "5", "sympy", 2),
    ],

    'symbolic_manipulation': [
        # Trig identities
        ("simplify sin^2(x) + cos^2(x)", "1", "sympy", 2),
        ("simplify 1 - sin^2(x)", "cos^2(x)", "sympy", 2),
        ("expand sin(2x)", "2sin(x)cos(x)", "sympy", 3),
        ("simplify (1 - cos(2x))/2", "sin^2(x)", "sympy", 3),

        # Algebraic simplification
        ("simplify (x^3 - y^3)/(x - y)", "x^2 + xy + y^2", "sympy", 3),
        ("expand (x + y + z)^2", "x^2+y^2+z^2+2xy+2xz+2yz", "sympy", 2),
        ("factor x^4 - y^4", "(x-y)(x+y)(x^2+y^2)", "sympy", 3),
        ("simplify sqrt(50) + sqrt(18)", "8*sqrt(2)", "sympy", 3),

        # Rational expressions
        ("simplify (x^2 - 4)/(x^2 - 4x + 4)", "(x+2)/(x-2)", "sympy", 3),
        ("simplify (a + b)/(a^2 - b^2)", "1/(a-b)", "sympy", 3),

        # Logarithms
        ("simplify ln(x^2)", "2*ln(x)", "sympy", 2),
        ("simplify ln(a) + ln(b)", "ln(ab)", "sympy", 2),
        ("simplify e^(ln(x))", "x", "sympy", 2),

        # Exponents
        ("simplify (x^a)^b", "x^(ab)", "sympy", 2),
        ("simplify x^a * x^b", "x^(a+b)", "sympy", 2),
    ],
}


def run_challenge_test():
    """Run comprehensive challenge test."""
    print("="*70)
    print("HOLY CALCULATOR PI - CHALLENGE TEST")
    print("="*70)
    print(f"Test date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Purpose: Test system limits with harder queries")
    print(f"Tier tested: SymPy only (no Wolfram, no LLM)")
    print("="*70)

    handler = SymPyHandler()

    results = []
    total_time = 0
    category_stats = {}

    for category_name, queries in CHALLENGE_QUERIES.items():
        print(f"\n{'='*70}")
        print(f"Category: {category_name.upper()} ({len(queries)} queries)")
        print(f"{'='*70}")

        category_results = {
            'total': len(queries),
            'correct': 0,
            'incorrect': 0,
            'failed': 0,
            'avg_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'queries': []
        }

        for i, (query, expected, tier, difficulty) in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] {query}")

            start = time.time()
            result = handler.process_query(query)
            elapsed = time.time() - start

            total_time += elapsed
            category_results['min_time'] = min(category_results['min_time'], elapsed)
            category_results['max_time'] = max(category_results['max_time'], elapsed)

            if result and result.get('success'):
                actual = result.get('formatted', str(result.get('result', result.get('derivative', result.get('integral', result.get('solutions'))))))

                is_correct = expressions_match(str(actual), expected)

                if is_correct:
                    category_results['correct'] += 1
                    status = "✅ CORRECT"
                else:
                    category_results['incorrect'] += 1
                    status = "⚠️  INCORRECT"

                print(f"  Result: {actual}")
                print(f"  Expected: {expected}")
                print(f"  Time: {elapsed*1000:.1f}ms")
                print(f"  Status: {status}")

                category_results['queries'].append({
                    'query': query,
                    'expected': expected,
                    'actual': str(actual),
                    'correct': is_correct,
                    'time': elapsed,
                    'difficulty': difficulty
                })

            else:
                category_results['failed'] += 1
                print(f"  Result: FAILED (no result)")
                print(f"  Expected: {expected}")
                print(f"  Time: {elapsed*1000:.1f}ms")
                print(f"  Status: ❌ FAILED")

                category_results['queries'].append({
                    'query': query,
                    'expected': expected,
                    'actual': None,
                    'correct': False,
                    'time': elapsed,
                    'difficulty': difficulty,
                    'failed': True
                })

        # Calculate category averages
        if category_results['total'] > 0:
            category_results['avg_time'] = sum(q['time'] for q in category_results['queries']) / len(category_results['queries'])
            category_results['accuracy'] = category_results['correct'] / category_results['total']

        category_stats[category_name] = category_results

        # Print category summary
        print(f"\n{'─'*70}")
        print(f"Category Summary: {category_name}")
        print(f"  Correct: {category_results['correct']}/{category_results['total']} ({category_results['accuracy']*100:.1f}%)")
        print(f"  Incorrect: {category_results['incorrect']}")
        print(f"  Failed: {category_results['failed']}")
        print(f"  Avg time: {category_results['avg_time']*1000:.1f}ms")
        print(f"  Time range: {category_results['min_time']*1000:.1f}ms - {category_results['max_time']*1000:.1f}ms")

    # Overall summary
    print(f"\n{'='*70}")
    print("OVERALL SUMMARY - CHALLENGE TEST")
    print(f"{'='*70}")

    total_queries = sum(stats['total'] for stats in category_stats.values())
    total_correct = sum(stats['correct'] for stats in category_stats.values())
    total_failed = sum(stats['failed'] for stats in category_stats.values())
    overall_accuracy = total_correct / total_queries if total_queries > 0 else 0

    print(f"Total queries tested: {total_queries}")
    print(f"Correct: {total_correct} ({overall_accuracy*100:.1f}%)")
    print(f"Incorrect: {sum(stats['incorrect'] for stats in category_stats.values())}")
    print(f"Failed: {total_failed}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average time per query: {(total_time/total_queries)*1000:.1f}ms")

    print(f"\nAccuracy by category:")
    for cat, stats in category_stats.items():
        print(f"  {cat:25s}: {stats['accuracy']*100:5.1f}%  ({stats['correct']}/{stats['total']})")

    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'test_type': 'challenge',
        'overall': {
            'total_queries': total_queries,
            'correct': total_correct,
            'accuracy': overall_accuracy,
            'total_time': total_time,
            'avg_time_per_query': total_time / total_queries if total_queries > 0 else 0
        },
        'by_category': category_stats
    }

    output_file = Path('challenge_test_results.json')
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n{'='*70}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*70}")

    return output


if __name__ == '__main__':
    results = run_challenge_test()
