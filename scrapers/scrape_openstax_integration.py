#!/usr/bin/env python3
"""
OpenStax Calculus Volume 1 - Integration Problems Scraper

Scrapes Chapter 5 (Integration) problems from OpenStax Calculus.
OpenStax is free/open source with permissive license.

Sections covered:
- 5.1: Approximating Areas
- 5.2: The Definite Integral
- 5.3: The Fundamental Theorem of Calculus
- 5.4: Integration Formulas and the Net Change Theorem
- 5.5: Substitution
- 5.6: Integrals Involving Exponential and Logarithmic Functions
- 5.7: Integrals Resulting in Inverse Trigonometric Functions
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from pathlib import Path


class OpenStaxScraper:
    """Scraper for OpenStax Calculus integration problems."""

    BASE_URL = "https://openstax.org/books/calculus-volume-1/pages"

    # Chapter 5 sections with integration problems
    INTEGRATION_SECTIONS = {
        '5.1': {
            'slug': '5-1-approximating-areas',
            'title': 'Approximating Areas',
            'difficulty_range': (2, 4),
        },
        '5.2': {
            'slug': '5-2-the-definite-integral',
            'title': 'The Definite Integral',
            'difficulty_range': (2, 5),
        },
        '5.3': {
            'slug': '5-3-the-fundamental-theorem-of-calculus',
            'title': 'The Fundamental Theorem of Calculus',
            'difficulty_range': (3, 6),
        },
        '5.4': {
            'slug': '5-4-integration-formulas-and-the-net-change-theorem',
            'title': 'Integration Formulas',
            'difficulty_range': (3, 5),
        },
        '5.5': {
            'slug': '5-5-substitution',
            'title': 'Substitution Rule',
            'difficulty_range': (3, 6),
        },
        '5.6': {
            'slug': '5-6-integrals-involving-exponential-and-logarithmic-functions',
            'title': 'Exponential and Logarithmic Integrals',
            'difficulty_range': (3, 5),
        },
        '5.7': {
            'slug': '5-7-integrals-resulting-in-inverse-trigonometric-functions',
            'title': 'Inverse Trig Integrals',
            'difficulty_range': (4, 6),
        },
    }

    def __init__(self, output_dir='test_data/scraped'):
        """Initialize scraper."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Educational Research Bot)'
        })

    def scrape_section(self, section_id):
        """
        Scrape all problems from a section.

        Args:
            section_id: Section ID like '5.5'

        Returns:
            List of problem dictionaries
        """
        section_info = self.INTEGRATION_SECTIONS[section_id]
        url = f"{self.BASE_URL}/{section_info['slug']}"

        print(f"\n{'='*60}")
        print(f"Scraping: {section_id} - {section_info['title']}")
        print(f"URL: {url}")
        print('='*60)

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            problems = []

            # OpenStax uses specific classes for exercises
            # Look for practice problems in the "Section Exercises" area
            exercise_divs = soup.find_all('div', class_='os-exercise')

            print(f"Found {len(exercise_divs)} exercise containers")

            for i, div in enumerate(exercise_divs, 1):
                problem_data = self._extract_problem(div, section_id, i)
                if problem_data:
                    problems.append(problem_data)

                    # Show progress
                    if i % 10 == 0:
                        print(f"  Processed {i}/{len(exercise_divs)} exercises...")

            print(f"✓ Extracted {len(problems)} problems from section {section_id}")
            return problems

        except Exception as e:
            print(f"✗ Error scraping section {section_id}: {e}")
            return []

    def _extract_problem(self, exercise_div, section_id, problem_num):
        """Extract problem data from exercise div."""
        try:
            # Find problem statement
            problem_container = exercise_div.find('div', class_='os-problem-container')
            if not problem_container:
                return None

            problem_text = self._clean_text(problem_container.get_text())

            # Try to find solution
            solution_container = exercise_div.find('div', class_='os-solution-container')
            solution_text = None
            if solution_container:
                solution_text = self._clean_text(solution_container.get_text())

            # Extract just the final answer if possible
            answer = self._extract_answer(solution_text) if solution_text else None

            # Estimate difficulty based on problem characteristics
            difficulty = self._estimate_difficulty(problem_text, section_id)

            return {
                'id': f'openstax_{section_id}_{problem_num}',
                'section': section_id,
                'section_title': self.INTEGRATION_SECTIONS[section_id]['title'],
                'problem': problem_text,
                'solution': solution_text,
                'answer': answer,
                'difficulty': difficulty,
                'source': 'OpenStax Calculus Volume 1',
                'url': f"{self.BASE_URL}/{self.INTEGRATION_SECTIONS[section_id]['slug']}"
            }

        except Exception as e:
            print(f"  Warning: Error extracting problem {problem_num}: {e}")
            return None

    def _clean_text(self, text):
        """Clean extracted text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove "Show Solution" buttons
        text = re.sub(r'Show Solution', '', text)
        # Remove problem numbers at start
        text = re.sub(r'^\d+\.\s*', '', text)
        return text.strip()

    def _extract_answer(self, solution_text):
        """Try to extract just the final answer from solution."""
        if not solution_text:
            return None

        # Look for common answer patterns
        patterns = [
            r'(?:answer|result|solution)(?:\s+is)?:?\s*(.+?)(?:\.|$)',
            r'=\s*([^=]+?)(?:\+\s*C|\.|$)',
            r'\\boxed\{([^}]+)\}',
        ]

        for pattern in patterns:
            match = re.search(pattern, solution_text, re.IGNORECASE)
            if match:
                answer = match.group(1).strip()
                # Limit length
                if len(answer) < 100:
                    return answer

        return None

    def _estimate_difficulty(self, problem_text, section_id):
        """Estimate problem difficulty based on content."""
        # Base difficulty from section
        min_diff, max_diff = self.INTEGRATION_SECTIONS[section_id]['difficulty_range']
        difficulty = min_diff

        # Increase based on complexity indicators
        if 'substitution' in problem_text.lower() or 'u-sub' in problem_text.lower():
            difficulty += 1
        if 'by parts' in problem_text.lower():
            difficulty += 2
        if any(word in problem_text.lower() for word in ['prove', 'show that', 'verify']):
            difficulty += 1
        if re.search(r'sin\^\d+|cos\^\d+', problem_text):  # Trig powers
            difficulty += 1
        if 'ln' in problem_text or 'log' in problem_text:
            difficulty += 1

        # Cap at section max
        return min(difficulty, max_diff)

    def scrape_all_sections(self):
        """Scrape all integration sections."""
        all_problems = []

        for section_id in self.INTEGRATION_SECTIONS.keys():
            problems = self.scrape_section(section_id)
            all_problems.extend(problems)

            # Be polite - don't hammer the server
            time.sleep(2)

        return all_problems

    def save_problems(self, problems, filename='openstax_integration_problems.json'):
        """Save problems to JSON file."""
        output_path = self.output_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(problems, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Saved {len(problems)} problems to {output_path}")

        # Also save summary
        self._save_summary(problems)

        return output_path

    def _save_summary(self, problems):
        """Save summary statistics."""
        summary = {
            'total_problems': len(problems),
            'by_section': {},
            'by_difficulty': {},
            'with_solutions': sum(1 for p in problems if p['solution']),
            'with_answers': sum(1 for p in problems if p['answer']),
        }

        # Count by section
        for problem in problems:
            section = problem['section']
            summary['by_section'][section] = summary['by_section'].get(section, 0) + 1

            # Count by difficulty
            diff = problem['difficulty']
            summary['by_difficulty'][diff] = summary['by_difficulty'].get(diff, 0) + 1

        summary_path = self.output_dir / 'openstax_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\nSummary:")
        print(f"  Total problems: {summary['total_problems']}")
        print(f"  With solutions: {summary['with_solutions']}")
        print(f"  With answers: {summary['with_answers']}")
        print(f"\nBy section:")
        for section, count in sorted(summary['by_section'].items()):
            section_title = self.INTEGRATION_SECTIONS[section]['title']
            print(f"  {section} ({section_title[:30]:30s}): {count:3d} problems")


def main():
    """Main scraper entry point."""
    print("=" * 70)
    print("OPENSTAX CALCULUS - INTEGRATION PROBLEMS SCRAPER")
    print("=" * 70)
    print("\nThis scraper extracts integration problems from OpenStax Calculus")
    print("OpenStax content is licensed under CC BY 4.0 (permissive)")
    print("Source: https://openstax.org/details/books/calculus-volume-1")
    print("=" * 70)

    scraper = OpenStaxScraper()

    # Option: scrape specific section for testing
    import sys
    if len(sys.argv) > 1:
        section_id = sys.argv[1]
        if section_id in scraper.INTEGRATION_SECTIONS:
            print(f"\nScraping single section: {section_id}")
            problems = scraper.scrape_section(section_id)
            scraper.save_problems(problems, f'openstax_{section_id}_problems.json')
        else:
            print(f"Unknown section: {section_id}")
            print(f"Available: {', '.join(scraper.INTEGRATION_SECTIONS.keys())}")
    else:
        # Scrape all sections
        print("\nScraping ALL integration sections...")
        problems = scraper.scrape_all_sections()

        # Save results
        scraper.save_problems(problems)

        print("\n" + "=" * 70)
        print("SCRAPING COMPLETE")
        print("=" * 70)


if __name__ == '__main__':
    main()
