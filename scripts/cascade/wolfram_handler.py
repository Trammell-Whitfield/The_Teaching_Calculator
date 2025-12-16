#!/usr/bin/env python3
"""
Wolfram Alpha Handler
Layer 2 of the Holy Calculator cascade system
"""

import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# Import our custom modules
import sys
sys.path.insert(0, str(Path(__file__).parent))
from wolfram_cache import WolframCache
from usage_tracker import UsageTracker


class WolframAlphaHandler:
    """
    Wolfram Alpha API handler with caching and rate limiting.

    Strategy:
    1. Check cache first (avoid API call if possible)
    2. Check usage quota (hard stop if exceeded)
    3. Try Simple Result API (fastest)
    4. If unclear/error, try Short Answers API (more detailed)
    5. Cache result for future use
    6. Record usage

    API Endpoints:
    - Simple Result: Returns plain text answer (fastest)
    - Short Answers: Returns formatted result with units (fallback)
    """

    # API endpoints
    SIMPLE_API_URL = "http://api.wolframalpha.com/v1/result"
    SHORT_API_URL = "http://api.wolframalpha.com/v1/conversation.jsp"

    # Timeout settings
    TIMEOUT_SECONDS = 10

    def __init__(self, api_key=None, cache_dir=None, usage_file=None):
        """
        Initialize Wolfram Alpha handler.

        Args:
            api_key: Wolfram Alpha App ID (loads from .env if not provided)
            cache_dir: Cache directory path
            usage_file: Usage tracking file path
        """
        # Load environment variables
        load_dotenv()

        # Get API key
        self.api_key = api_key or os.getenv('WOLFRAM_ALPHA_API_KEY')

        if not self.api_key or self.api_key == 'your_api_key_here':
            raise ValueError(
                "Wolfram Alpha API key not found. "
                "Please set WOLFRAM_ALPHA_API_KEY in .env file."
            )

        # Initialize cache and usage tracker
        self.cache = WolframCache(cache_dir=cache_dir)
        self.usage = UsageTracker(usage_file=usage_file)

        # Statistics for current session
        self.stats = {
            "queries_processed": 0,
            "cache_hits": 0,
            "api_calls_simple": 0,
            "api_calls_short": 0,
            "api_errors": 0,
            "quota_blocked": 0
        }

    def can_handle(self, query):
        """
        Determine if Wolfram Alpha can handle this query.

        Wolfram Alpha is good for:
        - Calculations and algebra
        - Unit conversions
        - Scientific constants
        - Statistical calculations
        - Chemistry/physics questions
        - Definite integrals
        - Word problems with clear mathematical content

        Args:
            query: User query string

        Returns:
            bool: True if Wolfram can likely handle it
        """
        # Keywords that suggest Wolfram Alpha can help
        wolfram_keywords = [
            "calculate", "compute", "convert", "what is",
            "how much", "how many", "solve", "find",
            "integrate", "derivative", "limit",
            "speed of", "mass of", "weight of",
            "molecular", "atomic", "chemical",
            "standard deviation", "mean", "average",
            "probability", "statistics"
        ]

        query_lower = query.lower()

        # Check for keywords
        for keyword in wolfram_keywords:
            if keyword in query_lower:
                return True

        # Check for mathematical operators
        math_operators = ['+', '-', '*', '/', '^', '=', '<', '>']
        if any(op in query for op in math_operators):
            return True

        # Default: let Wolfram try (it's quite capable)
        return True

    def process_query(self, query, is_dev=True, force=False):
        """
        Process a query through Wolfram Alpha (main entry point).

        Flow:
        1. Check cache
        2. Check quota
        3. Try Simple API
        4. Fallback to Short API if needed
        5. Cache result
        6. Update statistics

        Args:
            query: User query string
            is_dev: True for development mode, False for production
            force: Override quota limits (USE WITH CAUTION)

        Returns:
            dict: Result with metadata
            {
                "success": bool,
                "result": str or None,
                "source": "cache" | "simple_api" | "short_api" | "error",
                "error": str or None
            }
        """
        self.stats["queries_processed"] += 1

        # Step 1: Check cache
        cached = self.cache.get(query)
        if cached:
            self.stats["cache_hits"] += 1
            return {
                "success": True,
                "result": cached["result"],
                "source": "cache",
                "cached_at": cached.get("timestamp"),
                "api_used": cached.get("api_used"),
                "error": None
            }

        # Step 2: Check quota
        can_query, reason = self.usage.can_make_query(is_dev=is_dev, force=force)
        if not can_query:
            self.stats["quota_blocked"] += 1
            return {
                "success": False,
                "result": None,
                "source": "quota_exceeded",
                "error": reason
            }

        # Step 3: Try Simple Result API (primary)
        simple_result = self._query_simple(query)

        if simple_result["success"]:
            # Cache and record usage
            self.cache.set(query, simple_result["result"], api_used="simple")
            self.usage.record_query(is_dev=is_dev, force=force)
            self.stats["api_calls_simple"] += 1

            return {
                "success": True,
                "result": simple_result["result"],
                "source": "simple_api",
                "error": None
            }

        # Step 4: Fallback to Short Answers API
        short_result = self._query_short(query)

        if short_result["success"]:
            # Cache and record usage
            self.cache.set(query, short_result["result"], api_used="short")
            self.usage.record_query(is_dev=is_dev, force=force)
            self.stats["api_calls_short"] += 1

            return {
                "success": True,
                "result": short_result["result"],
                "source": "short_api",
                "error": None
            }

        # Both APIs failed
        self.stats["api_errors"] += 1
        return {
            "success": False,
            "result": None,
            "source": "error",
            "error": short_result.get("error", "Unknown error")
        }

    def _query_simple(self, query):
        """
        Query Simple Result API (fastest, returns plain text).

        Args:
            query: User query string

        Returns:
            dict: {"success": bool, "result": str or None, "error": str or None}
        """
        params = {
            'appid': self.api_key,
            'i': query
        }

        try:
            response = requests.get(
                self.SIMPLE_API_URL,
                params=params,
                timeout=self.TIMEOUT_SECONDS
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "result": response.text.strip(),
                    "error": None
                }
            elif response.status_code == 501:
                # Wolfram doesn't understand the query
                return {
                    "success": False,
                    "result": None,
                    "error": "Wolfram Alpha could not interpret the query"
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "result": None,
                    "error": "Invalid API key"
                }
            elif response.status_code == 403:
                return {
                    "success": False,
                    "result": None,
                    "error": "API access forbidden (check your API key permissions)"
                }
            else:
                return {
                    "success": False,
                    "result": None,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "result": None,
                "error": "Request timed out"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "result": None,
                "error": f"Network error: {str(e)}"
            }

    def _query_short(self, query):
        """
        Query Short Answers API (fallback, more detailed).

        Args:
            query: User query string

        Returns:
            dict: {"success": bool, "result": str or None, "error": str or None}
        """
        params = {
            'appid': self.api_key,
            'i': query,
            'geolocation': 'US',  # Optional: helps with some queries
        }

        try:
            response = requests.get(
                self.SHORT_API_URL,
                params=params,
                timeout=self.TIMEOUT_SECONDS
            )

            if response.status_code == 200:
                # Short API returns more detailed response
                result = response.text.strip()

                # Filter out error messages
                if "Wolfram Alpha did not understand" in result:
                    return {
                        "success": False,
                        "result": None,
                        "error": "Wolfram Alpha could not interpret the query"
                    }

                return {
                    "success": True,
                    "result": result,
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "result": None,
                    "error": f"HTTP {response.status_code}"
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "result": None,
                "error": "Request timed out"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "result": None,
                "error": f"Network error: {str(e)}"
            }

    def get_stats(self):
        """Get handler statistics."""
        cache_stats = self.cache.get_stats()
        usage_stats = self.usage.get_usage_stats()

        return {
            "session": self.stats,
            "cache": cache_stats,
            "usage": usage_stats
        }

    def print_stats(self):
        """Print formatted statistics."""
        stats = self.get_stats()

        print("\n" + "=" * 60)
        print("Wolfram Alpha Handler Statistics")
        print("=" * 60)

        print("\n📊 SESSION STATISTICS:")
        print(f"   Queries processed: {stats['session']['queries_processed']}")
        print(f"   Cache hits: {stats['session']['cache_hits']}")
        print(f"   Simple API calls: {stats['session']['api_calls_simple']}")
        print(f"   Short API calls: {stats['session']['api_calls_short']}")
        print(f"   API errors: {stats['session']['api_errors']}")
        print(f"   Quota blocks: {stats['session']['quota_blocked']}")

        total_api_calls = stats['session']['api_calls_simple'] + stats['session']['api_calls_short']
        if stats['session']['queries_processed'] > 0:
            cache_rate = (stats['session']['cache_hits'] / stats['session']['queries_processed']) * 100
            print(f"   Cache hit rate: {cache_rate:.1f}%")

        print(f"\n💾 CACHE:")
        print(f"   Total cached: {stats['cache']['total_cached']} queries")
        print(f"   Cache file size: {stats['cache']['cache_size_bytes']:,} bytes")

        print(f"\n📈 USAGE (Development Budget):")
        print(f"   Used: {stats['usage']['development']['used']}/{stats['usage']['development']['budget']}")
        print(f"   Remaining: {stats['usage']['development']['remaining']}")

        print("=" * 60 + "\n")


def main():
    """Test Wolfram Alpha handler."""
    print("🧪 Testing Wolfram Alpha Handler\n")

    try:
        handler = WolframAlphaHandler()
    except ValueError as e:
        print(f"❌ Error: {e}")
        return

    # Test queries
    test_queries = [
        "What is 2+2?",
        "What is the speed of light in m/s?",
        "Convert 100 fahrenheit to celsius",
        "What is 2+2?",  # Should hit cache
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\nQuery {i}: {query}")

        result = handler.process_query(query, is_dev=True)

        if result["success"]:
            print(f"✓ Success ({result['source']}): {result['result']}")
        else:
            print(f"✗ Failed ({result['source']}): {result['error']}")

    # Show statistics
    handler.print_stats()


if __name__ == "__main__":
    main()
