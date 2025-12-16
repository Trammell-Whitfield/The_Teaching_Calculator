#!/usr/bin/env python3
"""
Wolfram Alpha Query Cache
Stores API results indefinitely to minimize API calls
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path


class WolframCache:
    """
    Cache for Wolfram Alpha API results.

    Design:
    - Indefinite caching (math answers don't change)
    - Query normalization (case-insensitive, whitespace trimmed)
    - Hash-based lookup for fast retrieval
    - JSON storage for human readability
    """

    def __init__(self, cache_dir=None):
        """
        Initialize cache.

        Args:
            cache_dir: Path to cache directory (default: data/cache/wolfram)
        """
        if cache_dir is None:
            project_root = Path(__file__).parent.parent.parent
            cache_dir = project_root / "data" / "cache" / "wolfram"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.cache_file = self.cache_dir / "query_cache.json"
        self.cache_data = self._load_cache()

        # Statistics
        self.hits = 0
        self.misses = 0

    def _load_cache(self):
        """Load cache from disk or create new."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # Corrupted cache, start fresh
                return {}
        else:
            return {}

    def _save_cache(self):
        """Save cache to disk."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache_data, f, indent=2, sort_keys=True)
        except IOError as e:
            print(f"⚠️  Warning: Could not save cache: {e}")

    def _normalize_query(self, query):
        """
        Normalize query for consistent cache lookups.

        Args:
            query: Raw query string

        Returns:
            str: Normalized query (lowercase, trimmed)
        """
        return query.strip().lower()

    def _hash_query(self, query):
        """
        Create hash of normalized query for cache key.

        Args:
            query: Query string

        Returns:
            str: SHA256 hash (first 16 chars for readability)
        """
        normalized = self._normalize_query(query)
        hash_obj = hashlib.sha256(normalized.encode('utf-8'))
        return hash_obj.hexdigest()[:16]

    def get(self, query):
        """
        Retrieve cached result for query.

        Args:
            query: Query string

        Returns:
            dict or None: Cached result with metadata, or None if not cached
        """
        cache_key = self._hash_query(query)

        if cache_key in self.cache_data:
            self.hits += 1
            return self.cache_data[cache_key]
        else:
            self.misses += 1
            return None

    def set(self, query, result, api_used="simple", metadata=None):
        """
        Store query result in cache.

        Args:
            query: Original query string
            result: API result (string or dict)
            api_used: Which API was used ("simple" or "short")
            metadata: Optional additional metadata
        """
        cache_key = self._hash_query(query)

        cache_entry = {
            "query": query,
            "normalized_query": self._normalize_query(query),
            "result": result,
            "api_used": api_used,
            "timestamp": datetime.now().isoformat(),
            "cache_key": cache_key
        }

        if metadata:
            cache_entry["metadata"] = metadata

        self.cache_data[cache_key] = cache_entry
        self._save_cache()

    def has(self, query):
        """
        Check if query exists in cache (without incrementing hit counter).

        Args:
            query: Query string

        Returns:
            bool: True if cached, False otherwise
        """
        cache_key = self._hash_query(query)
        return cache_key in self.cache_data

    def remove(self, query):
        """
        Remove a specific query from cache.

        Args:
            query: Query string

        Returns:
            bool: True if removed, False if not found
        """
        cache_key = self._hash_query(query)

        if cache_key in self.cache_data:
            del self.cache_data[cache_key]
            self._save_cache()
            return True
        else:
            return False

    def clear(self, confirm=False):
        """
        Clear entire cache (USE WITH CAUTION).

        Args:
            confirm: Must be True to actually clear

        Returns:
            bool: True if cleared successfully
        """
        if not confirm:
            print("⚠️  WARNING: clear() requires confirm=True")
            print("   This will delete all cached queries!")
            return False

        self.cache_data = {}
        self._save_cache()

        print("✓ Cache cleared")
        return True

    def get_stats(self):
        """
        Get cache statistics.

        Returns:
            dict: Cache statistics
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "total_cached": len(self.cache_data),
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "cache_file": str(self.cache_file),
            "cache_size_bytes": self.cache_file.stat().st_size if self.cache_file.exists() else 0
        }

    def print_stats(self):
        """Print formatted cache statistics."""
        stats = self.get_stats()

        print("\n" + "=" * 60)
        print("Wolfram Alpha Cache Statistics")
        print("=" * 60)
        print(f"\n📦 CACHE SIZE:")
        print(f"   Total cached queries: {stats['total_cached']}")
        print(f"   File size: {stats['cache_size_bytes']:,} bytes")
        print(f"   Location: {stats['cache_file']}")

        print(f"\n🎯 SESSION STATISTICS:")
        print(f"   Cache hits: {stats['hits']}")
        print(f"   Cache misses: {stats['misses']}")
        print(f"   Total requests: {stats['total_requests']}")
        print(f"   Hit rate: {stats['hit_rate']:.1f}%")

        print("=" * 60 + "\n")

    def list_cached_queries(self, limit=10):
        """
        List recently cached queries.

        Args:
            limit: Maximum number of queries to show

        Returns:
            list: Recent cache entries
        """
        # Sort by timestamp (most recent first)
        sorted_entries = sorted(
            self.cache_data.values(),
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )

        return sorted_entries[:limit]

    def print_cached_queries(self, limit=10):
        """Print list of cached queries."""
        entries = self.list_cached_queries(limit)

        if not entries:
            print("\n📭 Cache is empty\n")
            return

        print(f"\n📋 Recently Cached Queries (showing {len(entries)} of {len(self.cache_data)}):")
        print("=" * 60)

        for i, entry in enumerate(entries, 1):
            timestamp = entry.get("timestamp", "unknown")
            if timestamp != "unknown":
                # Format timestamp for readability
                dt = datetime.fromisoformat(timestamp)
                timestamp = dt.strftime("%Y-%m-%d %H:%M")

            query = entry.get("query", "")[:50]  # Truncate long queries
            result = str(entry.get("result", ""))[:40]  # Truncate long results
            api = entry.get("api_used", "unknown")

            print(f"\n{i}. {query}")
            print(f"   Result: {result}")
            print(f"   API: {api} | Cached: {timestamp}")

        print("=" * 60 + "\n")

    def estimate_hits(self, queries):
        """
        Estimate how many queries will be cache hits.

        Args:
            queries: List of query strings

        Returns:
            dict: Estimation breakdown
        """
        hits = 0
        misses = 0

        for query in queries:
            if self.has(query):
                hits += 1
            else:
                misses += 1

        return {
            "total_queries": len(queries),
            "estimated_hits": hits,
            "estimated_misses": misses,
            "estimated_api_calls": misses,
            "hit_rate": (hits / len(queries) * 100) if queries else 0
        }


def main():
    """Test cache functionality."""
    cache = WolframCache()

    print("🧪 Testing Wolfram Alpha Cache\n")

    # Test 1: Store some queries
    print("Test 1: Storing queries...")
    cache.set("What is 2+2?", "4", api_used="simple")
    cache.set("What is the speed of light?", "299792458 m/s", api_used="simple")
    cache.set("Solve x^2 - 4 = 0", "x = -2, x = 2", api_used="short")
    print("✓ Stored 3 queries\n")

    # Test 2: Retrieve queries (test normalization)
    print("Test 2: Retrieving queries (testing normalization)...")
    result1 = cache.get("what is 2+2?")  # Different case
    result2 = cache.get("  What is 2+2?  ")  # Extra whitespace
    print(f"✓ Query 1 (different case): {result1['result'] if result1 else 'NOT FOUND'}")
    print(f"✓ Query 2 (whitespace): {result2['result'] if result2 else 'NOT FOUND'}\n")

    # Test 3: Cache miss
    print("Test 3: Cache miss...")
    result3 = cache.get("What is 5+5?")
    print(f"✓ Uncached query: {result3 if result3 else 'NOT FOUND (expected)'}\n")

    # Show stats
    cache.print_stats()

    # Show cached queries
    cache.print_cached_queries()

    # Test estimation
    print("📈 Estimation example:")
    test_queries = [
        "What is 2+2?",
        "What is 5+5?",
        "What is the speed of light?",
        "What is 10*10?"
    ]
    estimate = cache.estimate_hits(test_queries)
    print(f"   Total queries: {estimate['total_queries']}")
    print(f"   Estimated hits: {estimate['estimated_hits']}")
    print(f"   Estimated misses: {estimate['estimated_misses']}")
    print(f"   API calls needed: {estimate['estimated_api_calls']}")
    print(f"   Hit rate: {estimate['hit_rate']:.1f}%\n")


if __name__ == "__main__":
    main()
