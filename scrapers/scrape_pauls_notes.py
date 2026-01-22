#!/usr/bin/env python3
"""
Paul's Online Math Notes - Integration Problems Scraper

Scrapes integration practice problems from Paul Dawkins' excellent free resource.
One of the cleanest, most well-organized calculus problem sources online.

Sections:
- Indefinite Integrals
- Computing Definite Integrals
- Substitution Rule (Indefinite)
- Substitution Rule (Definite)
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from pathlib import Path
import time


class PaulsNotesScraper:
    """Scraper for Paul's Online Math Notes."""

    BASE_URL = "https://tutorial.math.lamar.edu"

    SECTIONS = {
        'indefinite_integrals': {
            'url': '/Problems/CalcI/IndefiniteIntegrals.aspx',
            'title': 'Indefinite Integrals',
            'difficulty_range': (2, 4),
        },
        'definite_integrals': {
            'url': '/Problems/CalcI/ComputingDefiniteIntegrals.aspx',
            'title': 'Computing Definite Integrals',
            'difficulty_range': (2, 4),
        },
        'substitution_indefinite': {
            'url': '/Problems/CalcI/SubstitutionRuleIndefinite.aspx',
            'title': 'Substitution Rule (Indefinite)',
            'difficulty_range': (3, 5),
        },
        'substitution_definite': {
            'url': '/Problems/CalcI/SubstitutionRuleDefinite.aspx',
            'title': 'Substitution Rule (Definite)',
            'difficulty_range': (3, 5),
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

    def scrape_section(self, section_key):
        """Scrape a specific section."""
        section_info = self.SECTIONS[section_key]
        url = self.BASE_URL + section_info['url']

        print(f"\n{'='*60}")
        print(f"Scraping: {section_info['title']}")
        print(f"URL: {url}")
        print('='*60)

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            problems = []

            # Paul's uses <ol class="practice-problems"> with <li> for each problem
            problem_lists = soup.find_all('ol', class_='practice-problems')

            print(f"Found {len(problem_lists)} problem lists")

            problem_num = 0
            for problem_list in problem_lists:
                # Each <li> is a problem (but skip nested <ol> for multi-part)
                list_items = problem_list.find_all('li', recursive=False)

                for li in list_items:
                    problem_num += 1
                    problem_data = self._extract_problem(li, section_key, problem_num)
                    if problem_data:
                        problems.append(problem_data)

            print(f"✓ Extracted {len(problems)} problems from {section_key}")
            return problems

        except Exception as e:
            print(f"✗ Error scraping {section_key}: {e}")
            return []

    def _extract_problem(self, li_element, section_key, problem_num):
        """Extract problem from <li> element."""
        try:
            section_info = self.SECTIONS[section_key]

            # Clone the li to avoid modifying original
            li = li_element

            # Check if this is a multi-part problem
            parts_list = li.find('ol', class_='example_parts_list')

            # Get problem text (remove solution link first)
            solution_link = li.find('a', class_='practice-soln-link')
            solution_url = None
            if solution_link:
                solution_url = solution_link.get('href')
                solution_link.decompose()  # Remove from tree

            # For multi-part problems, get the intro text + parts
            if parts_list:
                # Get intro text
                intro_text = li.get_text(separator=' ', strip=True).split('\n')[0]

                # Get each part
                part_items = parts_list.find_all('li')
                parts = [self._clean_text(part.get_text()) for part in part_items]

                problem_text = intro_text + ' ' + ' '.join(f'({chr(97+i)}) {part}' for i, part in enumerate(parts))
            else:
                # Single problem - just get all text
                problem_text = self._clean_text(li.get_text())

            if not problem_text or len(problem_text) < 10:
                return None

            # Estimate difficulty
            min_diff, max_diff = section_info['difficulty_range']
            difficulty = self._estimate_difficulty(problem_text, section_key, min_diff, max_diff)

            return {
                'id': f'pauls_{section_key}_{problem_num}',
                'section': section_key,
                'section_title': section_info['title'],
                'problem': problem_text,
                'solution': None,  # Solutions are on separate pages
                'answer': None,  # Would need to fetch solution page
                'difficulty': difficulty,
                'source': "Paul's Online Math Notes",
                'url': self.BASE_URL + section_info['url']
            }

        except Exception as e:
            print(f"  Warning: Error extracting problem {problem_num}: {e}")
            return None

    def _clean_text(self, text):
        """Clean extracted text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove "Show Solution" / "Hide Solution"
        text = re.sub(r'(Show|Hide)\s+Solution', '', text)
        # Remove "Solution" header
        text = re.sub(r'^Solution\s*:?\s*', '', text, flags=re.IGNORECASE)
        return text.strip()

    def _extract_answer(self, solution_text):
        """Extract final answer from solution."""
        if not solution_text:
            return None

        # Paul's often ends with "Answer:" or puts answer after equals
        patterns = [
            r'Answer\s*:?\s*(.+?)(?:\.|$)',
            r'=\s*([^=]+?)\s*(?:\+\s*[cC]|\.|$)',  # Captures before +C
            r'Therefore,?\s+(.+?)(?:\.|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, solution_text, re.IGNORECASE)
            if match:
                answer = match.group(1).strip()
                # Limit length (avoid grabbing whole explanation)
                if len(answer) < 80:
                    return answer

        return None

    def _estimate_difficulty(self, problem_text, section_key, min_diff, max_diff):
        """Estimate difficulty."""
        difficulty = min_diff

        # Complexity indicators
        if re.search(r'sin\^\d+|cos\^\d+|tan\^\d+', problem_text):
            difficulty += 1
        if re.search(r'ln|log', problem_text):
            difficulty += 1
        if re.search(r'e\^', problem_text):
            difficulty += 1
        if 'sqrt' in problem_text or '√' in problem_text:
            difficulty += 1
        if len(problem_text) > 50:  # Longer problems often harder
            difficulty += 1

        return min(difficulty, max_diff)

    def scrape_all_sections(self):
        """Scrape all available sections."""
        all_problems = []

        for section_key in self.SECTIONS.keys():
            problems = self.scrape_section(section_key)
            all_problems.extend(problems)

            # Be polite
            time.sleep(2)

        return all_problems

    def save_problems(self, problems, filename='pauls_notes_integration_problems.json'):
        """Save to JSON."""
        output_path = self.output_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(problems, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Saved {len(problems)} problems to {output_path}")

        # Summary
        self._save_summary(problems)

        return output_path

    def _save_summary(self, problems):
        """Save summary stats."""
        summary = {
            'total_problems': len(problems),
            'by_section': {},
            'by_difficulty': {},
            'with_solutions': sum(1 for p in problems if p['solution']),
            'with_answers': sum(1 for p in problems if p['answer']),
        }

        for problem in problems:
            section = problem['section']
            summary['by_section'][section] = summary['by_section'].get(section, 0) + 1

            diff = problem['difficulty']
            summary['by_difficulty'][diff] = summary['by_difficulty'].get(diff, 0) + 1

        summary_path = self.output_dir / 'pauls_notes_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\nSummary:")
        print(f"  Total problems: {summary['total_problems']}")
        print(f"  With solutions: {summary['with_solutions']}")
        print(f"  With answers: {summary['with_answers']}")
        print(f"\nBy section:")
        for section, count in sorted(summary['by_section'].items()):
            section_title = self.SECTIONS[section]['title']
            print(f"  {section:25s} ({section_title[:30]:30s}): {count:3d} problems")


def main():
    """Main entry point."""
    print("=" * 70)
    print("PAUL'S ONLINE MATH NOTES - INTEGRATION PROBLEMS SCRAPER")
    print("=" * 70)
    print("\nPaul Dawkins' notes are free educational resources")
    print("Source: https://tutorial.math.lamar.edu/")
    print("=" * 70)

    scraper = PaulsNotesScraper()

    # Scrape all sections
    print("\nScraping all integration sections...")
    problems = scraper.scrape_all_sections()

    # Save
    scraper.save_problems(problems)

    print("\n" + "=" * 70)
    print("SCRAPING COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    main()
