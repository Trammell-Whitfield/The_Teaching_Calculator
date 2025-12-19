#!/usr/bin/env python3
"""
Interactive CLI for Holy Calculator
Directly prompt the model and see outputs without TI-84 interface.
"""

import sys
import logging
from pathlib import Path

# Add scripts to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from cascade.calculator_engine import CalculatorEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_banner():
    """Print welcome banner."""
    print("\n" + "="*70)
    print("HOLY CALCULATOR - INTERACTIVE MODE")
    print("="*70)
    print("Ask math questions directly and see model outputs.")
    print("Commands:")
    print("  'stats'  - Show performance statistics")
    print("  'clear'  - Clear cache")
    print("  'quit'   - Exit")
    print("="*70 + "\n")


def print_result(result, verbose=True):
    """
    Print query result in a readable format.

    Args:
        result: Result dictionary from engine.solve()
        verbose: Show detailed metadata
    """
    if result['success']:
        print(f"\n✓ SUCCESS")
        print(f"{'='*70}")

        # Show result
        result_text = result['result'] if result['result'] else "[No result]"
        print(f"Answer: {result_text}")

        if verbose:
            print(f"\nMetadata:")
            print(f"  Source: {result['source']}")
            print(f"  Response time: {result['response_time']:.3f}s")
            print(f"  Cascade path: {' → '.join(result['cascade_path'])}")
            print(f"  Routing confidence: {result.get('routing_confidence', 0):.2%}")

            if result.get('from_cache'):
                print(f"  [CACHED RESULT]")

        print(f"{'='*70}\n")
    else:
        print(f"\n✗ FAILED")
        print(f"{'='*70}")
        print(f"Error: {result['error']}")
        print(f"Tried layers: {' → '.join(result['cascade_path'])}")
        print(f"{'='*70}\n")


def interactive_mode(engine, verbose=True):
    """
    Run interactive REPL loop.

    Args:
        engine: CalculatorEngine instance
        verbose: Show detailed metadata for each result
    """
    print_banner()

    while True:
        try:
            # Get user input
            query = input("\n🧮 > ").strip()

            if not query:
                continue

            # Handle commands
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break

            elif query.lower() == 'stats':
                engine.print_stats()
                continue

            elif query.lower() == 'clear':
                if engine.cache_enabled and engine.cache:
                    engine.cache.clear_memory()
                    print("✓ Cache cleared")
                else:
                    print("⚠ Cache is disabled")
                continue

            elif query.lower() == 'help':
                print_banner()
                continue

            elif query.lower().startswith('force:'):
                # Force specific layer (e.g., "force:llm what is 2+2?")
                parts = query.split(':', 2)
                if len(parts) >= 3:
                    layer = parts[1].strip()
                    actual_query = parts[2].strip()

                    if layer in ['sympy', 'wolfram', 'llm']:
                        print(f"\n⚡ Forcing layer: {layer}")
                        result = engine.solve(actual_query, force_layer=layer)
                        print_result(result, verbose)
                    else:
                        print(f"⚠ Invalid layer '{layer}'. Use: sympy, wolfram, or llm")
                else:
                    print("⚠ Format: force:<layer>:<query>")
                continue

            # Process query
            result = engine.solve(query)
            print_result(result, verbose)

        except KeyboardInterrupt:
            print("\n\nUse 'quit' to exit")
            continue
        except EOFError:
            print("\nGoodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            print(f"\n✗ Error: {e}\n")


def batch_mode(engine, queries, verbose=True):
    """
    Run queries in batch mode.

    Args:
        engine: CalculatorEngine instance
        queries: List of queries to process
        verbose: Show detailed metadata
    """
    print(f"\n🧪 BATCH MODE - Processing {len(queries)} queries\n")

    for i, query in enumerate(queries, 1):
        print(f"\n{'='*70}")
        print(f"Query {i}/{len(queries)}: {query}")
        print('='*70)

        result = engine.solve(query)
        print_result(result, verbose)

    # Show final stats
    engine.print_stats()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Interactive CLI for Holy Calculator"
    )
    parser.add_argument(
        '--enable-wolfram',
        action='store_true',
        help='Enable Wolfram Alpha layer (requires API key)'
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable query caching'
    )
    parser.add_argument(
        '--model',
        type=str,
        help='Path to LLM model (auto-detects if not specified)'
    )
    parser.add_argument(
        '--batch',
        nargs='+',
        help='Run in batch mode with specified queries'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Show minimal output (just answers, no metadata)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level'
    )

    args = parser.parse_args()

    # Set log level
    logging.getLogger().setLevel(args.log_level)

    # Initialize engine
    logger.info("Initializing Holy Calculator...")
    try:
        engine = CalculatorEngine(
            enable_wolfram=args.enable_wolfram,
            model_path=args.model,
            enable_cache=not args.no_cache
        )
        logger.info("✓ Engine ready\n")
    except Exception as e:
        logger.error(f"✗ Failed to initialize engine: {e}")
        sys.exit(1)

    # Run in appropriate mode
    verbose = not args.quiet

    if args.batch:
        batch_mode(engine, args.batch, verbose)
    else:
        interactive_mode(engine, verbose)


if __name__ == "__main__":
    main()
