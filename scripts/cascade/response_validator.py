#!/usr/bin/env python3
"""
Response Validator - Phase 1 AI Tutor Enhancement
Validates that tutoring responses follow pedagogical principles.

Ensures:
- No answer leakage (giving away the solution)
- Appropriate guiding questions
- Encouraging tone
- Reasonable length (battery efficiency)
"""

import re
from typing import Dict, Any, List, Tuple
from enum import Enum


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    CRITICAL = "critical"  # Must fix (e.g., answer leakage)
    WARNING = "warning"    # Should fix (e.g., too long)
    INFO = "info"         # Nice to fix (e.g., tone)


class ResponseValidator:
    """
    Validates tutoring responses for pedagogical quality.

    Performs multiple checks to ensure responses guide rather than solve.
    """

    # Patterns that indicate answer leakage
    ANSWER_LEAKAGE_PATTERNS = [
        r'the answer is\s+[0-9x\-\+\=\(\)\.]+\s*$',
        r'equals?\s+[0-9x\-\+\=\(\)\.]+\s*$',
        r'solution is\s+[0-9x\-\+\=\(\)\.]+\s*$',
        r'therefore,?\s+[x=]\s*[0-9\-\+\.]+\s*$',
        r'thus,?\s+[x=]\s*[0-9\-\+\.]+\s*$',
        r'\b[x-z]\s*=\s*[0-9\-\+\.]+\s*$',  # x = 4 at end
        r'final answer:\s*[0-9x\-\+\=\(\)\.]+\s*$',
    ]

    # Patterns for discouraging language
    DISCOURAGING_PHRASES = [
        r'\bwrong\b',
        r'\bincorrect\b',
        r'\bno,?\s+that',
        r'\bbad\s+(answer|attempt|try)',
        r'\bthat\'?s\s+not\s+(right|correct)',
        r'\byou\s+(failed|can\'t|don\'t\s+understand)',
    ]

    # Patterns for overly directive language (doing the work for student)
    OVERLY_DIRECTIVE_PATTERNS = [
        r'you\s+must\s+(do|use|apply)',
        r'the\s+correct\s+answer',
        r'here\'?s\s+the\s+solution',
        r'simply\s+(do|use|apply)',
        r'just\s+(do|use|apply|calculate)',
    ]

    def __init__(self):
        """Initialize the validator."""
        # Compile patterns for efficiency
        self.answer_leakage_patterns = [
            re.compile(p, re.IGNORECASE | re.MULTILINE)
            for p in self.ANSWER_LEAKAGE_PATTERNS
        ]
        self.discouraging_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in self.DISCOURAGING_PHRASES
        ]
        self.directive_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in self.OVERLY_DIRECTIVE_PATTERNS
        ]

        # Statistics
        self.stats = {
            'validations': 0,
            'critical_failures': 0,
            'warnings': 0,
            'passed': 0,
        }

    def validate(self, response: str, original_problem: str,
                 tutoring_mode: bool = True) -> Dict[str, Any]:
        """
        Validate a tutoring response for pedagogical quality.

        Args:
            response: The generated tutoring response
            original_problem: The original problem being taught
            tutoring_mode: Whether tutoring mode is enabled (skip checks if False)

        Returns:
            Dictionary with validation results:
            {
                'is_valid': bool,
                'issues': List[Dict],
                'score': float (0.0-1.0),
                'passed_checks': int,
                'total_checks': int,
                'recommendations': List[str]
            }
        """
        self.stats['validations'] += 1

        # Skip validation if not in tutoring mode
        if not tutoring_mode:
            return {
                'is_valid': True,
                'issues': [],
                'score': 1.0,
                'passed_checks': 0,
                'total_checks': 0,
                'recommendations': []
            }

        issues = []
        recommendations = []

        # Run all validation checks
        checks = [
            self._check_answer_leakage,
            self._check_question_presence,
            self._check_length,
            self._check_tone,
            self._check_structure,
        ]

        passed_checks = 0
        total_checks = len(checks)

        for check in checks:
            check_issues = check(response, original_problem)
            issues.extend(check_issues)
            if not check_issues:
                passed_checks += 1

        # Calculate score
        score = passed_checks / total_checks if total_checks > 0 else 0.0

        # Check for critical failures
        critical_issues = [i for i in issues if i['severity'] == ValidationSeverity.CRITICAL]
        is_valid = len(critical_issues) == 0

        if critical_issues:
            self.stats['critical_failures'] += 1
        else:
            if any(i['severity'] == ValidationSeverity.WARNING for i in issues):
                self.stats['warnings'] += 1
            else:
                self.stats['passed'] += 1

        # Generate recommendations
        if critical_issues:
            recommendations.append("CRITICAL: Regenerate response without revealing answer")
        if len([i for i in issues if 'question' in i['check'].lower()]) > 0:
            recommendations.append("Add 1-2 guiding questions")
        if len([i for i in issues if 'length' in i['check'].lower()]) > 0:
            recommendations.append("Shorten response to improve battery efficiency")

        return {
            'is_valid': is_valid,
            'issues': issues,
            'score': score,
            'passed_checks': passed_checks,
            'total_checks': total_checks,
            'recommendations': recommendations,
        }

    def _check_answer_leakage(self, response: str, problem: str) -> List[Dict[str, Any]]:
        """
        Check if response reveals the final answer.

        CRITICAL: This violates the core principle of tutoring.
        """
        issues = []

        for pattern in self.answer_leakage_patterns:
            match = pattern.search(response)
            if match:
                issues.append({
                    'severity': ValidationSeverity.CRITICAL,
                    'check': 'answer_leakage',
                    'message': f'Answer leaked: "{match.group()}"',
                    'location': match.span(),
                })

        # Additional check: Look for standalone final answers
        # (e.g., "x = 4" on its own line at the end)
        lines = response.strip().split('\n')
        if lines:
            last_line = lines[-1].strip()
            if re.match(r'^[x-z]\s*=\s*[\d\-\+\.]+$', last_line, re.IGNORECASE):
                issues.append({
                    'severity': ValidationSeverity.CRITICAL,
                    'check': 'answer_leakage',
                    'message': f'Final answer revealed at end: "{last_line}"',
                    'location': None,
                })

        return issues

    def _check_question_presence(self, response: str, problem: str) -> List[Dict[str, Any]]:
        """
        Check if response contains guiding questions.

        WARNING: Good tutoring should ask questions to promote thinking.
        """
        issues = []

        question_count = response.count('?')

        if question_count == 0:
            issues.append({
                'severity': ValidationSeverity.WARNING,
                'check': 'question_presence',
                'message': 'No guiding questions found',
                'location': None,
            })
        elif question_count > 4:
            issues.append({
                'severity': ValidationSeverity.WARNING,
                'check': 'question_presence',
                'message': f'Too many questions ({question_count}) - may overwhelm student',
                'location': None,
            })

        return issues

    def _check_length(self, response: str, problem: str) -> List[Dict[str, Any]]:
        """
        Check response length for battery efficiency.

        WARNING: Responses over 200 words consume more battery.
        """
        issues = []

        word_count = len(response.split())

        if word_count > 200:
            issues.append({
                'severity': ValidationSeverity.WARNING,
                'check': 'length',
                'message': f'Response too long ({word_count} words, target: <200)',
                'location': None,
            })
        elif word_count < 20:
            issues.append({
                'severity': ValidationSeverity.INFO,
                'check': 'length',
                'message': f'Response very short ({word_count} words) - may need more guidance',
                'location': None,
            })

        return issues

    def _check_tone(self, response: str, problem: str) -> List[Dict[str, Any]]:
        """
        Check for encouraging vs. discouraging tone.

        WARNING: Discouraging language harms learning motivation.
        """
        issues = []

        # Check for discouraging phrases
        for pattern in self.discouraging_patterns:
            matches = pattern.finditer(response)
            for match in matches:
                issues.append({
                    'severity': ValidationSeverity.WARNING,
                    'check': 'tone',
                    'message': f'Discouraging language: "{match.group()}"',
                    'location': match.span(),
                })

        # Check for overly directive language
        directive_count = sum(
            1 for pattern in self.directive_patterns
            if pattern.search(response)
        )

        if directive_count >= 2:
            issues.append({
                'severity': ValidationSeverity.INFO,
                'check': 'tone',
                'message': f'Overly directive ({directive_count} instances) - encourage more student agency',
                'location': None,
            })

        return issues

    def _check_structure(self, response: str, problem: str) -> List[Dict[str, Any]]:
        """
        Check response structure and formatting.

        INFO: Well-structured responses are easier to follow.
        """
        issues = []

        # Check for reasonable paragraph structure
        paragraphs = [p for p in response.split('\n\n') if p.strip()]

        if len(paragraphs) > 5:
            issues.append({
                'severity': ValidationSeverity.INFO,
                'check': 'structure',
                'message': f'Too many paragraphs ({len(paragraphs)}) - consider consolidating',
                'location': None,
            })

        # Check for presence of encouraging opener
        openers = ['great', 'good', 'excellent', 'nice', 'let\'s', 'wonderful']
        first_sentence = response.split('.')[0].lower() if '.' in response else response.lower()

        if not any(opener in first_sentence for opener in openers):
            issues.append({
                'severity': ValidationSeverity.INFO,
                'check': 'structure',
                'message': 'Consider starting with encouraging acknowledgment',
                'location': None,
            })

        return issues

    def get_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        return self.stats.copy()

    def print_stats(self):
        """Print formatted validation statistics."""
        print("\n" + "=" * 60)
        print("RESPONSE VALIDATOR STATISTICS")
        print("=" * 60)
        print(f"Total validations: {self.stats['validations']}")
        print(f"  Passed: {self.stats['passed']}")
        print(f"  Warnings: {self.stats['warnings']}")
        print(f"  Critical failures: {self.stats['critical_failures']}")

        if self.stats['validations'] > 0:
            pass_rate = (self.stats['passed'] / self.stats['validations']) * 100
            print(f"  Pass rate: {pass_rate:.1f}%")

        print("=" * 60 + "\n")


def main():
    """Test the response validator."""
    validator = ResponseValidator()

    test_cases = [
        # Good tutoring response
        ("Good tutoring", "2x + 5 = 13",
         """Great question! Let's work through this together.

What's our goal here? We want to isolate x, right?

Looking at 2x + 5 = 13, what operation is being added to 2x?

What do you think we should do first to start isolating x?

Hint: Think about undoing operations in reverse order."""),

        # Bad: Answer leakage
        ("Answer leakage", "2x + 5 = 13",
         """To solve this, subtract 5 from both sides to get 2x = 8.
Then divide both sides by 2.
The answer is x = 4."""),

        # Bad: No questions
        ("No questions", "2x + 5 = 13",
         """You need to subtract 5 from both sides and then divide by 2.
This will give you the solution."""),

        # Bad: Discouraging tone
        ("Discouraging", "2x + 5 = 13",
         """No, that's wrong. You can't do it that way.
The correct answer is to subtract 5 first."""),

        # Bad: Too long
        ("Too long", "2x + 5 = 13",
         " ".join(["This is a very long response."] * 50)),
    ]

    print("=" * 70)
    print("RESPONSE VALIDATOR TEST")
    print("=" * 70)

    for name, problem, response in test_cases:
        print(f"\n{'=' * 70}")
        print(f"TEST: {name}")
        print(f"PROBLEM: {problem}")
        print('=' * 70)

        result = validator.validate(response, problem, tutoring_mode=True)

        print(f"\nValidation: {'✓ PASSED' if result['is_valid'] else '✗ FAILED'}")
        print(f"Score: {result['score']:.2f} ({result['passed_checks']}/{result['total_checks']} checks)")

        if result['issues']:
            print("\nIssues found:")
            for issue in result['issues']:
                severity_icon = {
                    ValidationSeverity.CRITICAL: '🔴',
                    ValidationSeverity.WARNING: '🟡',
                    ValidationSeverity.INFO: '🔵',
                }[issue['severity']]
                print(f"  {severity_icon} [{issue['severity'].value.upper()}] {issue['check']}: {issue['message']}")

        if result['recommendations']:
            print("\nRecommendations:")
            for rec in result['recommendations']:
                print(f"  • {rec}")

    # Show statistics
    validator.print_stats()


if __name__ == "__main__":
    main()
