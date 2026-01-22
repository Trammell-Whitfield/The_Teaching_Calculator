#!/usr/bin/env python3
"""
Build Comprehensive Integration Test Bank

Combines:
1. Original 78 curated problems (test_data/calc1_integration_testbank.py)
2. OpenStax scraped problems
3. Paul's Notes scraped problems

Creates unified test bank with deduplication and categorization.
"""

import sys
import json
import re
from pathlib import Path
import hashlib

# Add to path
sys.path.insert(0, str(Path(__file__).parent / 'test_data'))

from calc1_integration_testbank import CALC1_INTEGRATION_PROBLEMS


class TestBankBuilder:
    """Builds comprehensive test bank from multiple sources."""

    def __init__(self):
        self.problems = []
        self.seen_hashes = set()  # For deduplication

    def add_curated_problems(self):
        """Add the original 78 curated problems."""
        print("\n" + "=" * 70)
        print("ADDING CURATED PROBLEMS")
        print("=" * 70)

        count = 0
        for category, problems in CALC1_INTEGRATION_PROBLEMS.items():
            for problem, answer, difficulty in problems:
                problem_data = {
                    'id': f'curated_{count}',
                    'problem': problem,
                    'answer': answer,
                    'difficulty': difficulty,
                    'category': category,
                    'source': 'Hand-curated',
                    'has_solution': False,  # Curated only have answers
                }

                if self._add_if_unique(problem_data):
                    count += 1

        print(f"✓ Added {count} curated problems")
        return count

    def add_scraped_problems(self, filename, source_name):
        """Add problems from scraped JSON file."""
        filepath = Path('test_data/scraped') / filename

        if not filepath.exists():
            print(f"⚠️  File not found: {filepath}")
            print(f"   Run scraper first to generate this file")
            return 0

        print(f"\n{'=' * 70}")
        print(f"ADDING {source_name} PROBLEMS")
        print(f"{'=' * 70}")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                scraped_data = json.load(f)

            count = 0
            for problem_data in scraped_data:
                # Standardize format
                standardized = {
                    'id': problem_data.get('id', f'{source_name.lower()}_{count}'),
                    'problem': problem_data.get('problem', ''),
                    'answer': problem_data.get('answer'),
                    'difficulty': problem_data.get('difficulty', 3),
                    'category': self._categorize_problem(problem_data.get('problem', '')),
                    'source': source_name,
                    'section': problem_data.get('section'),
                    'section_title': problem_data.get('section_title'),
                    'has_solution': problem_data.get('solution') is not None,
                    'url': problem_data.get('url'),
                }

                if self._add_if_unique(standardized):
                    count += 1

            print(f"✓ Added {count} problems from {source_name}")
            return count

        except Exception as e:
            print(f"✗ Error loading {source_name}: {e}")
            return 0

    def _add_if_unique(self, problem_data):
        """Add problem only if not duplicate."""
        # Create hash of problem text to detect duplicates
        problem_text = problem_data['problem'].lower()
        problem_hash = hashlib.md5(problem_text.encode()).hexdigest()

        if problem_hash in self.seen_hashes:
            return False  # Duplicate

        self.seen_hashes.add(problem_hash)
        self.problems.append(problem_data)
        return True

    def _categorize_problem(self, problem_text):
        """Categorize problem based on text content."""
        text_lower = problem_text.lower()

        # Simple keyword-based categorization
        if any(word in text_lower for word in ['substitution', 'u-sub']):
            return 'u_substitution'
        elif any(word in text_lower for word in ['by parts', 'integration by parts']):
            return 'integration_by_parts'
        elif re.match(r'.*sin.*\^.*|.*cos.*\^.*', text_lower):
            return 'trig_integrals'
        elif 'definite' in text_lower or re.search(r'from.*to', text_lower):
            return 'definite_integrals'
        elif any(word in text_lower for word in ['ln', 'log', 'exponential']):
            return 'exponential_logarithmic'
        elif 'partial fraction' in text_lower:
            return 'partial_fractions'
        else:
            return 'general_integration'

    def save_testbank(self, output_file='test_data/comprehensive_integration_testbank.json'):
        """Save comprehensive test bank."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.problems, f, indent=2, ensure_ascii=False)

        print(f"\n{'=' * 70}")
        print(f"SAVED COMPREHENSIVE TEST BANK")
        print(f"{'=' * 70}")
        print(f"File: {output_path}")
        print(f"Total problems: {len(self.problems)}")

        # Save summary
        self._save_summary(output_path.parent / 'testbank_summary.json')

    def _save_summary(self, summary_path):
        """Generate and save summary statistics."""
        summary = {
            'total_problems': len(self.problems),
            'by_source': {},
            'by_difficulty': {},
            'by_category': {},
            'with_answers': sum(1 for p in self.problems if p.get('answer')),
            'with_solutions': sum(1 for p in self.problems if p.get('has_solution')),
        }

        for problem in self.problems:
            # By source
            source = problem.get('source', 'Unknown')
            summary['by_source'][source] = summary['by_source'].get(source, 0) + 1

            # By difficulty
            diff = problem.get('difficulty', 3)
            summary['by_difficulty'][diff] = summary['by_difficulty'].get(diff, 0) + 1

            # By category
            category = problem.get('category', 'uncategorized')
            summary['by_category'][category] = summary['by_category'].get(category, 0) + 1

        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\nSummary Statistics:")
        print(f"  Total problems: {summary['total_problems']}")
        print(f"  With answers: {summary['with_answers']}")
        print(f"  With full solutions: {summary['with_solutions']}")

        print(f"\nBy source:")
        for source, count in sorted(summary['by_source'].items(), key=lambda x: -x[1]):
            print(f"  {source:25s}: {count:4d} problems")

        print(f"\nBy difficulty:")
        for diff in sorted(summary['by_difficulty'].keys()):
            count = summary['by_difficulty'][diff]
            bar = '█' * (count // 10)
            print(f"  Level {diff}: {count:4d} {bar}")

        print(f"\nBy category:")
        for category, count in sorted(summary['by_category'].items(), key=lambda x: -x[1]):
            print(f"  {category:30s}: {count:4d} problems")

    def get_sample_problems(self, n=5):
        """Get sample problems from test bank."""
        import random
        return random.sample(self.problems, min(n, len(self.problems)))


def main():
    """Build comprehensive test bank."""
    import re

    print("=" * 70)
    print("COMPREHENSIVE INTEGRATION TEST BANK BUILDER")
    print("=" * 70)
    print("\nCombines problems from multiple sources:")
    print("  1. Hand-curated problems (78 problems)")
    print("  2. OpenStax Calculus (if scraped)")
    print("  3. Paul's Online Math Notes (if scraped)")
    print("=" * 70)

    builder = TestBankBuilder()

    # Add curated problems
    curated_count = builder.add_curated_problems()

    # Try to add scraped problems
    openstax_count = builder.add_scraped_problems(
        'openstax_integration_problems.json',
        'OpenStax Calculus'
    )

    pauls_count = builder.add_scraped_problems(
        'pauls_notes_integration_problems.json',
        "Paul's Online Notes"
    )

    # Save combined test bank
    builder.save_testbank()

    # Show some samples
    print(f"\n{'=' * 70}")
    print("SAMPLE PROBLEMS FROM TEST BANK")
    print('=' * 70)

    samples = builder.get_sample_problems(n=5)
    for i, problem in enumerate(samples, 1):
        print(f"\nSample {i}:")
        print(f"  Source: {problem['source']}")
        print(f"  Difficulty: {problem['difficulty']}")
        print(f"  Problem: {problem['problem'][:80]}...")
        if problem.get('answer'):
            print(f"  Answer: {problem['answer']}")

    print(f"\n{'=' * 70}")
    print("TEST BANK BUILD COMPLETE")
    print('=' * 70)

    total = curated_count + openstax_count + pauls_count
    print(f"\nTotal problems in comprehensive test bank: {total}")

    if openstax_count == 0:
        print(f"\n💡 TIP: Run scrapers to add more problems:")
        print(f"   python scrapers/scrape_openstax_integration.py")
        print(f"   python scrapers/scrape_pauls_notes.py")


if __name__ == '__main__':
    main()
