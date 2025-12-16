"""
SymPy Handler - Layer 1 of the Holy Calculator Cascade
Handles fast, offline symbolic mathematics for 40-60% of queries.

Phase 5: SymPy Integration
Author: Holy Calculator Team
"""

import re
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor
)
from typing import Optional, Dict, Any, List


class SymPyHandler:
    """
    Handles symbolic mathematics using SymPy library.

    Capabilities:
    - Solving algebraic equations (linear, quadratic, systems)
    - Derivatives and integrals
    - Simplification and expansion
    - Trigonometric identities
    - Basic arithmetic
    """

    def __init__(self):
        """Initialize the SymPy handler with common symbols."""
        self.x = sp.Symbol('x')
        self.y = sp.Symbol('y')
        self.z = sp.Symbol('z')
        self.a = sp.Symbol('a')
        self.t = sp.Symbol('t')

        # Define parsing transformations for better natural language support
        self.transformations = (
            standard_transformations +
            (implicit_multiplication_application, convert_xor)
        )

    def can_handle(self, query: str) -> bool:
        """
        Determine if this handler can process the given query.

        Args:
            query: Natural language math query

        Returns:
            True if SymPy can likely handle this query, False otherwise
        """
        query_lower = query.lower()

        # Keywords that indicate SymPy can handle
        positive_indicators = [
            'solve', 'derivative', 'integrate', 'differentiate',
            'expand', 'factor', 'simplify', 'calculate',
            'd/dx', 'dy/dx', 'integral', 'find the derivative',
            'what is', 'compute', 'evaluate'
        ]

        # Keywords that indicate need for LLM
        negative_indicators = [
            'word problem', 'story', 'prove', 'explain why',
            'how does', 'what does it mean', 'interpret',
            'graph', 'plot', 'draw'
        ]

        # Check for negative indicators first
        for indicator in negative_indicators:
            if indicator in query_lower:
                return False

        # Check for positive indicators
        for indicator in positive_indicators:
            if indicator in query_lower:
                return True

        # If contains mathematical symbols, likely can handle
        math_symbols = ['x', '=', '+', '-', '*', '/', '^', 'sin', 'cos', 'tan']
        if any(symbol in query_lower for symbol in math_symbols):
            return True

        return False

    def _extract_equation(self, query: str) -> Optional[str]:
        """
        Extract equation from natural language query.

        Args:
            query: Natural language query

        Returns:
            Extracted equation string or None
        """
        # Look for equations after colons or "equation:" patterns
        if ':' in query:
            parts = query.split(':')
            equation = parts[-1].strip()
            if equation:
                return equation

        # Look for patterns like "solve 2x + 5 = 13"
        match = re.search(r'solve\s+(?:for\s+\w+\s*:?\s*)?(.+)', query, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Look for "f(x) = ..." patterns - extract only the right side
        match = re.search(r'f\([^)]+\)\s*=\s*(.+)', query, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # Return the whole query if it looks like an equation
        if '=' in query or any(op in query for op in ['+', '-', '*', '/', '^']):
            return query.strip()

        return None

    def _parse_expression(self, expr_str: str) -> Optional[sp.Expr]:
        """
        Parse a string into a SymPy expression.

        Args:
            expr_str: String representation of mathematical expression

        Returns:
            SymPy expression or None if parsing fails
        """
        try:
            # Replace common patterns
            expr_str = expr_str.replace('^', '**')  # x^2 -> x**2
            expr_str = expr_str.replace('÷', '/')

            # Parse the expression
            expr = parse_expr(expr_str, transformations=self.transformations)
            return expr
        except Exception as e:
            print(f"Error parsing expression '{expr_str}': {e}")
            return None

    def solve_equation(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Solve algebraic equations.

        Args:
            query: Natural language query containing an equation

        Returns:
            Dictionary with solution or None if solving fails
        """
        try:
            # Handle systems of equations (with 'and' keyword)
            if ' and ' in query.lower():
                return self._solve_system(query)

            # Extract equation from query
            equation_str = self._extract_equation(query)
            if not equation_str:
                return None

            # Handle equations with '='
            if '=' in equation_str:
                left, right = equation_str.split('=', 1)
                left_expr = self._parse_expression(left.strip())
                right_expr = self._parse_expression(right.strip())

                if left_expr is None or right_expr is None:
                    return None

                # Create equation
                equation = sp.Eq(left_expr, right_expr)

                # Determine which variable to solve for
                variables = list(equation.free_symbols)
                if not variables:
                    return None

                # Solve for the first variable found
                solutions = sp.solve(equation, variables[0])

                if not solutions:
                    return None

                return {
                    'success': True,
                    'solutions': solutions,
                    'variable': str(variables[0]),
                    'formatted': self._format_solutions(variables[0], solutions)
                }
            else:
                # Just an expression to evaluate
                expr = self._parse_expression(equation_str)
                if expr and expr.is_number:
                    return {
                        'success': True,
                        'result': float(expr),
                        'formatted': str(expr)
                    }
                return None

        except Exception as e:
            print(f"Error solving equation: {e}")
            return None

    def _format_solutions(self, variable: sp.Symbol, solutions: List) -> str:
        """Format solutions into readable string."""
        if len(solutions) == 1:
            return f"{variable} = {solutions[0]}"
        else:
            return ", ".join([f"{variable} = {sol}" for sol in solutions])

    def _solve_system(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Solve systems of equations.

        Args:
            query: Query containing multiple equations separated by 'and'

        Returns:
            Dictionary with solutions or None
        """
        try:
            # Split by 'and' to get individual equations
            parts = query.lower().split(' and ')

            # Extract equations
            equations = []
            for part in parts:
                # Remove 'solve:' prefix if present
                part = re.sub(r'^solve:?\s*', '', part.strip(), flags=re.IGNORECASE)

                if '=' in part:
                    left, right = part.split('=', 1)
                    left_expr = self._parse_expression(left.strip())
                    right_expr = self._parse_expression(right.strip())

                    if left_expr and right_expr:
                        equations.append(sp.Eq(left_expr, right_expr))

            if not equations:
                return None

            # Get all variables
            all_vars = set()
            for eq in equations:
                all_vars.update(eq.free_symbols)

            # Solve system
            solutions = sp.solve(equations, list(all_vars))

            if not solutions:
                return None

            # Format solutions
            if isinstance(solutions, dict):
                formatted = ", ".join([f"{var} = {val}" for var, val in solutions.items()])
            else:
                formatted = str(solutions)

            return {
                'success': True,
                'solutions': solutions,
                'formatted': formatted
            }

        except Exception as e:
            print(f"Error solving system: {e}")
            return None

    def compute_derivative(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Compute derivatives.

        Args:
            query: Natural language query about derivative

        Returns:
            Dictionary with derivative or None if computation fails
        """
        try:
            # Extract expression
            equation_str = self._extract_equation(query)
            if not equation_str:
                # Try to extract after "of:"
                match = re.search(r'of:?\s*(.+)', query, re.IGNORECASE)
                if match:
                    equation_str = match.group(1).strip()

            if not equation_str:
                return None

            # Parse expression
            expr = self._parse_expression(equation_str)
            if expr is None:
                return None

            # Determine variable (default to x)
            variables = list(expr.free_symbols)
            if not variables:
                return None

            var = variables[0]  # Use first variable found

            # Compute derivative
            derivative = sp.diff(expr, var)

            # Format derivative in cleaner format (replace ** with ^)
            formatted_derivative = str(derivative).replace('**', '^').replace('*', '')

            return {
                'success': True,
                'derivative': derivative,
                'variable': str(var),
                'formatted': formatted_derivative
            }

        except Exception as e:
            print(f"Error computing derivative: {e}")
            return None

    def compute_integral(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Compute integrals.

        Args:
            query: Natural language query about integral

        Returns:
            Dictionary with integral or None if computation fails
        """
        try:
            # Extract expression (remove 'dx', 'dy', etc.)
            equation_str = self._extract_equation(query)
            if not equation_str:
                match = re.search(r'of:?\s*(.+)', query, re.IGNORECASE)
                if match:
                    equation_str = match.group(1).strip()

            if not equation_str:
                return None

            # Remove differential notation (dx, dy, etc.)
            equation_str = re.sub(r'd[a-z]$', '', equation_str).strip()

            # Parse expression
            expr = self._parse_expression(equation_str)
            if expr is None:
                return None

            # Determine variable
            variables = list(expr.free_symbols)
            if not variables:
                return None

            var = variables[0]

            # Compute integral
            integral = sp.integrate(expr, var)

            return {
                'success': True,
                'integral': integral,
                'variable': str(var),
                'formatted': f"∫ {expr} d{var} = {integral} + C"
            }

        except Exception as e:
            print(f"Error computing integral: {e}")
            return None

    def simplify_expression(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Simplify or expand expressions.

        Args:
            query: Natural language query

        Returns:
            Dictionary with simplified/expanded result or None
        """
        try:
            # Determine operation type
            is_expand = 'expand' in query.lower()
            is_factor = 'factor' in query.lower()
            is_simplify = 'simplify' in query.lower()

            # Extract expression
            equation_str = self._extract_equation(query)
            if not equation_str:
                return None

            # Parse expression
            expr = self._parse_expression(equation_str)
            if expr is None:
                return None

            # Apply appropriate operation
            if is_expand:
                result = sp.expand(expr)
                operation = 'expansion'
            elif is_factor:
                result = sp.factor(expr)
                operation = 'factorization'
            else:
                result = sp.simplify(expr)
                operation = 'simplification'

            return {
                'success': True,
                'result': result,
                'operation': operation,
                'formatted': str(result)
            }

        except Exception as e:
            print(f"Error simplifying expression: {e}")
            return None

    def evaluate_expression(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Evaluate mathematical expressions (e.g., sin(0), cos(pi), etc.).

        Args:
            query: Natural language query

        Returns:
            Dictionary with result or None
        """
        try:
            # Extract expression from "What is X?" pattern
            match = re.search(r'what is\s+(.+)', query, re.IGNORECASE)
            if match:
                expr_str = match.group(1).strip()
                # Remove trailing question mark
                expr_str = expr_str.rstrip('?').strip()
            else:
                expr_str = self._extract_equation(query)

            if not expr_str:
                return None

            # Parse and evaluate
            expr = self._parse_expression(expr_str)
            if expr is None:
                return None

            # Evaluate the expression
            result = expr.evalf()

            # Try to simplify to integer if possible
            if result.is_number:
                try:
                    int_result = int(result)
                    if abs(result - int_result) < 0.0001:
                        result = int_result
                except:
                    pass

            return {
                'success': True,
                'result': result,
                'formatted': str(result)
            }

        except Exception as e:
            print(f"Error evaluating expression: {e}")
            return None

    def process_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Main entry point - processes a query and routes to appropriate method.

        Args:
            query: Natural language math query

        Returns:
            Dictionary with result or None if processing fails
        """
        if not self.can_handle(query):
            return None

        query_lower = query.lower()

        # Route to appropriate handler
        if 'derivative' in query_lower or 'differentiate' in query_lower or 'd/dx' in query_lower:
            return self.compute_derivative(query)
        elif 'integrate' in query_lower or 'integral' in query_lower:
            return self.compute_integral(query)
        elif 'expand' in query_lower or 'factor' in query_lower or 'simplify' in query_lower:
            return self.simplify_expression(query)
        elif 'solve' in query_lower or ('=' in query and 'and' not in query_lower):
            return self.solve_equation(query)
        elif ' and ' in query_lower and '=' in query:
            return self.solve_equation(query)  # System of equations
        elif 'what is' in query_lower:
            return self.evaluate_expression(query)
        elif 'calculate' in query_lower or 'compute' in query_lower:
            return self.solve_equation(query)
        else:
            # Try to handle as equation by default
            return self.solve_equation(query)


# Test harness
if __name__ == "__main__":
    handler = SymPyHandler()

    # Test cases
    test_queries = [
        "Solve for x: 2x + 5 = 13",
        "Find the derivative of f(x) = x^3 + 2x^2 - 5x + 1",
        "Integrate: x^2 dx",
        "Expand: (x + 2)(x - 3)",
        "Calculate: 123 + 456",
    ]

    print("SymPy Handler Test Run:")
    print("=" * 60)

    for query in test_queries:
        print(f"\nQuery: {query}")
        result = handler.process_query(query)
        if result:
            print(f"✓ Result: {result.get('formatted', result)}")
        else:
            print("✗ Failed to process")
