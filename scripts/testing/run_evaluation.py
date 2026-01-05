#!/usr/bin/env python3
"""
Comprehensive Evaluation Runner for Teaching Calculator
Runs full evaluation pipeline: classifier + response quality + reporting.
"""

import sys
import argparse
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from testing.test_dataset import TestDataset, TestQuery
from testing.evaluation_metrics import ClassifierEvaluator, ResponseScorer, EvaluationReport
from cascade.calculator_engine import CalculatorEngine, MathQueryRouter


class EvaluationRunner:
    """Main evaluation orchestrator."""

    def __init__(self, enable_wolfram: bool = False, model_path: str = None,
                 enable_cache: bool = False):
        """
        Initialize the evaluation runner.

        Args:
            enable_wolfram: Enable Wolfram Alpha layer
            model_path: Path to LLM model
            enable_cache: Enable caching (usually disabled for evaluation)
        """
        self.logger = logging.getLogger(__name__)

        # Load dataset
        self.logger.info("Loading test dataset...")
        self.dataset = TestDataset()
        self.logger.info(f"✓ Loaded {len(self.dataset.get_all())} test queries")

        # Initialize calculator engine
        self.logger.info("Initializing calculator engine...")
        try:
            self.engine = CalculatorEngine(
                enable_wolfram=enable_wolfram,
                model_path=model_path,
                enable_cache=enable_cache
            )
            self.logger.info("✓ Engine initialized")
        except Exception as e:
            self.logger.error(f"✗ Failed to initialize engine: {e}")
            raise

        # Initialize evaluators
        self.classifier_eval = ClassifierEvaluator()
        self.response_scorer = ResponseScorer()
        self.report_generator = EvaluationReport()

        # Results storage
        self.results = {
            'query_results': [],
            'classifier_metrics': None,
            'response_metrics': None,
            'timing_metrics': None
        }

    def run_full_evaluation(self, sample_size: int = None,
                           output_dir: str = "./eval_results") -> Dict[str, Any]:
        """
        Run complete evaluation pipeline.

        Args:
            sample_size: Number of queries to evaluate (None = all)
            output_dir: Directory to save results

        Returns:
            Dictionary with all evaluation results
        """
        print("\n" + "="*70)
        print("TEACHING CALCULATOR - COMPREHENSIVE EVALUATION")
        print("="*70)

        # Get queries to evaluate
        queries = self.dataset.get_all()
        if sample_size:
            queries = queries[:sample_size]

        print(f"\nEvaluating {len(queries)} queries...")
        print(f"Output directory: {output_dir}\n")

        # Phase 1: Run all queries through the system
        print("Phase 1: Running queries through system...")
        query_results = self._evaluate_queries(queries)

        # Phase 2: Evaluate classifier performance
        print("\nPhase 2: Evaluating classifier performance...")
        classifier_metrics = self._evaluate_classifier(query_results)

        # Phase 3: Evaluate response quality
        print("\nPhase 3: Evaluating response quality...")
        response_metrics = self._evaluate_responses(query_results)

        # Phase 4: Analyze timing
        print("\nPhase 4: Analyzing performance metrics...")
        timing_metrics = self._analyze_timing(query_results)

        # Compile results
        self.results = {
            'query_results': query_results,
            'classifier_metrics': classifier_metrics,
            'response_metrics': response_metrics,
            'timing_metrics': timing_metrics,
            'dataset_stats': self.dataset.get_statistics()
        }

        # Phase 5: Generate reports
        print("\nPhase 5: Generating evaluation reports...")
        self._generate_reports(output_dir)

        print("\n" + "="*70)
        print("EVALUATION COMPLETE")
        print("="*70)

        return self.results

    def _evaluate_queries(self, queries: List[TestQuery]) -> List[Dict[str, Any]]:
        """
        Run all queries through the calculator engine.

        Args:
            queries: List of test queries

        Returns:
            List of result dictionaries
        """
        results = []
        total = len(queries)

        for i, test_query in enumerate(queries, 1):
            # Progress indicator
            if i % 10 == 0:
                print(f"  Progress: {i}/{total} ({i/total*100:.1f}%)")

            # Run query
            start_time = time.time()
            try:
                result = self.engine.solve(test_query.query)
                elapsed = time.time() - start_time

                # Record result
                results.append({
                    'query': test_query.query,
                    'expected_tier': test_query.tier,
                    'predicted_tier': result['source'],
                    'expected_output': test_query.expected_output,
                    'actual_output': result.get('result', ''),
                    'category': test_query.category,
                    'difficulty': test_query.difficulty,
                    'success': result['success'],
                    'response_time': elapsed,
                    'cascade_path': result.get('cascade_path', []),
                    'error': result.get('error', None)
                })

            except Exception as e:
                self.logger.error(f"Error evaluating query '{test_query.query}': {e}")
                results.append({
                    'query': test_query.query,
                    'expected_tier': test_query.tier,
                    'predicted_tier': 'error',
                    'expected_output': test_query.expected_output,
                    'actual_output': '',
                    'category': test_query.category,
                    'difficulty': test_query.difficulty,
                    'success': False,
                    'response_time': 0,
                    'cascade_path': [],
                    'error': str(e)
                })

        print(f"  Completed: {total}/{total} (100.0%)")
        return results

    def _evaluate_classifier(self, query_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate classifier/router performance.

        Args:
            query_results: Results from query evaluation

        Returns:
            Classifier metrics dictionary
        """
        # Filter out 'decline' tier for now (system might not implement it yet)
        # and filter out errors
        valid_results = [
            r for r in query_results
            if r['predicted_tier'] != 'error' and r['predicted_tier'] != 'none'
        ]

        if not valid_results:
            return {'error': 'No valid results to evaluate'}

        # Extract labels
        y_true = [r['expected_tier'] for r in valid_results]
        y_pred = [r['predicted_tier'] for r in valid_results]

        # Evaluate
        metrics = self.classifier_eval.evaluate(y_true, y_pred)

        # Print metrics
        self.classifier_eval.print_metrics(metrics)

        # Analyze misclassifications
        queries = [r['query'] for r in valid_results]
        misclass = self.classifier_eval.analyze_misclassifications(y_true, y_pred, queries)

        if misclass:
            print("\nTop Misclassification Patterns:")
            for pattern, examples in sorted(misclass.items(),
                                           key=lambda x: len(x[1]), reverse=True)[:5]:
                print(f"  {pattern}: {len(examples)} cases")
                if examples:
                    print(f"    Example: \"{examples[0]['query'][:60]}...\"")

        metrics['misclassifications'] = {
            pattern: len(examples) for pattern, examples in misclass.items()
        }

        return metrics

    def _evaluate_responses(self, query_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate response quality by tier.

        Args:
            query_results: Results from query evaluation

        Returns:
            Response metrics by tier
        """
        metrics_by_tier = {}

        # Group by tier
        for tier in ['sympy', 'wolfram', 'llm']:
            tier_results = [r for r in query_results if r['expected_tier'] == tier]

            if not tier_results:
                continue

            scores = []
            score_details = []

            for result in tier_results:
                if not result['success']:
                    scores.append(0)
                    score_details.append({
                        'query': result['query'],
                        'score': 0,
                        'reason': 'Failed to solve'
                    })
                    continue

                # Score based on tier type
                if tier in ['sympy', 'wolfram']:
                    # Computational scoring (0 or 1)
                    score, reason = self.response_scorer.score_computational(
                        result['actual_output'],
                        result['expected_output']
                    )
                    scores.append(score)
                    score_details.append({
                        'query': result['query'],
                        'score': score,
                        'reason': reason,
                        'expected': result['expected_output'],
                        'actual': result['actual_output'][:100]
                    })

                elif tier == 'llm':
                    # Explanatory scoring (0-3)
                    score, reason = self.response_scorer.score_explanatory(
                        result['actual_output']
                    )
                    # Normalize to 0-1 for comparison
                    normalized_score = score / 3.0
                    scores.append(normalized_score)
                    score_details.append({
                        'query': result['query'],
                        'score': score,
                        'normalized_score': normalized_score,
                        'reason': reason,
                        'response_length': len(result['actual_output'])
                    })

            # Calculate metrics
            if scores:
                accuracy = sum(s >= 0.5 for s in scores) / len(scores)  # 50% threshold
                avg_score = sum(scores) / len(scores)

                metrics_by_tier[tier] = {
                    'total_queries': len(tier_results),
                    'successful_queries': sum(1 for r in tier_results if r['success']),
                    'accuracy': accuracy,
                    'avg_score': avg_score,
                    'score_distribution': {
                        'excellent': sum(1 for s in scores if s >= 0.9),
                        'good': sum(1 for s in scores if 0.7 <= s < 0.9),
                        'fair': sum(1 for s in scores if 0.5 <= s < 0.7),
                        'poor': sum(1 for s in scores if s < 0.5)
                    },
                    'sample_scores': score_details[:5]  # Store first 5 for reporting
                }

                print(f"\n{tier.upper()} Response Quality:")
                print(f"  Total queries: {len(tier_results)}")
                print(f"  Successful: {metrics_by_tier[tier]['successful_queries']}")
                print(f"  Accuracy: {accuracy:.3f}")
                print(f"  Average score: {avg_score:.3f}")

        return metrics_by_tier

    def _analyze_timing(self, query_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze response time metrics.

        Args:
            query_results: Results from query evaluation

        Returns:
            Timing metrics dictionary
        """
        # Overall timing
        all_times = [r['response_time'] for r in query_results if r['response_time'] > 0]

        timing_metrics = {
            'overall': {
                'total_queries': len(query_results),
                'avg_time': sum(all_times) / len(all_times) if all_times else 0,
                'min_time': min(all_times) if all_times else 0,
                'max_time': max(all_times) if all_times else 0,
                'median_time': sorted(all_times)[len(all_times)//2] if all_times else 0
            }
        }

        # Timing by tier
        for tier in ['sympy', 'wolfram', 'llm']:
            tier_times = [
                r['response_time'] for r in query_results
                if r['predicted_tier'] == tier and r['response_time'] > 0
            ]

            if tier_times:
                timing_metrics[tier] = {
                    'count': len(tier_times),
                    'avg_time': sum(tier_times) / len(tier_times),
                    'min_time': min(tier_times),
                    'max_time': max(tier_times)
                }

        # Print timing summary
        print("\nTiming Analysis:")
        print(f"  Overall average: {timing_metrics['overall']['avg_time']:.2f}s")
        print(f"  Median: {timing_metrics['overall']['median_time']:.2f}s")
        print(f"  Range: {timing_metrics['overall']['min_time']:.2f}s - "
              f"{timing_metrics['overall']['max_time']:.2f}s")

        for tier in ['sympy', 'wolfram', 'llm']:
            if tier in timing_metrics:
                print(f"  {tier.upper()} avg: {timing_metrics[tier]['avg_time']:.2f}s")

        return timing_metrics

    def _generate_reports(self, output_dir: str):
        """
        Generate all evaluation reports.

        Args:
            output_dir: Directory to save reports
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate comprehensive report
        self.report_generator.generate_report(
            self.results['classifier_metrics'],
            self.results['response_metrics'],
            self.results['dataset_stats'],
            output_dir
        )

        # Save confusion matrix plot
        if self.results['classifier_metrics']:
            cm_path = output_path / "confusion_matrix.png"
            self.classifier_eval.plot_confusion_matrix(
                self.results['classifier_metrics'],
                str(cm_path)
            )

        # Save detailed results
        results_file = output_path / "detailed_results.json"
        with open(results_file, 'w') as f:
            # Make a copy without the full query_results (too large)
            summary = {
                'classifier_metrics': self.results['classifier_metrics'],
                'response_metrics': self.results['response_metrics'],
                'timing_metrics': self.results['timing_metrics'],
                'dataset_stats': self.results['dataset_stats'],
                'sample_queries': self.results['query_results'][:10]  # Just first 10
            }
            json.dump(summary, f, indent=2)

        print(f"\n✓ Reports generated in: {output_dir}")
        print(f"  - evaluation_report.txt")
        print(f"  - evaluation_metrics.json")
        print(f"  - confusion_matrix.png")
        print(f"  - detailed_results.json")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run comprehensive evaluation of Teaching Calculator"
    )

    parser.add_argument(
        '--enable-wolfram',
        action='store_true',
        help='Enable Wolfram Alpha layer (requires API key)'
    )

    parser.add_argument(
        '--model-path',
        type=str,
        default=None,
        help='Path to LLM model file'
    )

    parser.add_argument(
        '--sample-size',
        type=int,
        default=None,
        help='Number of queries to evaluate (default: all)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='./eval_results',
        help='Directory to save evaluation results'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run evaluation
    try:
        runner = EvaluationRunner(
            enable_wolfram=args.enable_wolfram,
            model_path=args.model_path,
            enable_cache=False  # Disable cache for evaluation
        )

        results = runner.run_full_evaluation(
            sample_size=args.sample_size,
            output_dir=args.output_dir
        )

        # Print final summary
        print("\n" + "="*70)
        print("EVALUATION SUMMARY")
        print("="*70)

        if results['classifier_metrics']:
            print(f"\nClassifier Accuracy: {results['classifier_metrics']['accuracy']:.3f}")
            print(f"Weighted F1 Score: {results['classifier_metrics']['weighted_f1']:.3f}")

        if results['timing_metrics']:
            print(f"\nAverage Response Time: {results['timing_metrics']['overall']['avg_time']:.2f}s")

        print(f"\nFull results saved to: {args.output_dir}")
        print("="*70)

        return 0

    except Exception as e:
        logging.error(f"Evaluation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
