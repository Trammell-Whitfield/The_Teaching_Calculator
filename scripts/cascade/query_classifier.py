#!/usr/bin/env python3
"""
Query Classifier - Analyzes mathematical queries by type and difficulty.
"""

import re
from typing import Dict, Any, Tuple
from enum import Enum


class DifficultyLevel(Enum):
    """Difficulty levels for mathematical queries."""
    TRIVIAL = 1      # Basic arithmetic: 2+2, 5*3
    EASY = 2         # Simple algebra: 2x+5=13
    MEDIUM = 3       # Calculus, systems: derivative, matrix
    HARD = 4         # Proofs, complex word problems
    EXPERT = 5       # Research-level, advanced theory


class QueryType(Enum):
    """Types of mathematical queries."""
    ARITHMETIC = "arithmetic"
    ALGEBRA = "algebra"
    CALCULUS = "calculus"
    TRIGONOMETRY = "trigonometry"
    STATISTICS = "statistics"
    WORD_PROBLEM = "word_problem"
    PROOF = "proof"
    EXPLANATION = "explanation"
    UNKNOWN = "unknown"


class EnhancedQueryClassifier:
    """
    Enhanced classifier that determines both query type and difficulty.

    Integrates with existing MathQueryRouter for backward compatibility.
    """

    # Patterns for difficulty assessment
    TRIVIAL_PATTERNS = [
        r'^\d+[\+\-\*\/]\d+$',  # Simple arithmetic: 2+2, 5*3
        r'^\d+\s*[\+\-\*\/]\s*\d+$',
    ]

    EASY_PATTERNS = [
        r'\d*x\s*[\+\-]\s*\d+\s*=\s*\d+',  # Linear equations: 2x+5=13
        r'solve.*x.*=.*\d+',
        r'factor.*x\^2.*\d+',  # Simple quadratics
    ]

    MEDIUM_PATTERNS = [
        r'd/dx',  # Derivatives
        r'derivative',
        r'integrate',
        r'∫',
        r'matrix',
        r'determinant',
        r'system of equations',
    ]

    HARD_PATTERNS = [
        r'prove',
        r'proof',
        r'show that',
        r'demonstrate',
        r'optimization',
        r'differential equation',
    ]

    # Complexity indicators
    COMPLEXITY_INDICATORS = {
        'exponents': (r'\^\d+', 1),  # x^3 adds complexity
        'fractions': (r'\d+/\d+', 1),
        'trig_functions': (r'(sin|cos|tan|sec|csc|cot)', 2),
        'logarithms': (r'(log|ln)', 2),
        'multiple_variables': (r'[xyz].*[xyz]', 2),  # x and y
        'inequalities': (r'[<>≤≥]', 1),
        'absolute_value': (r'\|.*\|', 1),
    }

    def __init__(self):
        """Initialize the classifier."""
        pass

    def classify(self, query: str) -> Dict[str, Any]:
        """
        Classify a mathematical query by type and difficulty.

        Args:
            query: Mathematical query string

        Returns:
            Dictionary with classification results:
            {
                'type': QueryType,
                'difficulty': DifficultyLevel,
                'difficulty_score': int (1-5),
                'complexity_factors': list,
                'estimated_time': float (seconds),
                'recommended_layer': str,
                'confidence': float (0.0-1.0)
            }
        """
        query_lower = query.lower().strip()

        # Determine query type
        query_type = self._classify_type(query_lower)

        # Determine difficulty
        difficulty, complexity_factors = self._assess_difficulty(query, query_lower)

        # Estimate solving time
        estimated_time = self._estimate_time(difficulty, query_type)

        # Recommend layer
        recommended_layer = self._recommend_layer(query_type, difficulty)

        # Confidence score
        confidence = self._calculate_confidence(query_type, difficulty, complexity_factors)

        return {
            'type': query_type,
            'difficulty': difficulty,
            'difficulty_score': difficulty.value,
            'complexity_factors': complexity_factors,
            'estimated_time': estimated_time,
            'recommended_layer': recommended_layer,
            'confidence': confidence,
            'reasoning': self._generate_reasoning(query_type, difficulty, complexity_factors)
        }

    def _classify_type(self, query: str) -> QueryType:
        """Determine the type of mathematical query."""
        # Proofs
        if any(kw in query for kw in ['prove', 'proof', 'show that']):
            return QueryType.PROOF

        # Explanations
        if any(kw in query for kw in ['explain', 'why', 'what is', 'how does']):
            return QueryType.EXPLANATION

        # Word problems
        if self._is_word_problem(query):
            return QueryType.WORD_PROBLEM

        # Calculus
        if any(kw in query for kw in ['derivative', 'd/dx', 'integrate', 'limit']):
            return QueryType.CALCULUS

        # Trigonometry
        if any(kw in query for kw in ['sin', 'cos', 'tan', 'angle', 'triangle']):
            return QueryType.TRIGONOMETRY

        # Statistics
        if any(kw in query for kw in ['mean', 'median', 'standard deviation', 'probability']):
            return QueryType.STATISTICS

        # Algebra (includes equations)
        if any(kw in query for kw in ['solve', 'factor', 'expand', 'simplify', '=']):
            return QueryType.ALGEBRA

        # Arithmetic
        if re.match(r'^[\d\s\+\-\*\/\(\)\.]+$', query):
            return QueryType.ARITHMETIC

        return QueryType.UNKNOWN

    def _assess_difficulty(self, query: str, query_lower: str) -> Tuple[DifficultyLevel, list]:
        """
        Assess the difficulty level of a query.

        Returns:
            (difficulty_level, complexity_factors)
        """
        complexity_factors = []
        base_difficulty = 0

        # Check trivial patterns
        for pattern in self.TRIVIAL_PATTERNS:
            if re.match(pattern, query_lower):
                return DifficultyLevel.TRIVIAL, ['basic_arithmetic']

        # Check easy patterns
        for pattern in self.EASY_PATTERNS:
            if re.search(pattern, query_lower):
                base_difficulty = max(base_difficulty, 2)
                complexity_factors.append('simple_equation')

        # Check medium patterns
        for pattern in self.MEDIUM_PATTERNS:
            if re.search(pattern, query_lower):
                base_difficulty = max(base_difficulty, 3)
                complexity_factors.append('calculus_or_linear_algebra')

        # Check hard patterns
        for pattern in self.HARD_PATTERNS:
            if re.search(pattern, query_lower):
                base_difficulty = max(base_difficulty, 4)
                complexity_factors.append('proof_or_advanced_concept')

        # Add complexity indicators
        complexity_score = 0
        for name, (pattern, weight) in self.COMPLEXITY_INDICATORS.items():
            if re.search(pattern, query):
                complexity_score += weight
                complexity_factors.append(name)

        # Adjust difficulty based on complexity
        if complexity_score >= 4:
            base_difficulty = min(base_difficulty + 1, 5)
        elif complexity_score >= 2:
            base_difficulty = max(base_difficulty, 3)

        # Default to EASY if no patterns matched
        if base_difficulty == 0:
            base_difficulty = 2

        return DifficultyLevel(base_difficulty), complexity_factors

    def _is_word_problem(self, query: str) -> bool:
        """Detect if query is a word problem."""
        indicators = [
            len(query.split()) > 15,  # Long queries
            any(name in query for name in ['alice', 'bob', 'train', 'car', 'store', 'apples']),
            '?' in query and not any(op in query for op in ['=', 'd/dx', '∫']),
            any(word in query for word in ['if ', 'then', 'how many', 'how much'])
        ]
        return sum(indicators) >= 2

    def _estimate_time(self, difficulty: DifficultyLevel, query_type: QueryType) -> float:
        """
        Estimate solving time in seconds.

        Based on difficulty level and query type.
        """
        # Base time by difficulty
        base_times = {
            DifficultyLevel.TRIVIAL: 0.01,   # Instant
            DifficultyLevel.EASY: 0.5,       # SymPy fast
            DifficultyLevel.MEDIUM: 2.0,     # SymPy or Wolfram
            DifficultyLevel.HARD: 15.0,      # LLM needed
            DifficultyLevel.EXPERT: 45.0,    # Complex LLM reasoning
        }

        # Adjustments by type
        type_multipliers = {
            QueryType.ARITHMETIC: 0.5,
            QueryType.ALGEBRA: 1.0,
            QueryType.CALCULUS: 1.5,
            QueryType.WORD_PROBLEM: 2.0,
            QueryType.PROOF: 3.0,
            QueryType.EXPLANATION: 2.5,
        }

        base_time = base_times.get(difficulty, 5.0)
        multiplier = type_multipliers.get(query_type, 1.0)

        return base_time * multiplier

    def _recommend_layer(self, query_type: QueryType, difficulty: DifficultyLevel) -> str:
        """Recommend which cascade layer to use."""
        # Proofs and explanations always go to LLM
        if query_type in [QueryType.PROOF, QueryType.EXPLANATION]:
            return 'llm'

        # Word problems go to LLM
        if query_type == QueryType.WORD_PROBLEM:
            return 'llm'

        # By difficulty
        if difficulty == DifficultyLevel.TRIVIAL:
            return 'sympy'
        elif difficulty == DifficultyLevel.EASY:
            return 'sympy'
        elif difficulty == DifficultyLevel.MEDIUM:
            return 'sympy'  # Try SymPy first, cascade to Wolfram
        elif difficulty == DifficultyLevel.HARD:
            return 'llm'
        else:  # EXPERT
            return 'llm'

    def _calculate_confidence(self, query_type: QueryType, difficulty: DifficultyLevel,
                             complexity_factors: list) -> float:
        """Calculate confidence in the classification."""
        # Start with base confidence
        confidence = 0.7

        # Increase if type is certain
        if query_type in [QueryType.PROOF, QueryType.ARITHMETIC]:
            confidence += 0.2

        # Increase if difficulty indicators are strong
        if len(complexity_factors) >= 3:
            confidence += 0.1

        # Decrease if unknown type
        if query_type == QueryType.UNKNOWN:
            confidence -= 0.3

        return min(max(confidence, 0.0), 1.0)

    def _generate_reasoning(self, query_type: QueryType, difficulty: DifficultyLevel,
                           complexity_factors: list) -> str:
        """Generate human-readable reasoning for the classification."""
        parts = [
            f"Type: {query_type.value}",
            f"Difficulty: {difficulty.name}",
        ]

        if complexity_factors:
            factors_str = ', '.join(complexity_factors[:3])
            parts.append(f"Complexity: {factors_str}")

        return " | ".join(parts)


def main():
    """Test the classifier."""
    classifier = EnhancedQueryClassifier()

    test_queries = [
        "2 + 2",
        "Solve: 2x + 5 = 13",
        "What is the derivative of x^3 + 2x^2?",
        "Prove that sqrt(2) is irrational",
        "If Alice has 10 apples and gives 3 to Bob, how many does she have left?",
        "Find the eigenvalues of the matrix [[1, 2], [3, 4]]",
        "Explain why 1 + 1 = 2",
    ]

    print("\n" + "="*70)
    print("QUERY CLASSIFIER TEST")
    print("="*70)

    for query in test_queries:
        result = classifier.classify(query)

        print(f"\nQuery: {query}")
        print(f"  Type: {result['type'].value}")
        print(f"  Difficulty: {result['difficulty'].name} (score: {result['difficulty_score']})")
        print(f"  Estimated time: {result['estimated_time']:.2f}s")
        print(f"  Recommended: {result['recommended_layer']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Reasoning: {result['reasoning']}")


if __name__ == "__main__":
    main()
