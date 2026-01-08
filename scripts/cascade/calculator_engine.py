#!/usr/bin/env python3
"""
Calculator Engine - Cascade Orchestrator

Main orchestration logic for the 3-layer cascade system:
- Layer 1 (SymPy): Fast offline symbolic math
- Layer 2 (Wolfram): Online API for complex queries
- Layer 3 (LLM): Deep reasoning and explanations

Automatically routes queries to the most appropriate layer and
cascades to fallback layers if needed.
"""

import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import sys

# Import handlers
sys.path.insert(0, str(Path(__file__).parent))
from sympy_handler import SymPyHandler
from wolfram_handler import WolframAlphaHandler
from llm_handler import LLMHandler
from query_cache import SmartCache
from query_translator import QueryTranslator


class MathQueryRouter:
    """
    Intelligent router that determines the best layer to handle each query.

    Uses keyword analysis and pattern matching to route queries optimally.
    """

    # Keywords indicating each layer
    SYMPY_KEYWORDS = [
        'solve', 'simplify', 'expand', 'factor', 'differentiate',
        'integrate', 'derivative', 'limit', 'matrix', 'determinant',
        'eigenvalue', 'roots', 'equation'
    ]

    WOLFRAM_KEYWORDS = [
        'convert', 'plot', 'graph', 'distribution',
        'statistics', 'mean', 'median', 'standard deviation', 'prime',
        'taylor series', 'fourier', 'numerical', 'approximate',
        'speed of', 'mass of', 'molecular', 'atomic', 'chemical'
    ]

    LLM_KEYWORDS = [
        'prove', 'explain', 'why', 'word problem', 'alice', 'bob',
        'train', 'proof', 'show that', 'demonstrate', 'compare',
        'strategy', 'approach', 'understand', 'reasoning'
    ]

    def __init__(self):
        """Initialize the router."""
        self.logger = logging.getLogger(__name__)

    def route_query(self, query: str) -> Dict[str, Any]:
        """Route a query to the most appropriate computational layer."""
        query_lower = query.lower()

        # Proofs and explanations go to LLM
        if any(kw in query_lower for kw in ['prove', 'proof', 'explain', 'why', 'show that']):
            return {
                'primary': 'llm',
                'fallback_order': [],
                'confidence': 0.95,
                'reasoning': 'Requires explanation or proof'
            }

        # Word problems go to LLM
        if self._is_word_problem(query):
            return {
                'primary': 'llm',
                'fallback_order': [],
                'confidence': 0.9,
                'reasoning': 'Word problem detected'
            }

        # Check keyword matches
        sympy_score = sum(1 for kw in self.SYMPY_KEYWORDS if kw in query_lower)
        wolfram_score = sum(1 for kw in self.WOLFRAM_KEYWORDS if kw in query_lower)
        llm_score = sum(1 for kw in self.LLM_KEYWORDS if kw in query_lower)

        # Route based on highest score
        if sympy_score > max(wolfram_score, llm_score):
            return {
                'primary': 'sympy',
                'fallback_order': ['wolfram', 'llm'],
                'confidence': 0.8,
                'reasoning': f'SymPy keywords detected (score: {sympy_score})'
            }
        elif wolfram_score > llm_score:
            return {
                'primary': 'wolfram',
                'fallback_order': ['llm'],
                'confidence': 0.75,
                'reasoning': f'Wolfram keywords detected (score: {wolfram_score})'
            }
        else:
            # Default: try SymPy first (fastest), then cascade
            return {
                'primary': 'sympy',
                'fallback_order': ['wolfram', 'llm'],
                'confidence': 0.6,
                'reasoning': 'No strong indicators, defaulting to SymPy → cascade'
            }

    def _is_word_problem(self, query: str) -> bool:
        """Detect if query is a word problem."""
        indicators = [
            len(query.split()) > 15,  # Long queries often word problems
            any(name in query.lower() for name in ['alice', 'bob', 'train', 'car', 'store']),
            '?' in query and not any(op in query for op in ['=', 'd/dx', '∫']),
            any(word in query.lower() for word in ['if ', 'then', 'how many', 'how much'])
        ]
        return sum(indicators) >= 2


class CalculatorEngine:
    """
    Main orchestrator for the Holy Calculator cascade system.

    Manages all three layers and handles cascading logic.
    """

    def __init__(self, enable_wolfram: bool = False, wolfram_dev_mode: bool = True,
                 model_path: Optional[str] = None, enable_cache: bool = True):
        """
        Initialize the calculator engine.

        Args:
            enable_wolfram: Whether to enable Wolfram Alpha layer (requires API key)
            wolfram_dev_mode: Use development quota for Wolfram (vs production)
            model_path: Path to LLM model (auto-detects if None)
            enable_cache: Enable query result caching (default: True)
        """
        self.logger = logging.getLogger(__name__)

        # Initialize query translator
        self.translator = QueryTranslator()
        self.logger.info("✓ Query translator initialized")

        # Initialize cache
        self.cache = None
        self.cache_enabled = enable_cache
        if enable_cache:
            try:
                self.cache = SmartCache()
                self.logger.info("✓ Cache initialized")
            except Exception as e:
                self.logger.warning(f"⚠ Cache disabled: {e}")
                self.cache_enabled = False

        # Initialize layers
        self.logger.info("Initializing Holy Calculator layers...")

        # Layer 1: SymPy (always available)
        self.sympy = SymPyHandler()
        self.logger.info("✓ Layer 1 (SymPy) initialized")

        # Layer 2: Wolfram Alpha (optional)
        self.wolfram = None
        self.wolfram_enabled = enable_wolfram
        self.wolfram_dev_mode = wolfram_dev_mode

        if enable_wolfram:
            try:
                self.wolfram = WolframAlphaHandler()
                self.logger.info("✓ Layer 2 (Wolfram Alpha) initialized")
            except Exception as e:
                self.logger.warning(f"⚠ Wolfram Alpha disabled: {e}")
                self.wolfram_enabled = False

        # Layer 3: LLM (always available)
        try:
            self.llm = LLMHandler(model_path=model_path)
            self.logger.info(f"✓ Layer 3 (LLM) initialized - Model: {self.llm.model_path.name}")
        except Exception as e:
            self.logger.error(f"✗ Failed to initialize LLM: {e}")
            raise

        # Router
        self.router = MathQueryRouter()

        # Statistics
        self.stats = {
            'total_queries': 0,
            'sympy_successes': 0,
            'wolfram_successes': 0,
            'llm_successes': 0,
            'total_failures': 0,
            'avg_response_time': 0,
            'cascade_triggered': 0,  # How many times we fell through to next layer
        }

    def solve(self, query: str, force_layer: Optional[str] = None) -> Dict[str, Any]:
        """
        Solve a mathematical query using the cascade system.

        Args:
            query: User's mathematical query
            force_layer: Force use of specific layer ('sympy', 'wolfram', or 'llm')

        Returns:
            Dictionary with result and metadata:
            {
                'success': bool,
                'result': str or None,
                'source': 'sympy' | 'wolfram' | 'llm',
                'response_time': float (seconds),
                'cascade_path': ['layer1', 'layer2', ...],
                'error': str or None
            }
        """
        # Check cache first (skip if force_layer specified)
        if self.cache_enabled and not force_layer:
            cached_result = self.cache.get(query)
            if cached_result is not None:
                self.logger.info(f"✓ Cache HIT: {query[:50]}")
                # Update response time to reflect cache retrieval
                cached_result['response_time'] = 0.001  # Near-instant
                cached_result['from_cache'] = True
                return cached_result

        start_time = time.time()
        self.stats['total_queries'] += 1

        # Route the query
        if force_layer:
            routing = {'primary': force_layer, 'fallback_order': [], 'confidence': 1.0,
                      'reasoning': 'User-specified layer'}
        else:
            routing = self.router.route_query(query)

        self.logger.info(f"Query: {query[:60]}...")
        self.logger.debug(f"Routing: {routing['primary']} (confidence: {routing['confidence']:.2f})")
        self.logger.debug(f"Reasoning: {routing['reasoning']}")

        # Build execution order
        execution_order = [routing['primary']] + routing['fallback_order']
        cascade_path = []

        # Try each layer in order
        for layer in execution_order:
            cascade_path.append(layer)

            result = None

            # Try SymPy
            if layer == 'sympy':
                self.logger.debug("→ Trying Layer 1 (SymPy)...")
                result = self._try_sympy(query)

            # Try Wolfram
            elif layer == 'wolfram':
                if not self.wolfram_enabled:
                    self.logger.debug("→ Wolfram Alpha disabled, skipping...")
                    continue

                self.logger.debug("→ Trying Layer 2 (Wolfram Alpha)...")
                result = self._try_wolfram(query)

            # Try LLM
            elif layer == 'llm':
                self.logger.debug("→ Trying Layer 3 (LLM)...")
                result = self._try_llm(query)

            # Check if successful
            if result and result['success']:
                response_time = time.time() - start_time

                # Update statistics
                if layer == 'sympy':
                    self.stats['sympy_successes'] += 1
                elif layer == 'wolfram':
                    self.stats['wolfram_successes'] += 1
                elif layer == 'llm':
                    self.stats['llm_successes'] += 1

                if len(cascade_path) > 1:
                    self.stats['cascade_triggered'] += 1

                # Update average response time
                n = self.stats['total_queries']
                self.stats['avg_response_time'] = (
                    (self.stats['avg_response_time'] * (n - 1) + response_time) / n
                )

                self.logger.info(f"✓ Solved by {layer} in {response_time:.2f}s")

                final_result = {
                    'success': True,
                    'result': result.get('result') or result.get('formatted'),
                    'source': layer,
                    'response_time': response_time,
                    'cascade_path': cascade_path,
                    'routing_confidence': routing['confidence'],
                    'error': None,
                    'from_cache': False
                }

                # Cache successful results
                if self.cache_enabled:
                    self.cache.set(query, final_result)
                    self.logger.debug(f"Cached result for: {query[:50]}")

                return final_result

            # Layer failed, cascade to next
            if len(execution_order) > 1 and layer != execution_order[-1]:
                self.logger.debug(f"  ✗ {layer} failed, cascading to next layer...")

        # All layers failed
        response_time = time.time() - start_time
        self.stats['total_failures'] += 1

        self.logger.warning(f"✗ All layers failed for query: {query[:60]}...")

        return {
            'success': False,
            'result': None,
            'source': 'none',
            'response_time': response_time,
            'cascade_path': cascade_path,
            'routing_confidence': routing['confidence'],
            'error': 'All layers failed to solve the query'
        }

    def _try_sympy(self, query: str) -> Optional[Dict[str, Any]]:
        """Try solving with SymPy using translated format."""
        try:
            # Translate query to SymPy-compatible format
            translated = self.translator.translate(query)
            self.logger.debug(f"Translated to SymPy format: {translated['sympy_format']}")

            # Use translated format for known operations, original for general
            if translated['operation'] in ['derivative', 'second_derivative', 'third_derivative',
                                           'integral', 'limit', 'solve', 'simplify',
                                           'factor', 'expand']:
                query_to_process = translated['sympy_format']
            else:
                query_to_process = query

            return self.sympy.process_query(query_to_process)
        except Exception as e:
            self.logger.debug(f"SymPy error: {e}")
            return None

    def _try_wolfram(self, query: str) -> Optional[Dict[str, Any]]:
        """Try solving with Wolfram Alpha."""
        try:
            return self.wolfram.process_query(query, is_dev=self.wolfram_dev_mode)
        except Exception as e:
            self.logger.debug(f"Wolfram error: {e}")
            return None

    def _try_llm(self, query: str) -> Optional[Dict[str, Any]]:
        """Try solving with LLM using optimized prompt format."""
        try:
            # Translate query to LLM-optimized format
            translated = self.translator.translate(query)
            self.logger.debug(f"Using LLM-optimized prompt format")

            # Use LLM-formatted prompt which encourages proper answer formatting
            query_to_process = translated['llm_format']

            return self.llm.process_query(query_to_process)
        except Exception as e:
            self.logger.debug(f"LLM error: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics from all layers."""
        stats = {
            'engine': self.stats.copy(),
        }

        # Add layer-specific stats
        if self.sympy:
            stats['sympy'] = {
                'enabled': True,
                'success_rate': self._calc_success_rate('sympy')
            }

        if self.wolfram:
            stats['wolfram'] = self.wolfram.get_stats()
            stats['wolfram']['success_rate'] = self._calc_success_rate('wolfram')

        if self.llm:
            stats['llm'] = self.llm.get_stats()
            stats['llm']['success_rate'] = self._calc_success_rate('llm')

        # Add cache stats
        if self.cache_enabled and self.cache:
            stats['cache'] = self.cache.get_stats()

        return stats

    def _calc_success_rate(self, layer: str) -> float:
        """Calculate success rate for a layer."""
        if self.stats['total_queries'] == 0:
            return 0.0

        successes = self.stats.get(f'{layer}_successes', 0)
        return (successes / self.stats['total_queries']) * 100

    def print_stats(self):
        """Print formatted statistics."""
        print("\n" + "=" * 70)
        print("HOLY CALCULATOR - CASCADE STATISTICS")
        print("=" * 70)

        # Engine stats
        print("\n📊 ENGINE STATISTICS:")
        print(f"   Total queries: {self.stats['total_queries']}")
        print(f"   Successful: {self.stats['total_queries'] - self.stats['total_failures']}")
        print(f"   Failed: {self.stats['total_failures']}")
        print(f"   Avg response time: {self.stats['avg_response_time']:.2f}s")
        print(f"   Cascade triggered: {self.stats['cascade_triggered']} times")

        # Layer breakdown
        print("\n🎯 LAYER PERFORMANCE:")
        print(f"   Layer 1 (SymPy):   {self.stats['sympy_successes']:3d} successes "
              f"({self._calc_success_rate('sympy'):5.1f}%)")

        if self.wolfram_enabled:
            print(f"   Layer 2 (Wolfram): {self.stats['wolfram_successes']:3d} successes "
                  f"({self._calc_success_rate('wolfram'):5.1f}%)")
        else:
            print(f"   Layer 2 (Wolfram): DISABLED")

        print(f"   Layer 3 (LLM):     {self.stats['llm_successes']:3d} successes "
              f"({self._calc_success_rate('llm'):5.1f}%)")

        # Cache statistics
        if self.cache_enabled and self.cache:
            print("\n💾 CACHE STATISTICS:")
            cache_stats = self.cache.get_stats()
            print(f"   Hits:        {cache_stats['hits']} ({cache_stats['hit_rate']}%)")
            print(f"   Misses:      {cache_stats['misses']}")
            print(f"   Memory:      {cache_stats['memory_entries']} entries")
            print(f"   Disk:        {cache_stats['disk_entries']} entries ({cache_stats['disk_size_mb']} MB)")

        # Overall success rate
        if self.stats['total_queries'] > 0:
            overall_rate = ((self.stats['total_queries'] - self.stats['total_failures']) /
                          self.stats['total_queries'] * 100)
            print(f"\n   Overall success rate: {overall_rate:.1f}%")

        print("=" * 70 + "\n")


def main():
    """Test the calculator engine."""
    import logging
    logging.basicConfig(level=logging.INFO)

    print("🧪 Testing Holy Calculator Engine\n")

    # Initialize engine
    try:
        engine = CalculatorEngine(enable_wolfram=False)  # Disable Wolfram for quick test
    except Exception as e:
        print(f"❌ Failed to initialize engine: {e}")
        return

    # Test queries
    test_queries = [
        "Solve for x: 2x + 5 = 13",  # Should hit SymPy
        "What is the derivative of x^2 + 3x?",  # Should hit SymPy
        "Convert 100 fahrenheit to celsius",  # Would hit Wolfram if enabled
        "Explain why the square root of 2 is irrational",  # Should hit LLM
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}: {query}")
        print('='*70)

        result = engine.solve(query)

        if result['success']:
            print(f"✓ SUCCESS")
            print(f"  Source: {result['source']}")
            print(f"  Time: {result['response_time']:.2f}s")
            print(f"  Cascade: {' → '.join(result['cascade_path'])}")
            if result.get('from_cache'):
                print(f"  [CACHED RESULT]")
            result_text = result['result'] if result['result'] else "[No result text]"
            print(f"  Result: {result_text[:200]}...")
        else:
            print(f"✗ FAILED")
            print(f"  Error: {result['error']}")
            print(f"  Tried: {' → '.join(result['cascade_path'])}")

    # Show statistics
    engine.print_stats()


if __name__ == "__main__":
    main()
