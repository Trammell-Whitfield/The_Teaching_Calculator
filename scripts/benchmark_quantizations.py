#!/usr/bin/env python3
"""
Benchmark Q4 vs Q5 Quantizations
Compares performance, quality, and memory usage of different quantization levels.
"""

import sys
import time
import psutil
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from cascade.llm_handler import LLMHandler
from cascade.calculator_engine import CalculatorEngine

# Test queries covering different complexity levels
TEST_QUERIES = [
    # Simple arithmetic (baseline)
    "What is 25 * 17?",

    # Algebra
    "Solve for x: 3x + 7 = 22",

    # Calculus
    "What is the derivative of x^3 + 2x^2 - 5x + 1?",

    # Word problem
    "If a train travels 120 miles in 2 hours, what is its average speed?",

    # Multi-step reasoning
    "A rectangle has a perimeter of 30 cm and a length of 10 cm. What is its area?",
]


def get_available_models(base_dir):
    """Find all available quantized models."""
    models_dir = base_dir / 'models' / 'quantized'

    if not models_dir.exists():
        return []

    models = {}
    for model_file in models_dir.glob('*.gguf'):
        name = model_file.name
        # Categorize by quantization level
        if 'q4' in name.lower():
            models.setdefault('Q4', []).append(model_file)
        elif 'q5' in name.lower():
            models.setdefault('Q5', []).append(model_file)

    return models


def benchmark_model(model_path, queries, threads=2):
    """
    Benchmark a single model.

    Returns:
        Dictionary with performance metrics
    """
    print(f"\n{'='*70}")
    print(f"Benchmarking: {model_path.name}")
    print(f"{'='*70}")

    # Initialize handler
    try:
        handler = LLMHandler(model_path=str(model_path))
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        return None

    # Track metrics
    results = {
        'model': model_path.name,
        'model_size_mb': model_path.stat().st_size / (1024 * 1024),
        'queries': [],
        'total_time': 0,
        'total_tokens': 0,
        'successes': 0,
        'failures': 0,
    }

    # Get initial memory
    process = psutil.Process()
    initial_memory = process.memory_info().rss / (1024 * 1024)  # MB

    # Run queries
    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] Query: {query[:60]}...")

        start_time = time.time()
        result = handler.process_query(query)
        elapsed = time.time() - start_time

        if result and result['success']:
            tokens = result.get('tokens_generated', 0)
            tokens_per_sec = tokens / elapsed if elapsed > 0 else 0

            print(f"  ✓ Success: {tokens} tokens in {elapsed:.2f}s ({tokens_per_sec:.2f} tok/s)")
            print(f"  Answer: {result['result'][:80]}...")

            results['successes'] += 1
            results['total_time'] += elapsed
            results['total_tokens'] += tokens

            results['queries'].append({
                'query': query,
                'success': True,
                'time': elapsed,
                'tokens': tokens,
                'tokens_per_sec': tokens_per_sec,
                'answer': result['result'],
            })
        else:
            error = result.get('error', 'Unknown error') if result else 'No result'
            print(f"  ✗ Failed: {error}")

            results['failures'] += 1
            results['queries'].append({
                'query': query,
                'success': False,
                'error': error,
            })

    # Get peak memory usage
    peak_memory = process.memory_info().rss / (1024 * 1024)  # MB
    results['memory_used_mb'] = peak_memory - initial_memory

    # Calculate averages
    if results['successes'] > 0:
        results['avg_time'] = results['total_time'] / results['successes']
        results['avg_tokens_per_sec'] = results['total_tokens'] / results['total_time'] if results['total_time'] > 0 else 0
    else:
        results['avg_time'] = 0
        results['avg_tokens_per_sec'] = 0

    return results


def print_comparison(q4_results, q5_results):
    """Print side-by-side comparison of Q4 vs Q5."""
    print("\n" + "="*70)
    print("Q4 vs Q5 COMPARISON")
    print("="*70)

    if not q4_results or not q5_results:
        print("⚠ Missing results for comparison")
        return

    # Model info
    print("\n📦 MODEL SPECIFICATIONS:")
    print(f"  Q4 Model: {q4_results['model']}")
    print(f"    Size: {q4_results['model_size_mb']:.1f} MB")
    print(f"  Q5 Model: {q5_results['model']}")
    print(f"    Size: {q5_results['model_size_mb']:.1f} MB")
    print(f"  Size difference: {q5_results['model_size_mb'] - q4_results['model_size_mb']:.1f} MB ({((q5_results['model_size_mb'] / q4_results['model_size_mb']) - 1) * 100:.1f}% larger)")

    # Performance
    print("\n⚡ PERFORMANCE:")
    print(f"  Q4 avg speed: {q4_results['avg_tokens_per_sec']:.2f} tokens/sec")
    print(f"  Q5 avg speed: {q5_results['avg_tokens_per_sec']:.2f} tokens/sec")
    if q4_results['avg_tokens_per_sec'] > 0:
        speedup = (q4_results['avg_tokens_per_sec'] / q5_results['avg_tokens_per_sec'] - 1) * 100
        print(f"  Q4 is {abs(speedup):.1f}% {'faster' if speedup > 0 else 'slower'}")

    print(f"\n  Q4 avg response time: {q4_results['avg_time']:.2f}s")
    print(f"  Q5 avg response time: {q5_results['avg_time']:.2f}s")

    # Memory
    print(f"\n💾 MEMORY USAGE:")
    print(f"  Q4: {q4_results['memory_used_mb']:.1f} MB")
    print(f"  Q5: {q5_results['memory_used_mb']:.1f} MB")
    print(f"  Difference: {q5_results['memory_used_mb'] - q4_results['memory_used_mb']:.1f} MB")

    # Success rates
    print(f"\n✓ SUCCESS RATES:")
    total = len(TEST_QUERIES)
    print(f"  Q4: {q4_results['successes']}/{total} ({q4_results['successes']/total*100:.0f}%)")
    print(f"  Q5: {q5_results['successes']}/{total} ({q5_results['successes']/total*100:.0f}%)")

    # Query-by-query comparison
    print(f"\n📊 QUERY-BY-QUERY COMPARISON:")
    print(f"{'Query':<50} {'Q4 (tok/s)':<12} {'Q5 (tok/s)':<12} {'Winner'}")
    print("-" * 90)

    for i, (q4_q, q5_q) in enumerate(zip(q4_results['queries'], q5_results['queries'])):
        query = q4_q['query'][:47] + "..." if len(q4_q['query']) > 47 else q4_q['query']

        if q4_q['success'] and q5_q['success']:
            q4_speed = q4_q['tokens_per_sec']
            q5_speed = q5_q['tokens_per_sec']
            winner = "Q4" if q4_speed > q5_speed else "Q5" if q5_speed > q4_speed else "Tie"
            print(f"{query:<50} {q4_speed:>8.2f}     {q5_speed:>8.2f}     {winner}")
        else:
            q4_status = f"{q4_q['tokens_per_sec']:.2f}" if q4_q['success'] else "FAIL"
            q5_status = f"{q5_q['tokens_per_sec']:.2f}" if q5_q['success'] else "FAIL"
            print(f"{query:<50} {q4_status:>8}     {q5_status:>8}")

    # Recommendation
    print("\n" + "="*70)
    print("💡 RECOMMENDATION:")

    # Simple heuristic
    q4_faster = q4_results['avg_tokens_per_sec'] > q5_results['avg_tokens_per_sec']
    speed_diff = abs(q4_results['avg_tokens_per_sec'] - q5_results['avg_tokens_per_sec'])

    if q4_faster and speed_diff > 0.5:
        print("  → Use Q4: Significantly faster with minimal quality loss")
    elif not q4_faster and speed_diff > 0.5:
        print("  → Use Q5: Not much slower, better quality")
    else:
        print("  → Similar performance: Q4 recommended for speed, Q5 for quality")

    print("="*70 + "\n")


def main():
    """Main benchmark runner."""
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark Q4 vs Q5 quantizations")
    parser.add_argument('--threads', type=int, default=2, help='Number of threads to use')
    parser.add_argument('--queries', nargs='+', help='Custom queries to test (overrides defaults)')
    parser.add_argument('--no-prompt', action='store_true', help='Skip interactive prompts (for automated runs)')
    args = parser.parse_args()

    print("🧪 QUANTIZATION BENCHMARK")
    print("="*70)

    base_dir = Path(__file__).parent.parent

    # Find models
    models = get_available_models(base_dir)

    if not models:
        print("✗ No quantized models found in models/quantized/")
        print("  Please ensure you have Q4 and Q5 models available.")
        return 1

    print(f"\nFound models:")
    for quant_level, model_list in models.items():
        print(f"  {quant_level}: {len(model_list)} model(s)")
        for model in model_list:
            print(f"    - {model.name}")

    # Select models to test
    q4_model = models.get('Q4', [None])[0]
    q5_model = models.get('Q5', [None])[0]

    if not q4_model or not q5_model:
        print("\n✗ Need both Q4 and Q5 models for comparison")
        return 1

    # Use custom queries or defaults
    queries = args.queries if args.queries else TEST_QUERIES

    print(f"\nTest configuration:")
    print(f"  Threads: {args.threads}")
    print(f"  Queries: {len(queries)}")
    print(f"  Q4 model: {q4_model.name}")
    print(f"  Q5 model: {q5_model.name}")

    if not args.no_prompt:
        input("\nPress Enter to start benchmark...")
    else:
        print("\nStarting benchmark...")

    # Benchmark Q4
    q4_results = benchmark_model(q4_model, queries, threads=args.threads)

    # Benchmark Q5
    q5_results = benchmark_model(q5_model, queries, threads=args.threads)

    # Compare results
    if q4_results and q5_results:
        print_comparison(q4_results, q5_results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
