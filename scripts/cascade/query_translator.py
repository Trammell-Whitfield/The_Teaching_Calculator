#!/usr/bin/env python3
"""
Query Translation Layer for Holy Calculator
Converts natural language math queries to standardized symbolic formats.

This module addresses the critical issue where queries like "derivative of x^2"
were being parsed literally as "d*e*r*i*v*a*t*i*v*e*o*f*x^2" instead of being
recognized as calculus operations.
"""

import re
from typing import Dict, Any, Optional, Tuple, List


class QueryTranslator:
    """
    Translates natural language math queries to standardized formats.

    Provides both SymPy-compatible format and LLM-optimized prompts.
    """

    def __init__(self):
        """Initialize translation patterns for mathematical operations."""

        # Derivative patterns
        self.derivative_patterns = [
            (r"derivative of (.+)", "derivative"),
            (r"differentiate (.+)", "derivative"),
            (r"d/dx\s+(?:of\s+)?(.+)", "derivative"),
            (r"derive (.+)", "derivative"),
            (r"find\s+(?:the\s+)?derivative\s+of (.+)", "derivative"),
            (r"(?:what is|what's)\s+(?:the\s+)?derivative\s+of (.+)", "derivative"),
        ]

        # Second/higher derivative patterns
        self.higher_derivative_patterns = [
            (r"second derivative of (.+)", "second_derivative"),
            (r"2nd derivative of (.+)", "second_derivative"),
            (r"d2/dx2\s+(?:of\s+)?(.+)", "second_derivative"),
            (r"third derivative of (.+)", "third_derivative"),
        ]

        # Integral patterns
        self.integral_patterns = [
            (r"integral of (.+)", "integral"),
            (r"integrate (.+)", "integral"),
            (r"∫\s*(.+)(?:\s+dx)?", "integral"),
            (r"find\s+(?:the\s+)?integral\s+of (.+)", "integral"),
            (r"(?:what is|what's)\s+(?:the\s+)?integral\s+of (.+)", "integral"),
            (r"antiderivative of (.+)", "integral"),
        ]

        # Limit patterns
        self.limit_patterns = [
            (r"limit of (.+) as (.+) (?:approaches|->|→)\s*(.+)", "limit"),
            (r"lim\s+(.+)->(.+)\s+(?:of\s+)?(.+)", "limit"),
            (r"limit (.+) at (.+)\s*=\s*(.+)", "limit"),
        ]

        # Solve/equation patterns
        self.solve_patterns = [
            (r"solve\s+(?:for\s+\w+\s*:)?\s*(.+)", "solve"),
            (r"find\s+(?:\w+\s+)?(?:in|from|for)\s*(.+)", "solve"),
            (r"(?:what is|what's)\s+(.+)\s*\?", "solve"),
        ]

        # Simplify patterns
        self.simplify_patterns = [
            (r"simplify (.+)", "simplify"),
            (r"reduce (.+)", "simplify"),
            (r"simplification of (.+)", "simplify"),
        ]

        # Factor/expand patterns
        self.factor_patterns = [
            (r"factor (.+)", "factor"),
            (r"factorize (.+)", "factor"),
            (r"factorise (.+)", "factor"),
        ]

        self.expand_patterns = [
            (r"expand (.+)", "expand"),
            (r"expand out (.+)", "expand"),
            (r"multiplication of (.+)", "expand"),
        ]

    def translate(self, query: str) -> Dict[str, Any]:
        """
        Translate natural language query to standardized mathematical formats.

        Args:
            query: Natural language math query (e.g., "derivative of x^2")

        Returns:
            Dictionary with:
                - operation: Type of operation ('derivative', 'integral', etc.)
                - expression: Cleaned mathematical expression
                - variable: Variable of operation (default 'x')
                - original: Original query string
                - sympy_format: Ready for SymPy evaluation
                - llm_format: Optimized prompt for LLM
        """
        query = query.strip()
        query_lower = query.lower()

        # Try higher order derivatives first (more specific)
        for pattern, op in self.higher_derivative_patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                expr = match.group(1).strip()
                return self._format_higher_derivative(expr, op, query)

        # Try derivative
        for pattern, op in self.derivative_patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                expr = match.group(1).strip()
                return self._format_derivative(expr, query)

        # Try integral
        for pattern, op in self.integral_patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                expr = match.group(1).strip()
                return self._format_integral(expr, query)

        # Try limit
        for pattern, op in self.limit_patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                return self._format_limit(match, query)

        # Try factor
        for pattern, op in self.factor_patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                expr = match.group(1).strip()
                return self._format_factor(expr, query)

        # Try expand
        for pattern, op in self.expand_patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                expr = match.group(1).strip()
                return self._format_expand(expr, query)

        # Try simplify
        for pattern, op in self.simplify_patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                expr = match.group(1).strip()
                return self._format_simplify(expr, query)

        # Try solve
        for pattern, op in self.solve_patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                expr = match.group(1).strip()
                return self._format_solve(expr, query)

        # General mathematical expression
        return self._format_general(query)

    def _format_derivative(self, expr: str, original: str) -> Dict[str, Any]:
        """Format first derivative query."""
        expr = self._clean_expression(expr)
        var = self._extract_variable(expr)

        # Convert to SymPy-compatible syntax
        sympy_expr = self._to_sympy_syntax(expr)

        return {
            'operation': 'derivative',
            'expression': expr,
            'variable': var,
            'original': original,
            'sympy_format': f"diff({sympy_expr}, {var})",
            'llm_format': (
                f"Find the derivative of {expr} with respect to {var}. "
                f"Show your work step by step. "
                f"State the final answer clearly after 'The answer is:'"
            ),
        }

    def _format_higher_derivative(self, expr: str, op: str, original: str) -> Dict[str, Any]:
        """Format higher order derivative query."""
        expr = self._clean_expression(expr)
        var = self._extract_variable(expr)

        # Determine order
        order = 2 if op == 'second_derivative' else 3
        order_text = 'second' if order == 2 else 'third'

        sympy_expr = self._to_sympy_syntax(expr)

        return {
            'operation': op,
            'expression': expr,
            'variable': var,
            'order': order,
            'original': original,
            'sympy_format': f"diff({sympy_expr}, {var}, {order})",
            'llm_format': (
                f"Find the {order_text} derivative of {expr} with respect to {var}. "
                f"Show your work step by step. "
                f"State the final answer clearly after 'The answer is:'"
            ),
        }

    def _format_integral(self, expr: str, original: str) -> Dict[str, Any]:
        """Format integral query."""
        expr = self._clean_expression(expr)
        var = self._extract_variable(expr)

        sympy_expr = self._to_sympy_syntax(expr)

        return {
            'operation': 'integral',
            'expression': expr,
            'variable': var,
            'original': original,
            'sympy_format': f"integrate({sympy_expr}, {var})",
            'llm_format': (
                f"Find the indefinite integral of {expr} with respect to {var}. "
                f"Show your work step by step. "
                f"State the final answer clearly after 'The answer is:'"
            ),
        }

    def _format_limit(self, match: re.Match, original: str) -> Dict[str, Any]:
        """Format limit query."""
        groups = match.groups()

        if len(groups) == 3:
            expr, var, point = groups
            expr = self._clean_expression(expr.strip())
            var = var.strip()
            point = point.strip()

            sympy_expr = self._to_sympy_syntax(expr)

            return {
                'operation': 'limit',
                'expression': expr,
                'variable': var,
                'point': point,
                'original': original,
                'sympy_format': f"limit({sympy_expr}, {var}, {point})",
                'llm_format': (
                    f"Find the limit of {expr} as {var} approaches {point}. "
                    f"Show your work step by step. "
                    f"State the final answer clearly after 'The answer is:'"
                ),
            }

        return self._format_general(original)

    def _format_solve(self, expr: str, original: str) -> Dict[str, Any]:
        """Format solve equation query."""
        expr = self._clean_expression(expr)
        var = self._extract_variable(expr)

        sympy_expr = self._to_sympy_syntax(expr)

        return {
            'operation': 'solve',
            'expression': expr,
            'variable': var,
            'original': original,
            'sympy_format': f"solve({sympy_expr}, {var})",
            'llm_format': (
                f"Solve the equation: {expr}. "
                f"Find the value of {var}. "
                f"Show your work step by step. "
                f"State the final answer clearly after 'The answer is:'"
            ),
        }

    def _format_simplify(self, expr: str, original: str) -> Dict[str, Any]:
        """Format simplify query."""
        expr = self._clean_expression(expr)
        sympy_expr = self._to_sympy_syntax(expr)

        return {
            'operation': 'simplify',
            'expression': expr,
            'variable': self._extract_variable(expr),
            'original': original,
            'sympy_format': f"simplify({sympy_expr})",
            'llm_format': (
                f"Simplify the expression: {expr}. "
                f"Show your work step by step. "
                f"State the final answer clearly after 'The answer is:'"
            ),
        }

    def _format_factor(self, expr: str, original: str) -> Dict[str, Any]:
        """Format factor query."""
        expr = self._clean_expression(expr)
        sympy_expr = self._to_sympy_syntax(expr)

        return {
            'operation': 'factor',
            'expression': expr,
            'variable': self._extract_variable(expr),
            'original': original,
            'sympy_format': f"factor({sympy_expr})",
            'llm_format': (
                f"Factor the expression: {expr}. "
                f"Show your work step by step. "
                f"State the final answer clearly after 'The answer is:'"
            ),
        }

    def _format_expand(self, expr: str, original: str) -> Dict[str, Any]:
        """Format expand query."""
        expr = self._clean_expression(expr)
        sympy_expr = self._to_sympy_syntax(expr)

        return {
            'operation': 'expand',
            'expression': expr,
            'variable': self._extract_variable(expr),
            'original': original,
            'sympy_format': f"expand({sympy_expr})",
            'llm_format': (
                f"Expand the expression: {expr}. "
                f"Show your work step by step. "
                f"State the final answer clearly after 'The answer is:'"
            ),
        }

    def _format_general(self, query: str) -> Dict[str, Any]:
        """Format general mathematical query."""
        expr = self._clean_expression(query)
        sympy_expr = self._to_sympy_syntax(expr)

        return {
            'operation': 'general',
            'expression': expr,
            'variable': self._extract_variable(expr),
            'original': query,
            'sympy_format': sympy_expr,
            'llm_format': (
                f"Solve this problem: {query}. "
                f"Show your work step by step. "
                f"State the final answer clearly after 'The answer is:'"
            ),
        }

    def _clean_expression(self, expr: str) -> str:
        """
        Clean mathematical expression by removing common words.

        Keeps the mathematical symbols and variables intact.
        """
        # Remove leading/trailing whitespace
        expr = expr.strip()

        # Remove question marks
        expr = expr.rstrip('?')

        # Remove common filler words
        remove_words = [
            'the', 'of', 'with', 'respect', 'to', 'for', 'function',
            'equation', 'expression', 'please', 'find', 'what', 'is',
            'are', 'calculate', 'compute', 'determine'
        ]

        for word in remove_words:
            # Only remove if it's a whole word (word boundary)
            expr = re.sub(rf'\b{word}\b', '', expr, flags=re.IGNORECASE)

        # Clean up multiple spaces
        expr = ' '.join(expr.split())

        # Replace text representations with symbols
        replacements = {
            'squared': '**2',
            'cubed': '**3',
            ' times ': '*',
            ' plus ': '+',
            ' minus ': '-',
            ' divided by ': '/',
            ' over ': '/',
        }

        for text, symbol in replacements.items():
            expr = expr.replace(text, symbol)

        return expr.strip()

    def _to_sympy_syntax(self, expr: str) -> str:
        """
        Convert expression to SymPy-compatible syntax.

        Handles:
        - x^2 → x**2 (exponentiation)
        - 2x → 2*x (implicit multiplication)
        - sin, cos, tan, etc. (preserved as function calls)
        """
        # Replace ^ with **
        expr = expr.replace('^', '**')

        # Add implicit multiplication: 2x → 2*x, 3sin(x) → 3*sin(x)
        # Pattern: digit followed by letter
        expr = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expr)

        # Pattern: closing paren followed by letter/digit
        expr = re.sub(r'\)(\w)', r')*\1', expr)

        # Pattern: single letter/digit followed by opening paren → implicit multiplication
        # BUT preserve known function names (sin, cos, tan, log, etc.)
        known_functions = ['sin', 'cos', 'tan', 'sec', 'csc', 'cot',
                          'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh',
                          'log', 'ln', 'exp', 'sqrt', 'abs',
                          'diff', 'integrate', 'limit', 'solve', 'factor', 'expand', 'simplify']

        # Create a regex pattern that matches function names followed by '('
        func_pattern = r'\b(?:' + '|'.join(known_functions) + r')\('

        # Find all function calls to preserve them
        func_positions = set()
        for match in re.finditer(func_pattern, expr):
            func_positions.add(match.start())

        # Now add multiplication for single chars followed by ( that aren't function calls
        result = []
        i = 0
        while i < len(expr):
            # Check if this position is the start of a function call
            if i in func_positions:
                # Find the matching function and add it as-is
                for func in known_functions:
                    if expr[i:i+len(func)+1] == func + '(':
                        result.append(expr[i:i+len(func)+1])
                        i += len(func) + 1
                        break
            # Check for single char followed by (
            elif i < len(expr) - 1 and expr[i].isalnum() and expr[i+1] == '(':
                # Check if the char before is not alphanumeric (to ensure it's a single char)
                if i == 0 or not expr[i-1].isalnum():
                    result.append(expr[i] + '*(')
                    i += 2
                else:
                    result.append(expr[i])
                    i += 1
            else:
                result.append(expr[i])
                i += 1

        expr = ''.join(result)

        return expr

    def _extract_variable(self, expr: str) -> str:
        """
        Extract the primary variable from an expression.

        Returns the first single-letter variable found, defaults to 'x'.
        """
        # Look for single letter variables (excluding common function names)
        excluded = {'e', 'i', 'pi'}  # Mathematical constants

        variables = re.findall(r'\b([a-z])\b', expr, re.IGNORECASE)

        for var in variables:
            if var.lower() not in excluded:
                return var

        return 'x'  # Default variable


def main():
    """Test the query translator with sample queries."""
    translator = QueryTranslator()

    test_queries = [
        # Derivatives
        "derivative of x^2",
        "what is the derivative of sin(x)",
        "differentiate 3x^2 + 2x + 1",
        "second derivative of x^3",

        # Integrals
        "integrate cos(x)",
        "integral of x^2",
        "find the integral of e^x",

        # Limits
        "limit of (x^2 - 1)/(x - 1) as x approaches 1",
        "lim x->0 sin(x)/x",

        # Algebra
        "solve 2x + 5 = 13",
        "factor x^2 + 5x + 6",
        "expand (x + 1)(x + 2)",
        "simplify (x + 1)(x - 1)",

        # General
        "what is 2 + 2",
    ]

    print("="*70)
    print("QUERY TRANSLATOR TEST")
    print("="*70)

    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Original: {query}")
        result = translator.translate(query)
        print(f"   Operation: {result['operation']}")
        print(f"   Expression: {result['expression']}")
        print(f"   Variable: {result['variable']}")
        print(f"   SymPy format: {result['sympy_format']}")
        print(f"   LLM format: {result['llm_format'][:80]}...")

    print(f"\n{'='*70}")
    print(f"Tested {len(test_queries)} queries successfully!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
