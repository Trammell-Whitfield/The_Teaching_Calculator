#!/usr/bin/env python3
"""
Pedagogical Wrapper - Phase 1 AI Tutor Enhancement
Integrates intent classification, tutoring templates, and response validation.

Main orchestrator for tutoring mode that wraps LLM responses in
pedagogically-sound scaffolding.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from intent_classifier import IntentClassifier, UserIntent
from tutoring_templates import TutoringTemplates, TutoringMode
from response_validator import ResponseValidator


class PedagogicalWrapper:
    """
    Wraps LLM interactions to provide pedagogically-sound tutoring.

    Flow:
    1. Classify user intent (tutoring vs. quick answer)
    2. Select appropriate teaching template
    3. Generate response via LLM
    4. Validate response quality
    5. Return validated tutoring response
    """

    def __init__(self):
        """Initialize the pedagogical wrapper."""
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.intent_classifier = IntentClassifier()
        self.validator = ResponseValidator()

        # Statistics
        self.stats = {
            'total_queries': 0,
            'tutoring_mode_queries': 0,
            'quick_answer_queries': 0,
            'validation_failures': 0,
            'regenerations': 0,
        }

    def prepare_prompt(self, query: str, student_answer: Optional[str] = None,
                      force_mode: Optional[str] = None) -> Dict[str, Any]:
        """
        Prepare pedagogically-appropriate prompt for LLM.

        Args:
            query: User's query
            student_answer: Optional student answer for verification
            force_mode: Force specific mode ('tutoring', 'quick_answer', None)

        Returns:
            Dictionary with prompt and metadata:
            {
                'prompt': str,              # Formatted prompt for LLM
                'tutoring_mode': bool,      # Whether tutoring mode enabled
                'intent': UserIntent,       # Classified intent
                'mode': TutoringMode,       # Selected tutoring mode
                'original_query': str,      # Original query
                'student_answer': str or None,
                'metadata': dict           # Additional context
            }
        """
        self.stats['total_queries'] += 1

        # Step 1: Classify intent
        if force_mode == 'quick_answer':
            # Skip classification, use direct answer
            intent_result = {
                'intent': UserIntent.QUICK_ANSWER,
                'enable_tutoring_mode': False,
                'extracted_problem': query,
                'student_answer': None,
                'confidence': 1.0,
                'reasoning': 'User-forced quick answer mode'
            }
        elif force_mode == 'tutoring':
            # Force tutoring mode
            intent_result = {
                'intent': UserIntent.TUTORING,
                'enable_tutoring_mode': True,
                'extracted_problem': query,
                'student_answer': student_answer,
                'confidence': 1.0,
                'reasoning': 'User-forced tutoring mode'
            }
        else:
            # Auto-classify
            intent_result = self.intent_classifier.classify(query, student_answer)

        tutoring_enabled = intent_result['enable_tutoring_mode']

        if tutoring_enabled:
            self.stats['tutoring_mode_queries'] += 1
        else:
            self.stats['quick_answer_queries'] += 1

        self.logger.info(f"Intent: {intent_result['intent'].value} "
                        f"(confidence: {intent_result['confidence']:.2f})")
        self.logger.debug(f"Reasoning: {intent_result['reasoning']}")

        # Step 2: Select appropriate tutoring mode
        tutoring_mode = self._select_tutoring_mode(
            intent_result['intent'],
            intent_result['extracted_problem']
        )

        self.logger.info(f"Tutoring mode: {tutoring_mode.value}")

        # Step 3: Generate prompt using appropriate template
        problem = intent_result['extracted_problem']
        prompt = TutoringTemplates.select_template(
            mode=tutoring_mode,
            problem=problem,
            student_answer=intent_result.get('student_answer')
        )

        return {
            'prompt': prompt,
            'tutoring_mode': tutoring_enabled,
            'intent': intent_result['intent'],
            'mode': tutoring_mode,
            'original_query': query,
            'student_answer': intent_result.get('student_answer'),
            'metadata': {
                'confidence': intent_result['confidence'],
                'reasoning': intent_result['reasoning'],
                'extracted_problem': problem,
            }
        }

    def validate_response(self, response: str, original_problem: str,
                         tutoring_mode: bool = True) -> Dict[str, Any]:
        """
        Validate LLM response for pedagogical quality.

        Args:
            response: Generated LLM response
            original_problem: Original problem statement
            tutoring_mode: Whether tutoring mode is enabled

        Returns:
            Validation results from ResponseValidator
        """
        validation_result = self.validator.validate(
            response=response,
            original_problem=original_problem,
            tutoring_mode=tutoring_mode
        )

        if not validation_result['is_valid']:
            self.stats['validation_failures'] += 1
            self.logger.warning(f"Response validation failed: {len(validation_result['issues'])} issues")

        return validation_result

    def _select_tutoring_mode(self, intent: UserIntent, problem: str) -> TutoringMode:
        """
        Select appropriate tutoring mode based on intent and problem type.

        Args:
            intent: Classified user intent
            problem: The mathematical problem

        Returns:
            Appropriate TutoringMode
        """
        # Map intent to tutoring mode
        intent_to_mode = {
            UserIntent.TUTORING: TutoringMode.STANDARD_PROBLEM,
            UserIntent.EXPLANATION: TutoringMode.CONCEPT_EXPLANATION,
            UserIntent.VERIFICATION: TutoringMode.VERIFICATION,
            UserIntent.QUICK_ANSWER: TutoringMode.QUICK_ANSWER,
        }

        mode = intent_to_mode.get(intent, TutoringMode.STANDARD_PROBLEM)

        # Override with word problem mode if detected
        if self._is_word_problem(problem) and mode == TutoringMode.STANDARD_PROBLEM:
            mode = TutoringMode.WORD_PROBLEM

        return mode

    def _is_word_problem(self, query: str) -> bool:
        """Detect if query is a word problem."""
        indicators = [
            len(query.split()) > 15,
            any(name in query.lower() for name in ['alice', 'bob', 'train', 'car', 'store', 'apples']),
            '?' in query and not any(op in query for op in ['=', 'd/dx', '∫']),
            any(word in query.lower() for word in ['if ', 'then', 'how many', 'how much'])
        ]
        return sum(indicators) >= 2

    def extract_answer_from_response(self, response: str) -> Optional[str]:
        """
        Extract final answer from LLM response (if present).

        This is used for quick_answer mode to maintain backward compatibility
        with existing answer extraction logic.

        Args:
            response: Full LLM response

        Returns:
            Extracted answer or None
        """
        import re

        # Patterns to extract answers (from llm_handler.py)
        patterns = [
            r"\\boxed\{([^}]+)\}",
            r"####\s*([^\n]+)",
            r"(?:The answer is|Answer:|Final answer:)\s*[:]*\s*\$?\\?\[?\s*([^\\$\n]+)",
            r"Therefore,?\s+([^\n.]+)[.\n]",
            r"Thus,?\s+([^\n.]+)[.\n]",
            r"=\s*([0-9.x\-+*/^()]+)\s*(?:\n|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE | re.MULTILINE)
            if match:
                answer = match.group(1).strip()
                answer = answer.strip('*').rstrip('.')
                return answer

        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        stats = {
            'wrapper': self.stats.copy(),
            'intent_classifier': self.intent_classifier.get_stats(),
            'validator': self.validator.get_stats(),
        }

        # Add derived metrics
        if self.stats['total_queries'] > 0:
            stats['wrapper']['tutoring_mode_percentage'] = (
                self.stats['tutoring_mode_queries'] / self.stats['total_queries'] * 100
            )
            stats['wrapper']['validation_failure_rate'] = (
                self.stats['validation_failures'] / self.stats['tutoring_mode_queries'] * 100
                if self.stats['tutoring_mode_queries'] > 0 else 0
            )

        return stats

    def print_stats(self):
        """Print formatted statistics."""
        print("\n" + "=" * 70)
        print("PEDAGOGICAL WRAPPER STATISTICS")
        print("=" * 70)

        print("\n📊 OVERALL:")
        print(f"   Total queries: {self.stats['total_queries']}")
        print(f"   Tutoring mode: {self.stats['tutoring_mode_queries']} "
              f"({self.stats['tutoring_mode_queries']/max(self.stats['total_queries'], 1)*100:.1f}%)")
        print(f"   Quick answer: {self.stats['quick_answer_queries']} "
              f"({self.stats['quick_answer_queries']/max(self.stats['total_queries'], 1)*100:.1f}%)")
        print(f"   Validation failures: {self.stats['validation_failures']}")
        print(f"   Regenerations needed: {self.stats['regenerations']}")

        print("\n" + "=" * 70)

        # Print component stats
        print("\nINTENT CLASSIFIER:")
        print("─" * 70)
        self.intent_classifier.print_stats()

        print("\nRESPONSE VALIDATOR:")
        print("─" * 70)
        self.validator.print_stats()


def main():
    """Test the pedagogical wrapper."""
    import logging
    logging.basicConfig(level=logging.INFO)

    wrapper = PedagogicalWrapper()

    test_queries = [
        # Tutoring requests
        ("How do I solve 2x + 5 = 13?", None, None),
        ("Help me find the derivative of x^2", None, None),

        # Explanation requests
        ("Explain what a derivative is", None, None),
        ("What is the quadratic formula?", None, None),

        # Verification requests
        ("Is x = 4 correct for 2x + 5 = 13?", None, None),
        ("My answer is 42, is that right?", "42", None),

        # Quick answer (forced)
        ("Solve: 2x + 5 = 13", None, 'quick_answer'),

        # Quick answer (auto-detected)
        ("Calculate 123 * 456", None, None),

        # Word problem
        ("If Alice has 10 apples and gives 3 to Bob, how many does she have?", None, None),
    ]

    print("=" * 70)
    print("PEDAGOGICAL WRAPPER TEST")
    print("=" * 70)

    for query, student_answer, force_mode in test_queries:
        print(f"\n{'=' * 70}")
        print(f"QUERY: {query}")
        if student_answer:
            print(f"STUDENT ANSWER: {student_answer}")
        if force_mode:
            print(f"FORCED MODE: {force_mode}")
        print('=' * 70)

        result = wrapper.prepare_prompt(query, student_answer, force_mode)

        print(f"\nIntent: {result['intent'].value}")
        print(f"Tutoring mode: {'ENABLED' if result['tutoring_mode'] else 'DISABLED'}")
        print(f"Mode: {result['mode'].value}")
        print(f"Confidence: {result['metadata']['confidence']:.2f}")
        print(f"Reasoning: {result['metadata']['reasoning']}")

        print(f"\nGenerated Prompt Preview (first 300 chars):")
        print("─" * 70)
        print(result['prompt'][:300] + "...")

    # Show statistics
    wrapper.print_stats()


if __name__ == "__main__":
    main()
