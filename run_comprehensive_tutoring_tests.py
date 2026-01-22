#!/usr/bin/env python3
"""
Comprehensive Tutoring System Test Runner

Tests the Phase 1 tutoring system on the full comprehensive test bank.
Validates intent classification, pedagogical quality, and response validation
across 100s of problems.
"""

import sys
import json
import time
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent / 'scripts' / 'cascade'))

from pedagogical_wrapper import PedagogicalWrapper
from response_validator import ResponseValidator
from intent_classifier import UserIntent


class ComprehensiveTester:
    """Runs comprehensive tests on full test bank."""

    def __init__(self, testbank_path='test_data/comprehensive_integration_testbank.json'):
        """Initialize tester."""
        self.wrapper = PedagogicalWrapper()
        self.validator = ResponseValidator()

        # Load test bank
        self.problems = self._load_testbank(testbank_path)
        print(f"✓ Loaded {len(self.problems)} problems from test bank")

        # Results tracking
        self.results = {
            'total_tested': 0,
            'by_difficulty': defaultdict(lambda: {'total': 0, 'tutoring_enabled': 0}),
            'by_source': defaultdict(lambda: {'total': 0, 'tutoring_enabled': 0}),
            'by_category': defaultdict(lambda: {'total': 0, 'tutoring_enabled': 0}),
            'intent_distribution': defaultdict(int),
            'tutoring_mode_rate': 0,
        }

    def _load_testbank(self, path):
        """Load test bank from JSON."""
        testbank_file = Path(path)

        if not testbank_file.exists():
            print(f"\n⚠️  Test bank not found: {path}")
            print(f"   Run: python build_comprehensive_testbank.py")
            sys.exit(1)

        with open(testbank_file, 'r', encoding='utf-8') as f:
            problems = json.load(f)

        return problems

    def test_intent_classification(self, sample_size=None):
        """Test intent classification on all problems."""
        print("\n" + "=" * 70)
        print("TEST 1: INTENT CLASSIFICATION")
        print("=" * 70)

        problems_to_test = self.problems[:sample_size] if sample_size else self.problems

        tutoring_enabled_count = 0

        for i, problem in enumerate(problems_to_test, 1):
            # Convert problem to natural tutoring query
            query = self._format_as_student_query(problem['problem'])

            # Classify intent
            prompt_result = self.wrapper.prepare_prompt(query)

            # Track results
            self.results['total_tested'] += 1
            self.results['intent_distribution'][prompt_result['intent'].value] += 1

            if prompt_result['tutoring_mode']:
                tutoring_enabled_count += 1

            # Update by-category stats
            difficulty = problem.get('difficulty', 3)
            source = problem.get('source', 'Unknown')
            category = problem.get('category', 'general')

            self.results['by_difficulty'][difficulty]['total'] += 1
            self.results['by_source'][source]['total'] += 1
            self.results['by_category'][category]['total'] += 1

            if prompt_result['tutoring_mode']:
                self.results['by_difficulty'][difficulty]['tutoring_enabled'] += 1
                self.results['by_source'][source]['tutoring_enabled'] += 1
                self.results['by_category'][category]['tutoring_enabled'] += 1

            # Show progress
            if i % 50 == 0:
                print(f"  Processed {i}/{len(problems_to_test)} problems...")

        self.results['tutoring_mode_rate'] = tutoring_enabled_count / len(problems_to_test)

        print(f"\n✓ Tested {len(problems_to_test)} problems")
        print(f"  Tutoring mode enabled: {tutoring_enabled_count}/{len(problems_to_test)} ({self.results['tutoring_mode_rate']*100:.1f}%)")

    def test_prompt_generation(self, sample_size=10):
        """Test prompt generation quality on sample."""
        print("\n" + "=" * 70)
        print("TEST 2: PROMPT GENERATION QUALITY")
        print("=" * 70)

        # Get diverse sample across difficulties
        samples = self._get_stratified_sample(sample_size)

        for i, problem in enumerate(samples, 1):
            query = self._format_as_student_query(problem['problem'])
            prompt_result = self.wrapper.prepare_prompt(query)

            print(f"\nSample {i}/{len(samples)}")
            print(f"  Problem: {problem['problem'][:60]}...")
            print(f"  Difficulty: {problem.get('difficulty', 'N/A')}")
            print(f"  Intent: {prompt_result['intent'].value}")
            print(f"  Mode: {prompt_result['mode'].value}")
            print(f"  Tutoring: {'ENABLED' if prompt_result['tutoring_mode'] else 'DISABLED'}")
            print(f"  Prompt length: {len(prompt_result['prompt'])} chars")

            # Check for pedagogical rules in tutoring prompts
            if prompt_result['tutoring_mode']:
                has_rules = 'CRITICAL RULES' in prompt_result['prompt'] or 'RULES' in prompt_result['prompt']
                print(f"  Contains rules: {has_rules}")

    def test_validation_on_responses(self, sample_size=20):
        """Test response validation on simulated responses."""
        print("\n" + "=" * 70)
        print("TEST 3: RESPONSE VALIDATION")
        print("=" * 70)

        samples = self._get_stratified_sample(sample_size)

        good_responses = 0
        answer_leakage = 0

        # Simulated responses (mix of good and bad)
        response_templates = [
            # Good tutoring responses
            {
                'template': "Great question! Let's think about this step by step.\n\nWhat approach do you think we should use?\n\nHint: Consider {technique}.",
                'should_pass': True,
            },
            {
                'template': "This requires {technique}. Can you identify the pattern?\n\nWhat do you notice about the structure?",
                'should_pass': True,
            },
            # Bad response (answer leakage)
            {
                'template': "The answer is {answer}.",
                'should_pass': False,
            },
        ]

        for i, problem in enumerate(samples, 1):
            query = self._format_as_student_query(problem['problem'])
            prompt_result = self.wrapper.prepare_prompt(query)

            if not prompt_result['tutoring_mode']:
                continue

            # Simulate response (alternating good/bad)
            template = response_templates[i % len(response_templates)]
            simulated_response = template['template'].format(
                technique=problem.get('category', 'substitution'),
                answer=problem.get('answer', 'unknown')
            )

            # Validate
            validation = self.validator.validate(
                response=simulated_response,
                original_problem=query,
                tutoring_mode=True
            )

            if validation['is_valid']:
                good_responses += 1
            if not validation['is_valid'] and not template['should_pass']:
                # Correctly detected bad response
                answer_leakage += 1

            if i <= 5:  # Show first 5
                print(f"\nValidation {i}:")
                print(f"  Valid: {'✓' if validation['is_valid'] else '✗'}")
                print(f"  Score: {validation['score']:.2f}")
                if validation['issues']:
                    print(f"  Issues: {len(validation['issues'])}")

        print(f"\n✓ Validated {sample_size} simulated responses")
        print(f"  Good responses passed: {good_responses}")
        print(f"  Answer leakage detected: {answer_leakage}")

    def _format_as_student_query(self, problem_text):
        """Convert problem statement to natural student query."""
        # Add tutoring phrasing to some problems
        phrasings = [
            f"How do I {problem_text}?",
            f"Help me with: {problem_text}",
            f"{problem_text}",
            f"Can you guide me through {problem_text}?",
            f"What is {problem_text}?",
        ]

        import random
        return random.choice(phrasings)

    def _get_stratified_sample(self, n):
        """Get stratified sample across difficulties."""
        samples = []
        difficulties = sorted(set(p.get('difficulty', 3) for p in self.problems))

        per_difficulty = max(1, n // len(difficulties))

        for diff in difficulties:
            diff_problems = [p for p in self.problems if p.get('difficulty') == diff]
            import random
            samples.extend(random.sample(diff_problems, min(per_difficulty, len(diff_problems))))

        return samples[:n]

    def print_summary(self):
        """Print comprehensive summary of results."""
        print("\n" + "=" * 70)
        print("COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)

        print(f"\nTotal problems tested: {self.results['total_tested']}")
        print(f"Tutoring mode enabled: {self.results['tutoring_mode_rate']*100:.1f}%")

        print(f"\nIntent distribution:")
        for intent, count in sorted(self.results['intent_distribution'].items()):
            pct = (count / self.results['total_tested']) * 100
            print(f"  {intent:20s}: {count:4d} ({pct:5.1f}%)")

        print(f"\nTutoring mode by difficulty:")
        for diff in sorted(self.results['by_difficulty'].keys()):
            stats = self.results['by_difficulty'][diff]
            if stats['total'] > 0:
                rate = (stats['tutoring_enabled'] / stats['total']) * 100
                print(f"  Level {diff}: {stats['tutoring_enabled']:3d}/{stats['total']:3d} ({rate:5.1f}%)")

        print(f"\nTutoring mode by source:")
        for source, stats in sorted(self.results['by_source'].items()):
            if stats['total'] > 0:
                rate = (stats['tutoring_enabled'] / stats['total']) * 100
                print(f"  {source:25s}: {stats['tutoring_enabled']:3d}/{stats['total']:3d} ({rate:5.1f}%)")

    def save_results(self, output_file='test_results/comprehensive_tutoring_test_results.json'):
        """Save results to JSON."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert defaultdict to regular dict for JSON
        results_serializable = {
            'total_tested': self.results['total_tested'],
            'tutoring_mode_rate': self.results['tutoring_mode_rate'],
            'intent_distribution': dict(self.results['intent_distribution']),
            'by_difficulty': {k: dict(v) for k, v in self.results['by_difficulty'].items()},
            'by_source': {k: dict(v) for k, v in self.results['by_source'].items()},
            'by_category': {k: dict(v) for k, v in self.results['by_category'].items()},
        }

        with open(output_path, 'w') as f:
            json.dump(results_serializable, f, indent=2)

        print(f"\n✓ Results saved to {output_path}")


def main():
    """Run comprehensive tests."""
    print("=" * 70)
    print("COMPREHENSIVE TUTORING SYSTEM TESTS")
    print("=" * 70)

    tester = ComprehensiveTester()

    # Run tests
    print("\nRunning comprehensive test suite...")
    print("This may take a few minutes depending on test bank size...")

    # Test 1: Intent classification on all problems
    tester.test_intent_classification(sample_size=None)  # Test all

    # Test 2: Prompt generation quality on sample
    tester.test_prompt_generation(sample_size=10)

    # Test 3: Response validation
    tester.test_validation_on_responses(sample_size=20)

    # Summary
    tester.print_summary()

    # Save results
    tester.save_results()

    print("\n" + "=" * 70)
    print("TESTS COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    main()
