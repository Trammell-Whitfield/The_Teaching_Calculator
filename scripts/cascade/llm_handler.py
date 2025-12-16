#!/usr/bin/env python3
"""
LLM Handler - Layer 3 of the Holy Calculator Cascade
Handles complex reasoning and word problems using Qwen2.5-Math-7B-Instruct (Phase 7.5)

This is the final fallback layer for queries that SymPy and Wolfram cannot handle.
Upgraded from DeepSeek-Math to Qwen2.5-Math for superior mathematical reasoning.
"""

import subprocess
import os
import re
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from platform_config import PlatformConfig


class LLMHandler:
    """
    Handles mathematical queries using Qwen2.5-Math-7B-Instruct LLM via llama.cpp.

    Phase 7.5 Upgrade: Switched from DeepSeek-Math to Qwen2.5-Math
    - 83.6% accuracy on MATH benchmark (vs DeepSeek's ~55%)
    - 91.6% accuracy on GSM8K benchmark (vs DeepSeek's ~82%)
    - State-of-the-art 7B mathematical reasoning model

    Capabilities:
    - Mathematical reasoning and proofs
    - Word problems requiring interpretation
    - Multi-step problem solving
    - Conceptual explanations
    - Problems that require context understanding
    """

    def __init__(self, model_path: Optional[str] = None, llama_cpp_path: Optional[str] = None):
        """
        Initialize the LLM handler.

        Args:
            model_path: Path to GGUF model file (auto-detects if None)
            llama_cpp_path: Path to llama-cli binary (auto-detects if None)
        """
        # Detect platform and get optimized configuration
        self.platform_config = PlatformConfig()

        # Find model path (use platform preference if not specified)
        if model_path is None:
            model_path = self._find_model()

        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        # Find llama.cpp binary
        if llama_cpp_path is None:
            llama_cpp_path = self._find_llama_cli()

        self.llama_cli = Path(llama_cpp_path)
        if not self.llama_cli.exists():
            raise FileNotFoundError(f"llama-cli binary not found: {llama_cpp_path}")

        # Platform-optimized inference parameters
        platform_params = self.platform_config.get_llm_params()
        self.default_params = {
            'n_predict': platform_params['n_predict'],
            'temperature': platform_params['temperature'],
            'top_p': 0.9,
            'top_k': 40,
            'repeat_penalty': 1.1,
            'threads': platform_params['n_threads'],
            'n_ctx': platform_params.get('n_ctx', 2048),
        }

        # Statistics
        self.stats = {
            'queries_processed': 0,
            'avg_response_time': 0,
            'total_tokens_generated': 0,
        }

    def _find_model(self) -> str:
        """
        Auto-detect the model file using platform-aware preferences.

        Platform detection ensures optimal model selection:
        - Pi with 16GB RAM: Prefers Q5_K_M for quality
        - Pi with 8GB RAM: Prefers Q4_K_M for reliability
        - Desktop/Laptop: Prefers Q5_K_M if available
        """
        # Look in standard location
        base_dir = Path(__file__).parent.parent.parent
        quantized_dir = base_dir / 'models' / 'quantized'

        # Get platform-specific model preference
        preferred_models = self.platform_config.get_model_preference()

        for model_name in preferred_models:
            model_path = quantized_dir / model_name
            if model_path.exists():
                return str(model_path)

        raise FileNotFoundError(
            "No quantized model found. Please ensure you've completed Phase 2 "
            "(model quantization)."
        )

    def _find_llama_cli(self) -> str:
        """Auto-detect llama-cli binary."""
        base_dir = Path(__file__).parent.parent.parent
        llama_cli = base_dir / 'llama.cpp' / 'build' / 'bin' / 'llama-cli'

        if llama_cli.exists():
            return str(llama_cli)

        raise FileNotFoundError(
            "llama-cli binary not found. Please ensure you've built llama.cpp "
            "(see Phase 1 documentation)."
        )

    def can_handle(self, query: str) -> bool:
        """
        LLM can handle everything as the final fallback.

        Args:
            query: User query string

        Returns:
            Always True (LLM is the catch-all layer)
        """
        return True

    def _build_prompt(self, query: str) -> str:
        """
        Build the prompt for the LLM with proper formatting.

        DeepSeek-Math expects a structured prompt for best results.

        Args:
            query: User's mathematical query

        Returns:
            Formatted prompt string
        """
        # DeepSeek-Math instruction format
        prompt = f"""You are a mathematical problem solver. Solve the following problem step by step.

Problem: {query}

Solution:"""

        return prompt

    def process_query(self, query: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Process a mathematical query using the LLM.

        Args:
            query: User's mathematical query
            **kwargs: Override default inference parameters

        Returns:
            Dictionary with result and metadata, or None if processing fails
        """
        self.stats['queries_processed'] += 1

        # Build prompt
        prompt = self._build_prompt(query)

        # Merge custom params with defaults
        params = {**self.default_params, **kwargs}

        # Build llama.cpp command
        cmd = [
            str(self.llama_cli),
            '-m', str(self.model_path),
            '-p', prompt,
            '-n', str(params['n_predict']),
            '-c', str(params.get('n_ctx', 2048)),  # Context window
            '--temp', str(params['temperature']),
            '--top-p', str(params['top_p']),
            '--top-k', str(params['top_k']),
            '--repeat-penalty', str(params['repeat_penalty']),
            '-t', str(params['threads']),
            '--log-disable',  # Disable llama.cpp logging for cleaner output
        ]

        try:
            # Run llama.cpp
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )

            if result.returncode != 0:
                return {
                    'success': False,
                    'error': f"LLM inference failed: {result.stderr}",
                    'source': 'llm'
                }

            # Extract the response (llama.cpp outputs the prompt + completion)
            full_output = result.stdout

            # Try to extract just the answer part (after "Solution:")
            if 'Solution:' in full_output:
                answer = full_output.split('Solution:', 1)[1].strip()
            else:
                answer = full_output.strip()

            # Extract basic metadata (tokens generated)
            tokens_generated = len(answer.split())  # Rough estimate
            self.stats['total_tokens_generated'] += tokens_generated

            return {
                'success': True,
                'result': answer,
                'source': 'llm',
                'model': self.model_path.name,
                'tokens_generated': tokens_generated,
                'error': None
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'LLM inference timed out (>120s)',
                'source': 'llm'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"LLM error: {str(e)}",
                'source': 'llm'
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get handler statistics."""
        return self.stats.copy()

    def print_stats(self):
        """Print formatted statistics."""
        print("\n" + "=" * 60)
        print("LLM Handler Statistics")
        print("=" * 60)
        print(f"Model: {self.model_path.name}")
        print(f"Queries processed: {self.stats['queries_processed']}")
        print(f"Total tokens generated: {self.stats['total_tokens_generated']}")
        if self.stats['queries_processed'] > 0:
            avg_tokens = self.stats['total_tokens_generated'] / self.stats['queries_processed']
            print(f"Avg tokens per query: {avg_tokens:.1f}")
        print("=" * 60 + "\n")


def main():
    """Test LLM handler."""
    print("🧪 Testing LLM Handler\n")

    try:
        handler = LLMHandler()
        print(f"✓ Model loaded: {handler.model_path.name}")
        print(f"✓ llama.cpp: {handler.llama_cli}\n")
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return

    # Test queries
    test_queries = [
        "What is 2 + 2?",
        "Solve for x: 2x + 5 = 13",
        "Explain why the square root of 2 is irrational",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\nQuery {i}: {query}")
        print("-" * 60)

        result = handler.process_query(query, n_predict=200)

        if result['success']:
            print(f"✓ Result ({result['source']}):")
            print(result['result'])
            print(f"\nTokens: {result['tokens_generated']}")
        else:
            print(f"✗ Failed: {result['error']}")

    # Show statistics
    handler.print_stats()


if __name__ == "__main__":
    main()
