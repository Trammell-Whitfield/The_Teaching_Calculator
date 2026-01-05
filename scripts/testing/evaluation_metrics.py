#!/usr/bin/env python3
"""
Evaluation Metrics for Teaching Calculator
Implements classification metrics, scoring, and analysis.
"""

import numpy as np
from typing import Dict, List, Any, Tuple
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
    accuracy_score
)
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import re


class ClassifierEvaluator:
    """Evaluates the query classifier/router performance."""

    def __init__(self):
        """Initialize the evaluator."""
        self.tier_names = ['sympy', 'wolfram', 'llm', 'decline']
        self.tier_to_idx = {name: idx for idx, name in enumerate(self.tier_names)}
        self.idx_to_tier = {idx: name for idx, name in enumerate(self.tier_names)}

    def evaluate(self, y_true: List[str], y_pred: List[str]) -> Dict[str, Any]:
        """
        Evaluate classifier performance.

        Args:
            y_true: Ground truth tier labels
            y_pred: Predicted tier labels

        Returns:
            Dictionary with comprehensive metrics
        """
        # Convert to indices
        y_true_idx = [self.tier_to_idx[t] for t in y_true]
        y_pred_idx = [self.tier_to_idx[t] for t in y_pred]

        # Calculate metrics
        accuracy = accuracy_score(y_true_idx, y_pred_idx)

        # Find unique labels actually present in the data
        unique_labels = sorted(set(y_true_idx + y_pred_idx))
        unique_tier_names = [self.tier_names[i] for i in unique_labels]

        # Per-tier metrics (only for classes that are present)
        precision, recall, f1, support = precision_recall_fscore_support(
            y_true_idx, y_pred_idx, average=None, labels=unique_labels, zero_division=0
        )

        # Macro and weighted averages
        macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
            y_true_idx, y_pred_idx, average='macro', zero_division=0
        )

        weighted_precision, weighted_recall, weighted_f1, _ = precision_recall_fscore_support(
            y_true_idx, y_pred_idx, average='weighted', zero_division=0
        )

        # Confusion matrix (only for classes actually present)
        cm = confusion_matrix(y_true_idx, y_pred_idx, labels=unique_labels)

        # Per-tier metrics dict (only for classes that were evaluated)
        per_tier_metrics = {}
        for i, idx in enumerate(unique_labels):
            tier = self.tier_names[idx]
            per_tier_metrics[tier] = {
                'precision': float(precision[i]),
                'recall': float(recall[i]),
                'f1': float(f1[i]),
                'support': int(support[i])
            }

        return {
            'accuracy': float(accuracy),
            'macro_precision': float(macro_precision),
            'macro_recall': float(macro_recall),
            'macro_f1': float(macro_f1),
            'weighted_precision': float(weighted_precision),
            'weighted_recall': float(weighted_recall),
            'weighted_f1': float(weighted_f1),
            'per_tier_metrics': per_tier_metrics,
            'confusion_matrix': cm.tolist(),
            'classification_report': classification_report(
                y_true_idx, y_pred_idx,
                labels=unique_labels,
                target_names=unique_tier_names,
                output_dict=True,
                zero_division=0
            ),
            'tiers_evaluated': unique_tier_names
        }

    def print_metrics(self, metrics: Dict[str, Any]):
        """Print metrics in a readable format."""
        print("\n" + "="*70)
        print("CLASSIFIER EVALUATION METRICS")
        print("="*70)

        print(f"\nOverall Accuracy: {metrics['accuracy']:.3f}")

        print("\n" + "-"*70)
        print("Per-Tier Metrics:")
        print("-"*70)
        print(f"{'Tier':<12} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Support':<12}")
        print("-"*70)

        # Only print metrics for tiers that were evaluated
        for tier in metrics.get('tiers_evaluated', self.tier_names):
            m = metrics['per_tier_metrics'][tier]
            print(f"{tier:<12} {m['precision']:<12.3f} {m['recall']:<12.3f} "
                  f"{m['f1']:<12.3f} {m['support']:<12}")

        print("-"*70)
        print(f"{'Macro Avg':<12} {metrics['macro_precision']:<12.3f} "
              f"{metrics['macro_recall']:<12.3f} {metrics['macro_f1']:<12.3f}")
        print(f"{'Weighted Avg':<12} {metrics['weighted_precision']:<12.3f} "
              f"{metrics['weighted_recall']:<12.3f} {metrics['weighted_f1']:<12.3f}")
        print("="*70)

    def plot_confusion_matrix(self, metrics: Dict[str, Any], save_path: str):
        """
        Plot and save confusion matrix.

        Args:
            metrics: Metrics dictionary containing confusion matrix
            save_path: Path to save the plot
        """
        cm = np.array(metrics['confusion_matrix'])

        # Use only the tiers that were evaluated
        tier_labels = metrics.get('tiers_evaluated', self.tier_names)

        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                    xticklabels=tier_labels,
                    yticklabels=tier_labels)
        plt.xlabel('Predicted Tier', fontsize=12)
        plt.ylabel('Actual Tier', fontsize=12)
        plt.title('Query Classifier Confusion Matrix', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Confusion matrix saved to: {save_path}")

    def analyze_misclassifications(self, y_true: List[str], y_pred: List[str],
                                   queries: List[str]) -> Dict[str, List[Dict]]:
        """
        Analyze misclassification patterns.

        Args:
            y_true: Ground truth labels
            y_pred: Predicted labels
            queries: Original queries

        Returns:
            Dictionary mapping misclassification types to examples
        """
        misclassifications = {}

        for i, (true, pred) in enumerate(zip(y_true, y_pred)):
            if true != pred:
                key = f"{pred}→{true}"  # Predicted→Actual
                if key not in misclassifications:
                    misclassifications[key] = []

                misclassifications[key].append({
                    'query': queries[i],
                    'true_tier': true,
                    'predicted_tier': pred
                })

        return misclassifications

    def calculate_cost_weighted_accuracy(self, y_true: List[str], y_pred: List[str],
                                         cost_matrix: Dict[Tuple[str, str], float]) -> float:
        """
        Calculate accuracy weighted by misclassification costs.

        Args:
            y_true: Ground truth labels
            y_pred: Predicted labels
            cost_matrix: Dict mapping (predicted, actual) to cost

        Returns:
            Cost-weighted accuracy score
        """
        total_cost = 0
        for true, pred in zip(y_true, y_pred):
            if true != pred:
                cost = cost_matrix.get((pred, true), 1.0)
                total_cost += cost

        # Normalize by max possible cost
        max_cost = len(y_true) * max(cost_matrix.values())
        return 1.0 - (total_cost / max_cost)


class ResponseScorer:
    """Scores responses for correctness and quality."""

    def __init__(self):
        """Initialize the scorer."""
        pass

    def score_computational(self, predicted: str, expected: str,
                           tolerance: float = 0.001) -> Tuple[int, str]:
        """
        Score computational (Tier 1/2) responses.

        Args:
            predicted: The predicted answer
            expected: The expected answer
            tolerance: Numerical tolerance for floating point comparison

        Returns:
            (score, reasoning) where score is 0 or 1
        """
        if not predicted or not expected:
            return (0, "Empty response")

        # Normalize both strings
        pred_norm = self._normalize_math_expression(predicted)
        exp_norm = self._normalize_math_expression(expected)

        # Exact match after normalization
        if pred_norm == exp_norm:
            return (1, "Exact match")

        # Try numerical comparison
        try:
            pred_num = self._extract_number(predicted)
            exp_num = self._extract_number(expected)

            if pred_num is not None and exp_num is not None:
                if abs(pred_num - exp_num) < tolerance:
                    return (1, f"Numerical match (diff: {abs(pred_num - exp_num):.6f})")
                else:
                    return (0, f"Numerical mismatch (diff: {abs(pred_num - exp_num):.6f})")

        except (ValueError, TypeError):
            pass

        # Check if answer is contained in response
        if exp_norm in pred_norm:
            return (1, "Answer contained in response")

        return (0, "No match found")

    def score_explanatory(self, response: str, expected_keywords: List[str] = None) -> Tuple[int, str]:
        """
        Score explanatory (Tier 3 LLM) responses using rubric.

        Rubric:
        3 - Correct answer + clear explanation + appropriate depth
        2 - Correct answer + partial explanation
        1 - Partially correct or correct but unclear
        0 - Incorrect or irrelevant

        Args:
            response: The LLM's response
            expected_keywords: Optional list of keywords that should appear

        Returns:
            (score, reasoning) where score is 0-3
        """
        if not response or len(response) < 20:
            return (0, "Response too short or empty")

        score = 0
        reasons = []

        # Check length (proxy for depth)
        if len(response) > 100:
            score += 1
            reasons.append("sufficient length")

        # Check for explanation markers
        explanation_markers = [
            'because', 'since', 'therefore', 'thus', 'which means',
            'this is', 'the reason', 'we can see', 'notice that'
        ]
        if any(marker in response.lower() for marker in explanation_markers):
            score += 1
            reasons.append("contains explanation markers")

        # Check for mathematical content
        math_indicators = [
            r'\d+', r'x\^?\d+', r'[+\-*/=]', r'theorem', r'formula',
            r'equation', r'function', r'derivative', r'integral'
        ]
        if any(re.search(pattern, response.lower()) for pattern in math_indicators):
            score += 1
            reasons.append("contains mathematical content")

        # Check for expected keywords if provided
        if expected_keywords:
            keyword_matches = sum(1 for kw in expected_keywords if kw.lower() in response.lower())
            if keyword_matches >= len(expected_keywords) * 0.5:  # 50% match
                reasons.append(f"contains {keyword_matches}/{len(expected_keywords)} keywords")
            else:
                score = max(0, score - 1)
                reasons.append(f"missing keywords ({keyword_matches}/{len(expected_keywords)})")

        # Cap at 3
        score = min(score, 3)

        reasoning = "; ".join(reasons) if reasons else "no clear indicators"
        return (score, reasoning)

    def _normalize_math_expression(self, expr: str) -> str:
        """Normalize a mathematical expression for comparison."""
        if not expr:
            return ""

        # Convert to lowercase
        expr = expr.lower()

        # Remove whitespace
        expr = re.sub(r'\s+', '', expr)

        # Normalize common patterns
        expr = expr.replace('**', '^')
        expr = expr.replace('*', '')
        expr = expr.replace('sqrt', '√')

        # Remove common wrappers
        expr = expr.replace('[', '').replace(']', '')
        expr = expr.replace('{', '').replace('}', '')

        return expr

    def _extract_number(self, text: str) -> float:
        """Extract the first number from text."""
        # Look for number patterns
        patterns = [
            r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?',  # Scientific notation
            r'[-+]?\d+/\d+',  # Fractions
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                num_str = match.group()
                try:
                    # Handle fractions
                    if '/' in num_str:
                        parts = num_str.split('/')
                        return float(parts[0]) / float(parts[1])
                    return float(num_str)
                except ValueError:
                    continue

        return None


class EvaluationReport:
    """Generates comprehensive evaluation reports."""

    def __init__(self):
        """Initialize the report generator."""
        pass

    def generate_report(self, classifier_metrics: Dict[str, Any],
                       response_metrics: Dict[str, Any],
                       dataset_stats: Dict[str, Any],
                       output_dir: str):
        """
        Generate a comprehensive evaluation report.

        Args:
            classifier_metrics: Metrics from classifier evaluation
            response_metrics: Metrics from response scoring
            dataset_stats: Statistics about the dataset
            output_dir: Directory to save report files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Generate text report
        report_file = output_path / "evaluation_report.txt"
        with open(report_file, 'w') as f:
            self._write_text_report(f, classifier_metrics, response_metrics, dataset_stats)

        print(f"✓ Text report saved to: {report_file}")

        # Generate JSON report
        import json
        json_file = output_path / "evaluation_metrics.json"
        with open(json_file, 'w') as f:
            json.dump({
                'classifier_metrics': classifier_metrics,
                'response_metrics': response_metrics,
                'dataset_stats': dataset_stats
            }, f, indent=2)

        print(f"✓ JSON metrics saved to: {json_file}")

    def _write_text_report(self, f, classifier_metrics, response_metrics, dataset_stats):
        """Write formatted text report."""
        f.write("="*70 + "\n")
        f.write("TEACHING CALCULATOR - EVALUATION REPORT\n")
        f.write("="*70 + "\n\n")

        # Dataset statistics
        f.write("DATASET STATISTICS\n")
        f.write("-"*70 + "\n")
        f.write(f"Total queries: {dataset_stats['total_queries']}\n\n")

        f.write("Tier distribution:\n")
        for tier, count in dataset_stats['tier_distribution'].items():
            pct = (count / dataset_stats['total_queries']) * 100
            f.write(f"  {tier:10s}: {count:3d} ({pct:5.1f}%)\n")
        f.write("\n")

        # Classifier metrics
        f.write("CLASSIFIER PERFORMANCE\n")
        f.write("-"*70 + "\n")
        f.write(f"Overall Accuracy: {classifier_metrics['accuracy']:.3f}\n")
        f.write(f"Macro F1: {classifier_metrics['macro_f1']:.3f}\n")
        f.write(f"Weighted F1: {classifier_metrics['weighted_f1']:.3f}\n\n")

        f.write("Per-Tier Metrics:\n")
        f.write(f"{'Tier':<12} {'Precision':<12} {'Recall':<12} {'F1-Score':<12}\n")
        f.write("-"*70 + "\n")
        for tier, metrics in classifier_metrics['per_tier_metrics'].items():
            f.write(f"{tier:<12} {metrics['precision']:<12.3f} {metrics['recall']:<12.3f} "
                   f"{metrics['f1']:<12.3f}\n")
        f.write("\n")

        # Response metrics
        if response_metrics:
            f.write("RESPONSE QUALITY\n")
            f.write("-"*70 + "\n")

            for tier, metrics in response_metrics.items():
                f.write(f"\n{tier.upper()}:\n")
                f.write(f"  Accuracy: {metrics.get('accuracy', 'N/A')}\n")
                if 'avg_score' in metrics:
                    f.write(f"  Average Score: {metrics['avg_score']:.2f}/3.0\n")

        f.write("\n" + "="*70 + "\n")


def main():
    """Test the evaluation metrics."""
    # Create sample data
    y_true = ['sympy', 'sympy', 'wolfram', 'llm', 'llm', 'decline']
    y_pred = ['sympy', 'wolfram', 'wolfram', 'llm', 'llm', 'decline']

    # Test classifier evaluator
    evaluator = ClassifierEvaluator()
    metrics = evaluator.evaluate(y_true, y_pred)

    evaluator.print_metrics(metrics)

    # Save confusion matrix
    output_dir = Path("/tmp/eval_output")
    output_dir.mkdir(exist_ok=True)
    evaluator.plot_confusion_matrix(metrics, str(output_dir / "confusion_matrix.png"))

    # Test response scorer
    scorer = ResponseScorer()

    # Test computational scoring
    print("\n" + "="*70)
    print("RESPONSE SCORING TESTS")
    print("="*70)

    comp_tests = [
        ("3*x**2", "3x^2"),
        ("7.389", "7.390"),
        ("The answer is 42", "42"),
    ]

    print("\nComputational scoring:")
    for pred, exp in comp_tests:
        score, reason = scorer.score_computational(pred, exp)
        print(f"  {pred} vs {exp}: score={score}, reason='{reason}'")

    # Test explanatory scoring
    expl_tests = [
        "The Pythagorean theorem states that a^2 + b^2 = c^2 because...",
        "Yes",
        "The derivative measures the rate of change of a function with respect to its variable.",
    ]

    print("\nExplanatory scoring:")
    for resp in expl_tests:
        score, reason = scorer.score_explanatory(resp)
        print(f"  '{resp[:50]}...': score={score}/3, reason='{reason}'")


if __name__ == "__main__":
    main()
