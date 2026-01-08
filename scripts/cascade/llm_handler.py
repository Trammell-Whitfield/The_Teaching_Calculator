#!/usr/bin/env python3
"""
LLM Handler - Layer 3 fallback using Qwen2.5-Math-7B-Instruct.

Handles complex reasoning, word problems, and explanations that
require deep mathematical understanding.
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
    Handles mathematical queries using Qwen2.5-Math-7B-Instruct via llama.cpp.

    Specializes in reasoning, proofs, word problems, and multi-step solutions.
    """

    def __init__(self, model_path: Optional[str] = None, llama_cpp_path: Optional[str] = None):
        """Initialize the LLM handler with model and binary paths."""
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
            'repeat_penalty': 1.15,  # Increased from 1.1 to prevent repetitive loops
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

            # Debug: Print raw output to help diagnose extraction issues
            if os.environ.get('DEBUG_LLM'):
                print(f"\n{'='*70}")
                print("RAW LLM OUTPUT:")
                print(f"{'='*70}")
                print(full_output)
                print(f"{'='*70}\n")

            # Extract answer using multiple patterns
            answer = self._extract_answer(full_output)

            # If extraction failed, log it for debugging
            if answer is None:
                print(f"⚠ WARNING: Failed to extract answer from LLM output")
                print(f"Last 200 characters: {full_output[-200:]}")
                # Return full output as fallback
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

    def _extract_answer(self, text: str) -> Optional[str]:
        """
        Extract mathematical answer from LLM output using multiple patterns.

        Tries various common answer formats used by math LLMs:
        - "The answer is: X"
        - "#### X" (GSM8K format)
        - "\\boxed{X}" (LaTeX format)
        - "Therefore, X"
        - "Solution: X"
        - "= X" (equation format)

        Args:
            text: Raw LLM output

        Returns:
            Extracted answer string, or None if no pattern matches
        """
        # List of patterns to try, in order of preference
        patterns = [
            # Explicit answer markers
            r"(?:The answer is|Answer:|Final answer:)\s*\**\s*([^\n]+)",
            r"####\s*([^\n]+)",  # GSM8K format
            r"\\boxed\{([^}]+)\}",  # LaTeX boxed format

            # Common conclusion phrases
            r"Therefore,?\s+([^\n.]+)[.\n]",
            r"Thus,?\s+([^\n.]+)[.\n]",
            r"So,?\s+([^\n.]+)[.\n]",

            # Solution markers
            r"Solution:\s*([^\n]+)",
            r"Result:\s*([^\n]+)",

            # Equation format (equals sign)
            r"=\s*([0-9.x\-+*/^()]+)\s*(?:\n|$)",

            # Last resort: look for conclusion after steps
            r"Step \d+.*?\n\s*([^\n]+)$",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                answer = match.group(1).strip()
                # Remove asterisks (markdown bold)
                answer = answer.strip('*')
                # Remove trailing periods
                answer = answer.rstrip('.')

                if os.environ.get('DEBUG_LLM'):
                    print(f"✓ Extracted answer using pattern: {pattern[:50]}...")
                    print(f"  Answer: {answer}")

                return answer

        # No pattern matched
        if os.environ.get('DEBUG_LLM'):
            print(f"✗ No extraction pattern matched")

        return None

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
