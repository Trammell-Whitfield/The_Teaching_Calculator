#!/usr/bin/env python3
"""
Holy Calculator - Math-Enhanced LLM Calculator
Main entry point for the cascading math solver system.

Architecture:
    Layer 1: SymPy (fast, offline symbolic math)
    Layer 2: Wolfram Alpha (comprehensive, online API)
    Layer 3: Qwen2.5-Math-7B-Instruct (LLM fallback, offline)

Supported Models (auto-detected):
    - Qwen2.5-Math-7B-Instruct Q5_K_M (recommended for 16GB RAM)
    - Qwen2.5-Math-7B-Instruct Q4_K_M (recommended for 8GB RAM)

Usage:
    python main.py --query "Solve for x: 2x + 5 = 13"
    python main.py --interactive
    python main.py --test
"""

import argparse
import logging
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

# Configure logging
def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

def validate_model_path(model_path: str) -> Path:
    """Validate that the model file exists and return as Path object."""
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Model file not found: {model_path}\n"
            f"Available models should be in 'models/quantized/' directory.\n"
            f"Run quantization first if you haven't already."
        )
    if not path.suffix == '.gguf':
        raise ValueError(f"Model must be in GGUF format, got: {path.suffix}")
    return path


def get_default_model() -> str:
    """Find the best available quantized model."""
    quantized_dir = Path(__file__).parent / 'models' / 'quantized'

    # Priority: Qwen2.5-Math > DeepSeek-Math
    # Q5_K_M for 16GB RAM systems, Q4_K_M for 8GB RAM
    preferred_models = [
        'qwen2.5-math-7b-instruct-q5km.gguf',
        'qwen2.5-math-7b-instruct-q4km.gguf',
        'deepseek-math-7b-q5km.gguf',
        'deepseek-math-7b-q4km.gguf',
    ]

    for model_name in preferred_models:
        model_path = quantized_dir / model_name
        if model_path.exists():
            return str(model_path)

    return str(quantized_dir / 'qwen2.5-math-7b-instruct-q5km.gguf')


def main():
    parser = argparse.ArgumentParser(
        description='Holy Calculator - Math-Enhanced LLM Calculator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --query "What is the derivative of x^2 + 3x + 2?"
  %(prog)s --interactive
  %(prog)s --test --verbose
  %(prog)s --query "Solve 2x + 5 = 13" --model models/quantized/qwen2.5-math-7b-instruct-q5km.gguf
        """
    )
    parser.add_argument(
        '--query', '-q',
        type=str,
        help='Mathematical query to solve'
    )
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode'
    )
    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='Run test suite'
    )
    parser.add_argument(
        '--enable-wolfram',
        action='store_true',
        help='Enable Wolfram Alpha layer (requires API key and internet)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Path to LLM model (GGUF format). Auto-detects if not specified.'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Setup logging first
    logger = setup_logging(args.verbose)

    # Validate arguments
    if not any([args.query, args.interactive, args.test]):
        parser.print_help()
        logger.error("Must specify --query, --interactive, or --test")
        sys.exit(1)

    # Determine and validate model path
    model_path = args.model if args.model else get_default_model()
    logger.debug(f"Using model: {model_path}")

    try:
        model_path = validate_model_path(model_path)
        logger.info(f"Model validated: {model_path.name}")
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        sys.exit(2)

    # Import cascade engine
    try:
        from cascade.calculator_engine import CalculatorEngine
    except ImportError as e:
        logger.error(f"Failed to import CalculatorEngine: {e}")
        logger.error("Make sure Phase 7 is complete and all dependencies are installed.")
        sys.exit(3)

    # Initialize calculator engine
    try:
        logger.debug("Initializing calculator engine...")
        engine = CalculatorEngine(
            enable_wolfram=args.enable_wolfram,
            model_path=str(model_path)
        )
        logger.info("Calculator engine ready!")
    except Exception as e:
        logger.error(f"Failed to initialize calculator engine: {e}")
        sys.exit(4)

    if args.test:
        logger.info("Running test suite...")
        _run_test_suite(engine, logger)
        return 0

    if args.interactive:
        logger.info("Starting interactive mode...")
        _run_interactive_mode(engine, logger)
        return 0

    if args.query:
        logger.info("Processing query...")
        result = engine.solve(args.query)
        _print_result(result)

        # Show statistics if verbose
        if args.verbose:
            engine.print_stats()

        return 0 if result['success'] else 1


def _print_result(result: dict):
    """Print query result in a user-friendly format."""
    print("\n" + "=" * 70)

    if result['success']:
        print("✓ SOLUTION FOUND")
        print("=" * 70)
        print(f"\n{result['result']}\n")
        print(f"Source: Layer {_layer_to_num(result['source'])} ({result['source'].upper()})")
        print(f"Response time: {result['response_time']:.2f}s")

        if len(result['cascade_path']) > 1:
            cascade = ' → '.join([_layer_to_num(l) for l in result['cascade_path']])
            print(f"Cascade path: {cascade}")
    else:
        print("✗ NO SOLUTION FOUND")
        print("=" * 70)
        print(f"\nError: {result['error']}")
        print(f"Attempted: {', '.join(result['cascade_path'])}")
        print(f"Response time: {result['response_time']:.2f}s")

        print("\nTroubleshooting:")
        print("  - For Wolfram queries, ensure --enable-wolfram flag is set")
        print("  - For complex queries, the LLM may need more context")
        print("  - Try rephrasing your question")

    print("=" * 70 + "\n")


def _layer_to_num(layer: str) -> str:
    """Convert layer name to number."""
    mapping = {'sympy': 'L1', 'wolfram': 'L2', 'llm': 'L3'}
    return mapping.get(layer, layer)


def _run_test_suite(engine, logger=None):
    """Run a quick test suite."""
    test_queries = [
        ("Solve for x: 2x + 5 = 13", "sympy"),
        ("What is the derivative of x^2 + 3x?", "sympy"),
        ("Simplify: (x+1)(x-1)", "sympy"),
        ("What is 12345 + 67890?", "sympy"),
        ("Explain why 2 + 2 = 4", "llm"),
    ]

    print("\n" + "=" * 70)
    print("RUNNING TEST SUITE")
    print("=" * 70)

    passed = 0
    failed = 0

    for i, (query, expected_layer) in enumerate(test_queries, 1):
        print(f"\nTest {i}/{len(test_queries)}: {query}")
        print("-" * 70)

        result = engine.solve(query)

        if result['success']:
            print(f"✓ PASS - Solved by {result['source']} in {result['response_time']:.2f}s")
            passed += 1

            if result['source'] != expected_layer:
                print(f"  Note: Expected {expected_layer}, got {result['source']}")
        else:
            print(f"✗ FAIL - {result['error']}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 70 + "\n")

    engine.print_stats()


def _run_interactive_mode(engine, logger=None):
    """Run interactive REPL mode."""
    print("\n" + "=" * 70)
    print("HOLY CALCULATOR - INTERACTIVE MODE")
    print("=" * 70)
    print("\nEnter mathematical queries. Type 'quit' or 'exit' to stop.")
    print("Type 'help' for commands, 'stats' for statistics.\n")

    while True:
        try:
            # Get user input
            query = input("🧮 > ").strip()

            if not query:
                continue

            # Handle commands
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break

            if query.lower() == 'help':
                print("\nCommands:")
                print("  quit/exit - Exit interactive mode")
                print("  stats     - Show statistics")
                print("  help      - Show this message")
                print("  clear     - Clear screen")
                print("\nOr enter any mathematical query to solve.\n")
                continue

            if query.lower() == 'stats':
                engine.print_stats()
                continue

            if query.lower() == 'clear':
                import os
                os.system('clear' if os.name != 'nt' else 'cls')
                continue

            # Process query
            print()
            result = engine.solve(query)

            if result['success']:
                print(f"✓ {result['result']}")
                print(f"  [{result['source']}, {result['response_time']:.2f}s]")
            else:
                print(f"✗ {result['error']}")

            print()

        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'quit' to exit.\n")
            continue
        except EOFError:
            print("\n\nGoodbye!")
            break


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
