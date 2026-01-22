#!/usr/bin/env python3
"""
Intent Classifier - Phase 1 AI Tutor Enhancement
Classifies user intent to determine teaching mode vs. direct answer mode.

This lightweight classifier determines whether the user wants:
- A) Tutoring/guidance through problem-solving
- B) Concept explanation
- C) Answer verification/checking
- D) Quick direct answer

Battery-optimized: Uses rule-based classification first, LLM only for ambiguous cases.
"""

import re
from typing import Dict, Any, Optional
from enum import Enum


class UserIntent(Enum):
    """User's learning intent."""
    TUTORING = "tutoring"           # Wants step-by-step guidance
    EXPLANATION = "explanation"     # Wants concept clarification
    VERIFICATION = "verification"   # Wants to check their answer
    QUICK_ANSWER = "quick_answer"   # Just wants the answer
    UNKNOWN = "unknown"             # Unclear intent


class IntentClassifier:
    """
    Lightweight intent classifier using rule-based patterns.

    Optimized for battery life - uses simple keyword matching
    instead of expensive LLM calls for most queries.
    """

    # Explicit tutoring request patterns
    TUTORING_PATTERNS = [
        r'\bhow (do|can|should) i\b',
        r'\bhelp me\b',
        r'\bguide me\b',
        r'\bwalk (me )?through\b',
        r'\bshow me how\b',
        r'\bteach me\b',
        r'\bi (don\'t know|don\'t understand|\'m stuck)\b',
        r'\bcan you help\b',
        r'\bsteps? (to|for)\b',
        r'\bwhere (do|should) i start\b',
    ]

    # Explanation request patterns
    EXPLANATION_PATTERNS = [
        r'\bexplain\b',
        r'\bwhat (is|are|does)\b',
        r'\bwhy (is|does|do)\b',
        r'\bhow does .* work\b',
        r'\bwhat does .* mean\b',
        r'\bmean(ing)? of\b',
        r'\bdefinition of\b',
        r'\binterpret\b',
        r'\bunderstand(ing)?\b',
    ]

    # Verification patterns
    VERIFICATION_PATTERNS = [
        r'\bis (this|my answer) (right|correct)\b',
        r'\bcheck (this|my (answer|work))\b',
        r'\bdid i (get|do) (this|it) (right|correctly)\b',
        r'\bi (got|think|believe) .* (is|equals)\b',
        r'\bverify\b',
        r'\bconfirm\b',
        r'\bmy answer is\b',
    ]

    # Quick answer indicators
    QUICK_ANSWER_PATTERNS = [
        r'^\s*what is \d+[\+\-\*\/]\d+\s*\??$',  # "what is 2+2?"
        r'^\s*calculate\b',
        r'^\s*compute\b',
        r'^\s*evaluate\b',
        r'^\s*(solve|find|simplify|factor|expand):?\s',  # Imperative commands
    ]

    def __init__(self):
        """Initialize the intent classifier."""
        # Compile patterns for efficiency
        self.tutoring_patterns = [re.compile(p, re.IGNORECASE) for p in self.TUTORING_PATTERNS]
        self.explanation_patterns = [re.compile(p, re.IGNORECASE) for p in self.EXPLANATION_PATTERNS]
        self.verification_patterns = [re.compile(p, re.IGNORECASE) for p in self.VERIFICATION_PATTERNS]
        self.quick_answer_patterns = [re.compile(p, re.IGNORECASE) for p in self.QUICK_ANSWER_PATTERNS]

        # Statistics
        self.stats = {
            'classifications': 0,
            'tutoring': 0,
            'explanation': 0,
            'verification': 0,
            'quick_answer': 0,
            'unknown': 0,
        }

    def classify(self, query: str, student_answer: Optional[str] = None) -> Dict[str, Any]:
        """
        Classify user intent from query.

        Args:
            query: User's query string
            student_answer: Optional student answer for verification mode

        Returns:
            Dictionary with classification:
            {
                'intent': UserIntent,
                'confidence': float (0.0-1.0),
                'reasoning': str,
                'enable_tutoring_mode': bool,
                'extracted_problem': str or None,
                'student_answer': str or None
            }
        """
        self.stats['classifications'] += 1

        query_lower = query.lower().strip()

        # If student provided their answer, likely verification
        if student_answer or self._extract_student_answer(query):
            extracted_answer = student_answer or self._extract_student_answer(query)
            self.stats['verification'] += 1
            return {
                'intent': UserIntent.VERIFICATION,
                'confidence': 0.95,
                'reasoning': 'Student provided answer for checking',
                'enable_tutoring_mode': True,
                'extracted_problem': self._extract_problem_from_verification(query),
                'student_answer': extracted_answer
            }

        # Check for explicit tutoring requests
        tutoring_score = sum(1 for p in self.tutoring_patterns if p.search(query_lower))
        if tutoring_score > 0:
            self.stats['tutoring'] += 1
            return {
                'intent': UserIntent.TUTORING,
                'confidence': min(0.7 + (tutoring_score * 0.1), 0.95),
                'reasoning': f'Explicit tutoring keywords (score: {tutoring_score})',
                'enable_tutoring_mode': True,
                'extracted_problem': self._extract_problem(query),
                'student_answer': None
            }

        # Check for explanation requests
        explanation_score = sum(1 for p in self.explanation_patterns if p.search(query_lower))
        if explanation_score > 0:
            self.stats['explanation'] += 1
            return {
                'intent': UserIntent.EXPLANATION,
                'confidence': min(0.7 + (explanation_score * 0.1), 0.95),
                'reasoning': f'Explanation keywords (score: {explanation_score})',
                'enable_tutoring_mode': True,
                'extracted_problem': query,  # The whole query is the concept
                'student_answer': None
            }

        # Check for quick answer patterns
        quick_score = sum(1 for p in self.quick_answer_patterns if p.search(query_lower))
        if quick_score > 0:
            self.stats['quick_answer'] += 1
            return {
                'intent': UserIntent.QUICK_ANSWER,
                'confidence': 0.85,
                'reasoning': 'Imperative command for direct answer',
                'enable_tutoring_mode': False,  # Direct answer mode
                'extracted_problem': query,
                'student_answer': None
            }

        # Default: Assume tutoring mode for educational context
        # Better to teach when uncertain than to just give answers
        self.stats['tutoring'] += 1
        return {
            'intent': UserIntent.TUTORING,
            'confidence': 0.60,
            'reasoning': 'Default to tutoring mode (educational context)',
            'enable_tutoring_mode': True,
            'extracted_problem': query,
            'student_answer': None
        }

    def _extract_student_answer(self, query: str) -> Optional[str]:
        """
        Extract student's proposed answer from verification queries.

        Examples:
        - "Is x = 4 correct?" → "x = 4"
        - "I think the answer is 42" → "42"
        - "My answer: 3.14159" → "3.14159"
        """
        patterns = [
            r'i (think|believe|got) (?:the answer is |that )?(.+?)(?:\?|$)',
            r'my answer(?: is)?:?\s*(.+?)(?:\?|$)',
            r'is (.+?) (?:right|correct|the answer)\??',
        ]

        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                # Extract the answer (last captured group)
                answer = match.group(match.lastindex).strip()
                return answer

        return None

    def _extract_problem_from_verification(self, query: str) -> str:
        """Extract the original problem from a verification query."""
        # Remove verification language to get problem
        verification_phrases = [
            r'\bis (this|my answer) (right|correct)\??',
            r'\bcheck (this|my (answer|work))\b',
            r'\bdid i (get|do) (this|it) (right|correctly)\??',
            r'\bi (got|think|believe)',
            r'\bmy answer(?: is)?:?',
        ]

        cleaned = query
        for phrase in verification_phrases:
            cleaned = re.sub(phrase, '', cleaned, flags=re.IGNORECASE)

        return cleaned.strip()

    def _extract_problem(self, query: str) -> str:
        """
        Extract the core mathematical problem from a tutoring request.

        Examples:
        - "How do I solve 2x + 5 = 13?" → "2x + 5 = 13"
        - "Help me find the derivative of x^2" → "derivative of x^2"
        """
        # Remove common tutoring preambles
        tutoring_preambles = [
            r'^(how (do|can|should) i|help me|guide me|show me how to|teach me to)\s+',
            r'^(can you help( me)? with|i need help with)\s+',
        ]

        cleaned = query
        for preamble in tutoring_preambles:
            cleaned = re.sub(preamble, '', cleaned, flags=re.IGNORECASE)

        return cleaned.strip()

    def get_stats(self) -> Dict[str, Any]:
        """Get classification statistics."""
        return self.stats.copy()

    def print_stats(self):
        """Print formatted statistics."""
        print("\n" + "=" * 60)
        print("INTENT CLASSIFIER STATISTICS")
        print("=" * 60)
        print(f"Total classifications: {self.stats['classifications']}")

        if self.stats['classifications'] > 0:
            for intent in ['tutoring', 'explanation', 'verification', 'quick_answer', 'unknown']:
                count = self.stats[intent]
                pct = (count / self.stats['classifications']) * 100
                print(f"  {intent.capitalize():15s}: {count:3d} ({pct:5.1f}%)")

        print("=" * 60 + "\n")


def main():
    """Test the intent classifier."""
    classifier = IntentClassifier()

    test_queries = [
        # Tutoring requests
        ("How do I solve 2x + 5 = 13?", None),
        ("Help me find the derivative of x^2", None),
        ("I'm stuck on this integral", None),
        ("Can you guide me through factoring x^2 - 9?", None),

        # Explanation requests
        ("Explain what a derivative is", None),
        ("What does the quadratic formula mean?", None),
        ("Why is sqrt(2) irrational?", None),

        # Verification requests
        ("Is x = 4 correct?", None),
        ("I think the answer is 42", None),
        ("Check my work: x = 3", None),
        ("My answer is 3.14159, is that right?", None),

        # Quick answer requests
        ("Solve: 2x + 5 = 13", None),
        ("What is 2 + 2?", None),
        ("Calculate 123 * 456", None),
        ("Evaluate sin(0)", None),

        # Ambiguous
        ("derivative of x^3", None),
        ("2x + 5 = 13", None),
    ]

    print("\n" + "=" * 70)
    print("INTENT CLASSIFIER TEST")
    print("=" * 70)

    for query, student_answer in test_queries:
        result = classifier.classify(query, student_answer)

        print(f"\nQuery: {query}")
        if student_answer:
            print(f"Student answer: {student_answer}")
        print(f"  Intent: {result['intent'].value}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Tutoring mode: {'YES' if result['enable_tutoring_mode'] else 'NO'}")
        print(f"  Reasoning: {result['reasoning']}")
        if result['extracted_problem']:
            print(f"  Extracted problem: {result['extracted_problem']}")
        if result['student_answer']:
            print(f"  Student's answer: {result['student_answer']}")

    # Show statistics
    classifier.print_stats()


if __name__ == "__main__":
    main()
