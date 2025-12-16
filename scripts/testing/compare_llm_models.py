#!/usr/bin/env python3
"""
Comprehensive LLM Model Comparison Tool
Compares Qwen2.5-Math-7B vs DeepSeek-Math-7B on mathematical reasoning

Usage:
    python compare_llm_models.py \
        --model1 models/quantized/qwen2.5-math-7b-instruct-q4km.gguf \
        --model2 models/quantized/deepseek-math-7b-q4km.gguf \
        --test-cases data/test-cases/llm-comparison-problems.yaml \
        --limit 5
"""

import subprocess
import time
import psutil
import json
import yaml
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
import argparse
from datetime import datetime


class ModelComparator:
    """Systematic comparison of two LLM models on math tasks."""

    def __init__(self, model1_path: str, model2_path: str, test_cases_path: str):
        self.model1_path = Path(model1_path)
        self.model2_path = Path(model2_path)

        if not self.model1_path.exists():
            raise FileNotFoundError(f"Model 1 not found: {model1_path}")
        if not self.model2_path.exists():
            raise FileNotFoundError(f"Model 2 not found: {model2_path}")

        self.test_cases = self._load_test_cases(test_cases_path)

        # Find llama-cli
        self.llama_cli = Path(__file__).parent.parent.parent / 'llama.cpp' / 'build' / 'bin' / 'llama-cli'
        if not self.llama_cli.exists():
            raise FileNotFoundError(f"llama-cli not found at {self.llama_cli}")

        self.results = {
            'model1': {
                'name': self.model1_path.name,
                'path': str(self.model1_path),
                'tests': []
            },
            'model2': {
                'name': self.model2_path.name,
                'path': str(self.model2_path),
                'tests': []
            },
            'metadata': {
                'start_time': datetime.now().isoformat(),
                'test_cases_file': test_cases_path
            }
        }

    def _load_test_cases(self, path: str) -> Dict:
        """Load YAML test cases."""
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def _get_cpu_temp(self) -> float:
        """Get CPU temperature (platform-specific)."""
        try:
            # macOS using powermetrics (requires sudo)
            # Placeholder - actual implementation depends on platform
            return 0.0
        except:
            return 0.0

    def _run_inference(self, model_path: Path, prompt: str, max_tokens: int = 512) -> Dict[str, Any]:
        """Run inference and collect comprehensive metrics."""

        # Start monitoring
        start_time = time.time()
        process = psutil.Process()
        start_mem = process.memory_info().rss / 1024**2  # MB

        # Build command
        cmd = [
            str(self.llama_cli),
            '-m', str(model_path),
            '-p', prompt,
            '-n', str(max_tokens),
            '-t', '4',  # 4 threads for optimal Pi 5 performance
            '-c', '2048',  # Context window
            '--temp', '0.1',  # Low temperature for deterministic math
            '--repeat-penalty', '1.1',
            '--log-disable'  # Disable llama.cpp logging
        ]

        # Run inference
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )

            output = result.stdout
            success = result.returncode == 0

        except subprocess.TimeoutExpired:
            output = "[TIMEOUT after 120s]"
            success = False
        except Exception as e:
            output = f"[ERROR: {str(e)}]"
            success = False

        # Capture metrics
        end_time = time.time()
        end_mem = process.memory_info().rss / 1024**2  # MB

        elapsed = end_time - start_time
        tokens = self._count_tokens(output)
        tps = tokens / elapsed if elapsed > 0 else 0

        return {
            'output': output,
            'success': success,
            'time_seconds': round(elapsed, 2),
            'tokens_generated': tokens,
            'tokens_per_second': round(tps, 2),
            'memory_mb': round(end_mem - start_mem, 2),
            'timestamp': datetime.now().isoformat()
        }

    def _count_tokens(self, text: str) -> int:
        """Rough token count estimation (words as proxy)."""
        if not text or text.startswith('['):
            return 0
        return len(text.split())

    def _format_prompt(self, problem: str) -> str:
        """Format problem into structured prompt for math LLMs."""
        return f"""You are a mathematical problem solver. Solve the following problem step by step. Show your work clearly.

Problem: {problem}

Solution:
1."""

    def compare_on_problem(self, problem: str, category: str, expected: str, difficulty: str):
        """Run both models on a single problem."""

        prompt = self._format_prompt(problem)

        print(f"\n{'='*70}")
        print(f"Problem ({category}, {difficulty}):")
        print(f"  {problem}")
        print(f"Expected: {expected}")
        print(f"{'='*70}")

        # Test Model 1
        print(f"\n→ Testing {self.model1_path.name}...")
        result1 = self._run_inference(self.model1_path, prompt)
        result1.update({
            'problem': problem,
            'category': category,
            'expected': expected,
            'difficulty': difficulty
        })
        self.results['model1']['tests'].append(result1)

        if result1['success']:
            print(f"  ✓ Time: {result1['time_seconds']}s | TPS: {result1['tokens_per_second']}")
            print(f"  Output: {result1['output'][:150].strip()}...")
        else:
            print(f"  ✗ {result1['output']}")

        # Cool down
        time.sleep(2)

        # Test Model 2
        print(f"\n→ Testing {self.model2_path.name}...")
        result2 = self._run_inference(self.model2_path, prompt)
        result2.update({
            'problem': problem,
            'category': category,
            'expected': expected,
            'difficulty': difficulty
        })
        self.results['model2']['tests'].append(result2)

        if result2['success']:
            print(f"  ✓ Time: {result2['time_seconds']}s | TPS: {result2['tokens_per_second']}")
            print(f"  Output: {result2['output'][:150].strip()}...")
        else:
            print(f"  ✗ {result2['output']}")

        # Cool down
        time.sleep(2)

    def run_full_comparison(self, limit_per_category: int = None):
        """Run comparison on all test cases."""

        for category_name, problems in self.test_cases.items():
            print(f"\n\n{'#'*70}")
            print(f"# Category: {category_name.upper().replace('_', ' ')}")
            print(f"{'#'*70}")

            count = 0
            for problem_data in problems:
                if limit_per_category and count >= limit_per_category:
                    print(f"\n[Limit reached: {limit_per_category} problems per category]")
                    break

                self.compare_on_problem(
                    problem=problem_data['problem'],
                    category=problem_data['category'],
                    expected=problem_data['expected_answer'],
                    difficulty=problem_data['difficulty']
                )

                count += 1

        # Mark completion time
        self.results['metadata']['end_time'] = datetime.now().isoformat()

    def _calculate_stats(self, tests: List[Dict]) -> Dict:
        """Calculate aggregate statistics."""
        if not tests:
            return {
                'total_tests': 0,
                'successful': 0,
                'failed': 0
            }

        successful_tests = [t for t in tests if t['success']]

        return {
            'total_tests': len(tests),
            'successful': len(successful_tests),
            'failed': len(tests) - len(successful_tests),
            'success_rate': round(len(successful_tests) / len(tests) * 100, 2) if tests else 0,
            'avg_time': round(sum(t['time_seconds'] for t in successful_tests) / len(successful_tests), 2) if successful_tests else 0,
            'avg_tps': round(sum(t['tokens_per_second'] for t in successful_tests) / len(successful_tests), 2) if successful_tests else 0,
            'avg_memory_mb': round(sum(t['memory_mb'] for t in successful_tests) / len(successful_tests), 2) if successful_tests else 0,
            'total_tokens': sum(t['tokens_generated'] for t in successful_tests),
            'total_time': round(sum(t['time_seconds'] for t in tests), 2)
        }

    def _generate_recommendation(self, stats1: Dict, stats2: Dict) -> str:
        """Generate model recommendation based on performance."""

        # Check if either model failed too much
        if stats1['success_rate'] < 50 and stats2['success_rate'] < 50:
            return "⚠️  Both models show poor success rates. Consider higher quantization (Q5_K_M or Q6_K)."

        if stats1['success_rate'] < 50:
            return f"Recommend Model 2 ({self.model2_path.name}): Model 1 has poor success rate ({stats1['success_rate']}%)"

        if stats2['success_rate'] < 50:
            return f"Recommend Model 1 ({self.model1_path.name}): Model 2 has poor success rate ({stats2['success_rate']}%)"

        # Both models work well - compare performance
        if stats1['avg_tps'] > stats2['avg_tps'] * 1.15:
            return f"Recommend Model 1 ({self.model1_path.name}): 15%+ faster ({stats1['avg_tps']} vs {stats2['avg_tps']} TPS)"

        if stats2['avg_tps'] > stats1['avg_tps'] * 1.15:
            return f"Recommend Model 2 ({self.model2_path.name}): 15%+ faster ({stats2['avg_tps']} vs {stats1['avg_tps']} TPS)"

        # Similar performance - prefer newer model (Qwen2.5)
        if 'qwen' in self.model1_path.name.lower():
            return f"Recommend Model 1 ({self.model1_path.name}): Newer architecture, comparable performance"
        elif 'qwen' in self.model2_path.name.lower():
            return f"Recommend Model 2 ({self.model2_path.name}): Newer architecture, comparable performance"

        return "Models show similar performance. Choose based on other factors (size, availability)."

    def generate_report(self, output_path: str = 'model_comparison_report.json'):
        """Generate comprehensive comparison report."""

        # Calculate aggregate metrics
        model1_stats = self._calculate_stats(self.results['model1']['tests'])
        model2_stats = self._calculate_stats(self.results['model2']['tests'])

        # Calculate by-category stats
        model1_by_category = self._stats_by_category(self.results['model1']['tests'])
        model2_by_category = self._stats_by_category(self.results['model2']['tests'])

        report = {
            'metadata': self.results['metadata'],
            'model1': {
                'name': self.model1_path.name,
                'path': str(self.model1_path),
                'overall_stats': model1_stats,
                'by_category': model1_by_category,
                'tests': self.results['model1']['tests']
            },
            'model2': {
                'name': self.model2_path.name,
                'path': str(self.model2_path),
                'overall_stats': model2_stats,
                'by_category': model2_by_category,
                'tests': self.results['model2']['tests']
            },
            'comparison': {
                'speed_ratio': round(model1_stats['avg_tps'] / model2_stats['avg_tps'], 2) if model2_stats['avg_tps'] > 0 else 0,
                'memory_diff_mb': round(model1_stats['avg_memory_mb'] - model2_stats['avg_memory_mb'], 2),
                'success_rate_diff': round(model1_stats['success_rate'] - model2_stats['success_rate'], 2),
                'recommendation': self._generate_recommendation(model1_stats, model2_stats)
            }
        }

        # Save report
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        # Print summary
        self._print_summary(report)

        return report

    def _stats_by_category(self, tests: List[Dict]) -> Dict:
        """Calculate statistics broken down by problem category."""
        categories = {}

        for test in tests:
            cat = test.get('category', 'unknown')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(test)

        return {
            cat: self._calculate_stats(tests)
            for cat, tests in categories.items()
        }

    def _print_summary(self, report: Dict):
        """Print formatted summary."""
        print("\n\n" + "="*70)
        print("MODEL COMPARISON SUMMARY")
        print("="*70)

        print(f"\n📊 MODEL 1: {report['model1']['name']}")
        print(f"    Path: {report['model1']['path']}")
        stats1 = report['model1']['overall_stats']
        print(f"    Tests: {stats1['total_tests']} | Success: {stats1['successful']} ({stats1['success_rate']}%)")
        print(f"    Avg Speed: {stats1['avg_tps']} tokens/sec")
        print(f"    Avg Time: {stats1['avg_time']}s per problem")
        print(f"    Avg Memory: {stats1['avg_memory_mb']} MB")

        print(f"\n📊 MODEL 2: {report['model2']['name']}")
        print(f"    Path: {report['model2']['path']}")
        stats2 = report['model2']['overall_stats']
        print(f"    Tests: {stats2['total_tests']} | Success: {stats2['successful']} ({stats2['success_rate']}%)")
        print(f"    Avg Speed: {stats2['avg_tps']} tokens/sec")
        print(f"    Avg Time: {stats2['avg_time']}s per problem")
        print(f"    Avg Memory: {stats2['avg_memory_mb']} MB")

        print(f"\n🏆 COMPARISON:")
        comp = report['comparison']
        print(f"    Speed ratio (M1/M2): {comp['speed_ratio']}x")
        print(f"    Memory diff: {comp['memory_diff_mb']} MB")
        print(f"    Success rate diff: {comp['success_rate_diff']}%")

        print(f"\n💡 RECOMMENDATION:")
        print(f"    {comp['recommendation']}")

        print("="*70)
        print(f"\n📄 Full report saved to: model_comparison_report.json")


def main():
    parser = argparse.ArgumentParser(
        description="Compare two LLM models on mathematical reasoning tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--model1', required=True, help='Path to first model (GGUF)')
    parser.add_argument('--model2', required=True, help='Path to second model (GGUF)')
    parser.add_argument('--test-cases', required=True, help='Path to test cases YAML file')
    parser.add_argument('--limit', type=int, help='Limit number of problems per category')
    parser.add_argument('--output', default='model_comparison_report.json', help='Output report path')

    args = parser.parse_args()

    print("="*70)
    print("LLM MODEL COMPARISON TOOL")
    print("="*70)
    print(f"Model 1: {args.model1}")
    print(f"Model 2: {args.model2}")
    print(f"Test Cases: {args.test_cases}")
    if args.limit:
        print(f"Limit: {args.limit} problems per category")
    print("="*70)

    try:
        # Run comparison
        comparator = ModelComparator(args.model1, args.model2, args.test_cases)
        comparator.run_full_comparison(limit_per_category=args.limit)
        comparator.generate_report(output_path=args.output)

        print(f"\n✓ Comparison complete!")
        return 0

    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
