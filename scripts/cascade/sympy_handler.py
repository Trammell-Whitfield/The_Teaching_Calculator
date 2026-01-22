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
            'what is', 'compute', 'evaluate',
            # Bug B fix: Add combinatorics and number theory keywords
            'gcd', 'lcm', 'mod', 'choose', 'factorial'
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
            import re

            # Replace common patterns
            expr_str = expr_str.replace('^', '**')  # x^2 -> x**2
            expr_str = expr_str.replace('÷', '/')

            # FIX: Convert ln to log (SymPy uses log for natural log)
            expr_str = expr_str.replace('ln(', 'log(')

            # FIX: Handle 'e' as Euler's number (prevent it being treated as variable)
            # Replace standalone 'e' with 'E' (SymPy's constant)
            expr_str = re.sub(r'\be\b', 'E', expr_str)

            # FIX BUG A: Convert inverse trig functions (arcsin → asin, etc.)
            expr_str = expr_str.replace('arcsin', 'asin')
            expr_str = expr_str.replace('arccos', 'acos')
            expr_str = expr_str.replace('arctan', 'atan')
            expr_str = expr_str.replace('arcsec', 'asec')
            expr_str = expr_str.replace('arccsc', 'acsc')
            expr_str = expr_str.replace('arccot', 'acot')

            # FIX BUG F: Convert trig power notation sin^2(x) → (sin(x))**2
            expr_str = re.sub(r'(sin|cos|tan|sec|csc|cot)\*\*(\d+)\(([^)]+)\)',
                             r'(\1(\3))**\2', expr_str)

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

    def _normalize_output(self, output: str) -> str:
        """
        Normalize output notation to match expected mathematical conventions.

        - Convert log() to ln() (Bug C)
        - Convert I to i for imaginary unit (Bug D)
        - Convert exp() to e^ for clarity
        - Convert ** to ^ for readability
        - Add strategic multiplication signs
        """
        import re

        # Bug C: Convert log to ln (natural logarithm)
        output = output.replace('log(', 'ln(')

        # Bug D: Convert imaginary unit I to i
        output = output.replace('*I', 'i')
        output = output.replace(' I', ' i')
        output = output.replace('I,', 'i,')
        output = output.replace('I)', 'i)')
        if output.endswith(' I'):
            output = output[:-2] + ' i'

        # Convert exp(...) to e^(...)
        # Handle nested exp calls carefully
        output = re.sub(r'exp\(([^()]+)\)', r'e^(\1)', output)
        # Handle more complex nested expressions
        max_iterations = 5
        for _ in range(max_iterations):
            old_output = output
            output = re.sub(r'exp\(([^()]*\([^()]*\)[^()]*)\)', r'e^(\1)', output)
            if output == old_output:
                break

        # Convert ** to ^ for readability
        output = output.replace('**', '^')

        # Add strategic multiplication signs:
        # Before opening parens: 3(x+1) → 3*(x+1)
        output = re.sub(r'(\d)(\()', r'\1*\2', output)
        # Between closing and opening parens: (x+1)(x-1) → (x+1)*(x-1)
        output = re.sub(r'(\))(\()', r'\1*\2', output)

        return output

    def _format_solutions(self, variable: sp.Symbol, solutions: List) -> str:
        """Format solutions into readable string."""
        if len(solutions) == 1:
            formatted = f"{variable} = {solutions[0]}"
        else:
            formatted = ", ".join([f"{variable} = {sol}" for sol in solutions])

        # Apply output normalization
        return self._normalize_output(formatted)

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
            # STEP 1: Extract the mathematical expression from natural language
            equation_str = None

            # Handle d/dx(expression) notation
            # Match everything between first ( and last )
            match = re.search(r'd/d([xyz])\s*\((.+)\)', query, re.IGNORECASE)
            if match:
                # Extract content between parentheses
                full_match = match.group(0)  # e.g., "d/dx(sin(x))"
                # Find the opening paren after d/dx
                start = full_match.index('(')
                # Get everything from that paren to end, then strip last char
                equation_str = full_match[start+1:-1].strip()

            # Handle "find d/dx of expression" pattern (MUST come before generic d/dx pattern)
            if not equation_str:
                match = re.search(r'find\s+d/d[xyz]\s+of\s+(.+)', query, re.IGNORECASE)
                if match:
                    equation_str = match.group(1).strip()

            # Handle "derivative of expression" pattern
            if not equation_str:
                match = re.search(r'derivative\s+of\s+(.+?)(?:\s+with\s+respect\s+to|\?|$)', query, re.IGNORECASE)
                if match:
                    equation_str = match.group(1).strip()

            # Handle "differentiate expression" pattern
            if not equation_str:
                match = re.search(r'differentiate\s+(.+?)(?:\s+with\s+respect\s+to|\?|$)', query, re.IGNORECASE)
                if match:
                    equation_str = match.group(1).strip()

            # Handle "what is the derivative of expression" pattern
            if not equation_str:
                match = re.search(r'what\s+is\s+(?:the\s+)?derivative\s+of\s+(.+?)(?:\?|$)', query, re.IGNORECASE)
                if match:
                    equation_str = match.group(1).strip()

            # Handle "what is d/dx of expression" pattern (MUST come before generic d/dx)
            if not equation_str:
                match = re.search(r'what\s+is\s+d/d[xyz]\s+of\s+(.+?)(?:\?|$)', query, re.IGNORECASE)
                if match:
                    equation_str = match.group(1).strip()

            # Generic d/dx pattern (fallback, comes LAST to avoid false matches)
            if not equation_str:
                match = re.search(r'd/d([xyz])\s+(.+)', query, re.IGNORECASE)
                if match:
                    equation_str = match.group(2).strip()

            # Fallback: try extract_equation
            if not equation_str:
                equation_str = self._extract_equation(query)

            if not equation_str:
                return None

            # STEP 2: Clean up the expression string
            # Remove trailing question marks and whitespace
            equation_str = equation_str.rstrip('?').strip()

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

            # Convert to string and apply comprehensive normalization
            formatted_derivative = str(derivative)
            formatted_derivative = self._normalize_output(formatted_derivative)

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
            # STEP 1: Extract the mathematical expression from natural language
            equation_str = None

            # Handle "integral of expression" pattern
            match = re.search(r'integral\s+of\s+(.+?)(?:\s+d[xyz]|\s+from|\?|$)', query, re.IGNORECASE)
            if match:
                equation_str = match.group(1).strip()

            # Handle "integrate expression" pattern
            if not equation_str:
                match = re.search(r'integrate\s+(.+?)(?:\s+d[xyz]|\s+from|\?|$)', query, re.IGNORECASE)
                if match:
                    equation_str = match.group(1).strip()

            # Handle "find integral of expression" pattern
            if not equation_str:
                match = re.search(r'find\s+(?:the\s+)?integral\s+of\s+(.+?)(?:\s+d[xyz]|\s+from|\?|$)', query, re.IGNORECASE)
                if match:
                    equation_str = match.group(1).strip()

            # Handle "find the integral of expression" pattern
            if not equation_str:
                match = re.search(r'find\s+integral\s+of\s+(.+?)(?:\s+d[xyz]|\?|$)', query, re.IGNORECASE)
                if match:
                    equation_str = match.group(1).strip()

            # Handle definite integral patterns (for later enhancement)
            if not equation_str:
                match = re.search(r'integral\s+from\s+.+?\s+to\s+.+?\s+of\s+(.+)', query, re.IGNORECASE)
                if match:
                    equation_str = match.group(1).strip()

            # Fallback: try extract_equation
            if not equation_str:
                equation_str = self._extract_equation(query)

            if not equation_str:
                return None

            # STEP 2: Clean up the expression string
            # Remove trailing question marks and whitespace
            equation_str = equation_str.rstrip('?').strip()

            # Remove differential notation at end (dx, dy, dz)
            equation_str = re.sub(r'\s*d[xyz]\s*$', '', equation_str).strip()

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

            # Convert to string and apply comprehensive normalization
            formatted_integral = str(integral)
            formatted_integral = self._normalize_output(formatted_integral)

            return {
                'success': True,
                'integral': integral,
                'variable': str(var),
                'formatted': f"{formatted_integral} + C"
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

            # Apply appropriate operation with aggressive simplification
            if is_expand:
                result = sp.expand(expr)
                operation = 'expansion'
            elif is_factor:
                result = sp.factor(expr)
                operation = 'factorization'
            else:
                # Use aggressive simplification for better results
                result = sp.simplify(expr, force=True)
                operation = 'simplification'

            # Convert to string and apply comprehensive normalization
            formatted = str(result)
            formatted = self._normalize_output(formatted)

            return {
                'success': True,
                'result': result,
                'operation': operation,
                'formatted': formatted
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

            # Normalize output
            formatted = self._normalize_output(str(result))

            return {
                'success': True,
                'result': result,
                'formatted': formatted
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

        # FIX BUG B: Preprocess natural language math operators
        query = self._preprocess_natural_language_operators(query)

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
        elif 'what is' in query_lower or 'calculate' in query_lower or 'compute' in query_lower:
            return self.evaluate_expression(query)
        else:
            # Try to handle as equation by default
            return self.solve_equation(query)

    def _preprocess_natural_language_operators(self, query: str) -> str:
        """
        FIX BUG B: Convert natural language math operators to SymPy functions.

        Handles: choose, mod, gcd, lcm, factorial, etc.
        """
        import re

        # Binomial coefficients: "n choose k"
        match = re.search(r'(\d+)\s+choose\s+(\d+)', query, re.IGNORECASE)
        if match:
            n, k = match.groups()
            query = re.sub(r'\d+\s+choose\s+\d+', f'binomial({n}, {k})', query, flags=re.IGNORECASE)

        # GCD: "gcd of a and b"
        match = re.search(r'gcd\s+of\s+(\d+)\s+and\s+(\d+)', query, re.IGNORECASE)
        if match:
            a, b = match.groups()
            # Replace the whole query with just the function call for evaluation
            return f'what is gcd({a}, {b})'

        # LCM: "lcm of a, b, and c"
        match = re.search(r'lcm\s+of\s+([\d,\s]+)', query, re.IGNORECASE)
        if match:
            numbers = re.findall(r'\d+', match.group(1))
            return f'what is lcm({", ".join(numbers)})'

        # Modular arithmetic: "a mod b"
        match = re.search(r'(\d+)\s+mod\s+(\d+)', query, re.IGNORECASE)
        if match:
            a, b = match.groups()
            query = re.sub(r'\d+\s+mod\s+\d+', f'Mod({a}, {b})', query, flags=re.IGNORECASE)

        # Prime factors: "prime factors of n"
        match = re.search(r'prime\s+factors?\s+of\s+(\d+)', query, re.IGNORECASE)
        if match:
            n = match.group(1)
            query = re.sub(r'prime\s+factors?\s+of\s+\d+', f'factorint({n})', query, flags=re.IGNORECASE)

        return query


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
