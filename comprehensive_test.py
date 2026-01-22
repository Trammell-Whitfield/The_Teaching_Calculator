#!/usr/bin/env python3
"""
Comprehensive test of Holy Calculator with realistic queries
Tests SymPy, Wolfram (simulated), and LLM tiers
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
    """
    Normalize a mathematical expression for comparison.

    Removes formatting differences while preserving mathematical meaning.
    """
    if not expr:
        return ""

    # Convert to string and lowercase
    normalized = str(expr).lower()

    # Remove all whitespace
    normalized = normalized.replace(' ', '')

    # Normalize exponentiation FIRST (before touching *)
    # Convert both ** and ^ to **  for SymPy compatibility
    normalized = normalized.replace('^', '**')

    # Normalize common symbols
    normalized = normalized.replace('±', '+-')
    normalized = normalized.replace('√', 'sqrt')

    # Remove "The answer is:" if present
    if 'answeris' in normalized:
        parts = normalized.split('answeris')
        normalized = parts[-1] if parts else normalized

    # Remove trailing C (constant of integration)
    normalized = normalized.rstrip('+c').rstrip('c')

    return normalized.strip()


def expressions_match(actual: str, expected: str, tolerance: float = 0.01) -> bool:
    """
    Check if two mathematical expressions match.

    Args:
        actual: Actual answer from system
        expected: Expected answer
        tolerance: Tolerance for fuzzy matching

    Returns:
        True if expressions match (exact or fuzzy)
    """
    if not actual or not expected:
        return False

    # Normalize both expressions
    norm_actual = normalize_math_expression(actual)
    norm_expected = normalize_math_expression(expected)

    # Exact match after normalization
    if norm_actual == norm_expected:
        return True

    # Check if expected is contained in actual (for formatted answers)
    if norm_expected in norm_actual:
        return True

    # Check if actual contains expected (for concise answers)
    if norm_actual in norm_expected:
        return True

    # Special cases for common variations
    # x = 4 vs 4
    if '=' in norm_expected or '=' in norm_actual:
        # Extract just the value after =
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

    # Check for equivalent forms of ± notation
    # x = ±4 vs x = -4, x = 4 vs x = 4 or x = -4
    if '+-' in norm_expected or 'or' in norm_expected:
        # This is a ± answer, check if actual contains one of the values
        if norm_actual in norm_expected:
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

# Test dataset matching the 130-query structure from audit
TEST_QUERIES = {
    'derivatives': [
        ("derivative of x^3", "3*x**2", "sympy", 2),
        ("d/dx(sin(x))", "cos(x)", "sympy", 2),
        ("differentiate x^2 + 3x + 5", "2*x + 3", "sympy", 2),
        ("what is the derivative of e^x?", "e**x", "sympy", 2),
        ("find d/dx of cos(2x)", "-2*sin(2*x)", "sympy", 3),
        ("derivative of x*sin(x)", "x*cos(x) + sin(x)", "sympy", 3),
        ("d/dx(ln(x))", "1/x", "sympy", 2),
        ("differentiate x^4 - 2x^2 + 1", "4*x**3 - 4*x", "sympy", 2),
        ("what is d/dx of tan(x)?", "sec(x)**2", "sympy", 3),
        ("derivative of x^n", "n*x**(n-1)", "sympy", 2),
        ("d/dx(sqrt(x))", "1/(2*sqrt(x))", "sympy", 2),
        ("derivative of 1/x", "-1/x**2", "sympy", 2),
        ("differentiate cos(x)*sin(x)", "cos(x)**2 - sin(x)**2", "sympy", 3),
        ("d/dx(x^2*e^x)", "x**2*e**x + 2*x*e**x", "sympy", 3),
        ("derivative of ln(x^2)", "2/x", "sympy", 3),
    ],
    'integrals': [
        ("integrate x^2", "x**3/3 + C", "sympy", 2),
        ("integral of sin(x)", "-cos(x) + C", "sympy", 2),
        ("find the integral of 1/x", "ln(x) + C", "sympy", 2),
        ("integrate 2x + 3", "x**2 + 3*x + C", "sympy", 2),
        ("integral of e^x", "e**x + C", "sympy", 2),
        ("integrate cos(x)", "sin(x) + C", "sympy", 2),
        ("find integral of x^3", "x**4/4 + C", "sympy", 2),
        ("integrate 1/(x^2)", "-1/x + C", "sympy", 2),
        ("integral of sqrt(x)", "(2/3)*x**(3/2) + C", "sympy", 3),
        ("integrate x*e^x", "x*e**x - e**x + C", "sympy", 3),
        ("integral from 0 to 1 of x^2", "1/3", "sympy", 3),
        ("definite integral of sin(x) from 0 to pi", "2", "sympy", 3),
        ("integrate 1/(1+x^2)", "arctan(x) + C", "sympy", 3),
        ("find integral of ln(x)", "x*ln(x) - x + C", "sympy", 4),
        ("integrate e^(-x^2)", "no elementary form", "wolfram", 4),
    ],
    'algebra': [
        ("solve 2x + 5 = 13", "x = 4", "sympy", 1),
        ("solve x^2 = 16", "x = ±4", "sympy", 2),
        ("solve x^2 + 5x + 6 = 0", "x = -2 or x = -3", "sympy", 2),
        ("find x: 3x - 7 = 11", "x = 6", "sympy", 1),
        ("solve 2x + 3 = x + 7", "x = 4", "sympy", 2),
        ("solve x^2 - 4x + 4 = 0", "x = 2", "sympy", 2),
        ("find roots of x^3 - 1 = 0", "x = 1, complex roots", "sympy", 3),
        ("solve system: x + y = 5 and x - y = 1", "x = 3, y = 2", "sympy", 3),
        ("factor x^2 - 9", "(x-3)(x+3)", "sympy", 2),
        ("expand (x+2)(x-3)", "x^2 - x - 6", "sympy", 2),
        ("simplify (x^2 - 1)/(x - 1)", "x + 1", "sympy", 2),
        ("solve |x - 3| = 5", "x = 8 or x = -2", "sympy", 3),
        ("find x: x/2 + x/3 = 5", "x = 6", "sympy", 2),
        ("solve 2^x = 8", "x = 3", "sympy", 2),
        ("simplify sqrt(50)", "5*sqrt(2)", "sympy", 2),
        ("factor x^3 + 8", "(x+2)(x^2-2x+4)", "sympy", 3),
        ("solve x^2 + 1 = 0", "x = ±i", "sympy", 3),
        ("expand (x+1)^3", "x^3 + 3x^2 + 3x + 1", "sympy", 2),
        ("simplify (x^2 - 4)/(x + 2)", "x - 2", "sympy", 2),
        ("solve sqrt(x) = 4", "x = 16", "sympy", 2),
    ],
    'numerical': [
        ("what is 2 + 2", "4", "sympy", 1),
        ("calculate 15 * 23", "345", "sympy", 1),
        ("what is 100 / 4", "25", "sympy", 1),
        ("calculate 2^10", "1024", "sympy", 1),
        ("what is sqrt(144)", "12", "sympy", 1),
        ("calculate 5!", "120", "sympy", 1),
        ("what is 7 mod 3", "1", "sympy", 1),
        ("calculate gcd(48, 18)", "6", "sympy", 2),
        ("what is lcm(12, 18)", "36", "sympy", 2),
        ("is 17 prime?", "yes", "wolfram", 2),
        ("what is the 10th fibonacci number", "55", "wolfram", 2),
        ("calculate sin(30 degrees)", "0.5", "wolfram", 2),
        ("what is cos(0)", "1", "sympy", 1),
        ("calculate tan(45 degrees)", "1", "wolfram", 2),
        ("what is log(1000)", "3", "wolfram", 2),
    ],
    'symbolic': [
        ("simplify sin^2(x) + cos^2(x)", "1", "sympy", 2),
        ("expand sin(a+b)", "sin(a)cos(b) + cos(a)sin(b)", "sympy", 3),
        ("simplify (a+b)^2 - (a-b)^2", "4ab", "sympy", 2),
        ("factor a^3 - b^3", "(a-b)(a^2+ab+b^2)", "sympy", 3),
        ("expand (a+b+c)^2", "a^2+b^2+c^2+2ab+2ac+2bc", "sympy", 3),
        ("simplify (a^2 - b^2)/(a - b)", "a + b", "sympy", 2),
        ("solve for x: ax + b = 0", "x = -b/a", "sympy", 2),
        ("expand (1+x)^n using binomial theorem", "binomial expansion", "llm", 4),
        ("simplify sqrt(a^2)", "|a|", "sympy", 3),
        ("factor x^n - 1", "difference of nth powers", "sympy", 3),
        ("simplify e^(ln(x))", "x", "sympy", 2),
    ],
    'conversion': [
        ("convert 100 fahrenheit to celsius", "37.78 C", "wolfram", 2),
        ("convert 5 miles to kilometers", "8.05 km", "wolfram", 2),
    ],
    'constants': [
        ("what is pi", "3.14159...", "wolfram", 1),
        ("what is e (euler's number)", "2.71828...", "wolfram", 1),
    ],
    'explanations': [
        ("explain what a derivative is", "rate of change explanation", "llm", 3),
        ("what is the fundamental theorem of calculus", "FTC explanation", "llm", 4),
        ("why is e^(i*pi) = -1", "Euler's identity explanation", "llm", 4),
        ("explain the pythagorean theorem", "a^2 + b^2 = c^2 for right triangles", "llm", 2),
        ("what is a limit in calculus", "limit explanation", "llm", 3),
        ("explain integration by parts", "integration technique explanation", "llm", 3),
        ("what is the chain rule", "derivative composition rule", "llm", 3),
        ("explain what a logarithm is", "inverse of exponential", "llm", 2),
        ("what does it mean to factor", "factoring explanation", "llm", 2),
        ("explain the quadratic formula", "x = (-b ± sqrt(b^2-4ac))/(2a)", "llm", 3),
        ("what is a matrix", "2D array of numbers", "llm", 2),
        ("explain what sine and cosine represent", "trig functions explanation", "llm", 3),
        ("what is the difference between permutation and combination", "ordering explanation", "llm", 3),
        ("explain what imaginary numbers are", "sqrt(-1) = i explanation", "llm", 3),
        ("what is calculus used for", "calculus applications", "llm", 2),
        ("explain the concept of infinity", "infinity explanation", "llm", 4),
        ("what is a function", "mapping explanation", "llm", 2),
        ("explain what convergence means", "series convergence explanation", "llm", 4),
        ("what is the mean value theorem", "MVT explanation", "llm", 4),
        ("explain what a vector is", "magnitude and direction", "llm", 2),
    ],
    'proofs': [
        ("prove that sqrt(2) is irrational", "proof by contradiction", "llm", 4),
        ("prove sum of first n integers is n(n+1)/2", "induction proof", "llm", 4),
        ("prove pythagorean theorem", "geometric proof", "llm", 4),
        ("prove there are infinitely many primes", "Euclid's proof", "llm", 4),
        ("prove derivative of sin(x) is cos(x)", "limit definition proof", "llm", 4),
        ("prove e^(i*theta) = cos(theta) + i*sin(theta)", "Euler's formula proof", "llm", 5),
        ("prove fundamental theorem of calculus", "FTC proof", "llm", 5),
        ("prove 0.999... = 1", "repeating decimal proof", "llm", 3),
        ("prove sum of angles in a triangle is 180", "geometric proof", "llm", 3),
        ("prove quadratic formula", "completing the square", "llm", 4),
    ],
    'word_problems': [
        ("If a train travels 60 mph for 2 hours, how far does it go?", "120 miles", "llm", 2),
        ("Alice has 10 apples, gives 3 to Bob. How many left?", "7", "llm", 1),
        ("A rectangle has length 8 and width 5. What's the area?", "40", "llm", 1),
        ("If I buy 3 items at $4 each, what's the total?", "$12", "llm", 1),
        ("A car depreciates 15% per year. After 3 years, what % of value remains?", "~61.4%", "llm", 3),
        ("Find the dimensions of a rectangle with perimeter 40 and max area", "10x10 square", "llm", 4),
        ("Two trains 200 miles apart travel toward each other at 50 and 60 mph. When do they meet?", "~1.82 hours", "llm", 3),
        ("If f(x) = x^2 and g(x) = x+1, what is f(g(3))?", "16", "llm", 2),
        ("A ball is thrown upward at 20 m/s. When does it reach max height?", "2.04 seconds", "llm", 3),
        ("What's the probability of rolling two dice and getting a sum of 7?", "1/6", "llm", 2),
    ],
    'out_of_domain': [
        ("who is the president", "out of scope", "decline", 1),
        ("what is the weather today", "out of scope", "decline", 1),
        ("tell me a joke", "out of scope", "decline", 1),
        ("what is love", "out of scope", "decline", 1),
        ("how do I cook pasta", "out of scope", "decline", 1),
        ("what is the meaning of life", "out of scope", "decline", 1),
        ("who won the super bowl", "out of scope", "decline", 1),
        ("translate this to spanish", "out of scope", "decline", 1),
        ("what is the capital of France", "out of scope", "decline", 1),
        ("recommend a good book", "out of scope", "decline", 1),
    ],
}

def run_sympy_evaluation():
    """
    Run comprehensive evaluation on SymPy tier only.
    Full LLM evaluation would require model loading.
    """
    print("="*70)
    print("HOLY CALCULATOR - COMPREHENSIVE EVALUATION")
    print("="*70)
    print(f"Test date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing: SymPy handler (derivatives, integrals, algebra, numerical)")
    print("="*70)

    handler = SymPyHandler()

    results = []
    total_time = 0
    category_stats = {}

    # Test categories that SymPy should handle
    testable_categories = ['derivatives', 'integrals', 'algebra', 'numerical', 'symbolic']

    for category_name, queries in TEST_QUERIES.items():
        if category_name not in testable_categories:
            continue

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

                # Check correctness using normalized comparison
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
    print("OVERALL SUMMARY")
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
        print(f"  {cat:15s}: {stats['accuracy']*100:5.1f}%  ({stats['correct']}/{stats['total']})")

    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'overall': {
            'total_queries': total_queries,
            'correct': total_correct,
            'accuracy': overall_accuracy,
            'total_time': total_time,
            'avg_time_per_query': total_time / total_queries if total_queries > 0 else 0
        },
        'by_category': category_stats
    }

    output_file = Path('comprehensive_test_results.json')
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n{'='*70}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*70}")

    return output

if __name__ == '__main__':
    results = run_sympy_evaluation()
