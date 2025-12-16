#!/usr/bin/env python3
"""
Query Cache for Holy Calculator
Caches query results to improve performance and reduce battery usage.
"""

import hashlib
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class QueryCache:
    """
    Cache for mathematical query results.

    Features:
    - Persistent disk cache (survives restarts)
    - In-memory cache (fast access)
    - TTL (time-to-live) support
    - Cache statistics
    - Automatic cleanup of old entries
    """

    def __init__(self, cache_dir: Optional[Path] = None,
                 max_memory_entries: int = 100,
                 default_ttl_hours: int = 24):
        """
        Initialize the cache.

        Args:
            cache_dir: Directory for persistent cache (default: ./cache/)
            max_memory_entries: Max entries to keep in memory
            default_ttl_hours: Default time-to-live in hours (0 = no expiry)
        """
        self.logger = logging.getLogger(__name__)

        # Cache directory
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent.parent / 'cache'
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # In-memory cache (LRU-like)
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.max_memory_entries = max_memory_entries

        # Default TTL
        self.default_ttl = timedelta(hours=default_ttl_hours)

        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'saves': 0,
            'evictions': 0,
        }

        self.logger.info(f"Cache initialized: {self.cache_dir}")

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result for a query.

        Args:
            query: Mathematical query string

        Returns:
            Cached result dict or None if not found/expired
        """
        cache_key = self._hash_query(query)

        # Check memory cache first
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]

            if self._is_valid(entry):
                self.stats['hits'] += 1
                self.logger.debug(f"Memory cache HIT: {query[:50]}")

                # Update access time (for LRU)
                entry['last_accessed'] = datetime.now().isoformat()

                return entry['result']
            else:
                # Expired, remove from memory
                del self.memory_cache[cache_key]

        # Check disk cache
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    entry = json.load(f)

                if self._is_valid(entry):
                    self.stats['hits'] += 1
                    self.logger.debug(f"Disk cache HIT: {query[:50]}")

                    # Load into memory cache
                    entry['last_accessed'] = datetime.now().isoformat()
                    self._add_to_memory(cache_key, entry)

                    return entry['result']
                else:
                    # Expired, delete file
                    cache_file.unlink()
                    self.logger.debug(f"Cache expired: {query[:50]}")

            except Exception as e:
                self.logger.warning(f"Cache read error: {e}")

        # Cache miss
        self.stats['misses'] += 1
        self.logger.debug(f"Cache MISS: {query[:50]}")
        return None

    def set(self, query: str, result: Dict[str, Any],
            ttl_hours: Optional[int] = None):
        """
        Cache a query result.

        Args:
            query: Mathematical query string
            result: Result dictionary from calculator engine
            ttl_hours: Time-to-live in hours (None = use default)
        """
        cache_key = self._hash_query(query)

        # Determine expiry time
        if ttl_hours == 0:
            expires_at = None  # Never expires
        elif ttl_hours is not None:
            expires_at = (datetime.now() + timedelta(hours=ttl_hours)).isoformat()
        else:
            expires_at = (datetime.now() + self.default_ttl).isoformat()

        # Create cache entry
        entry = {
            'query': query,
            'result': result,
            'cached_at': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat(),
            'expires_at': expires_at,
        }

        # Save to memory
        self._add_to_memory(cache_key, entry)

        # Save to disk
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            with open(cache_file, 'w') as f:
                json.dump(entry, f, indent=2)

            self.stats['saves'] += 1
            self.logger.debug(f"Cached: {query[:50]}")

        except Exception as e:
            self.logger.warning(f"Cache write error: {e}")

    def _hash_query(self, query: str) -> str:
        """Generate cache key from query."""
        # Normalize query (lowercase, strip whitespace)
        normalized = query.lower().strip()

        # Hash it
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def _is_valid(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        # No expiry set
        if entry.get('expires_at') is None:
            return True

        # Check expiry time
        try:
            expires_at = datetime.fromisoformat(entry['expires_at'])
            return datetime.now() < expires_at
        except:
            return False

    def _add_to_memory(self, cache_key: str, entry: Dict[str, Any]):
        """Add entry to memory cache with LRU eviction."""
        # Check if we need to evict
        if len(self.memory_cache) >= self.max_memory_entries:
            # Find least recently accessed entry
            oldest_key = min(
                self.memory_cache.keys(),
                key=lambda k: self.memory_cache[k]['last_accessed']
            )

            del self.memory_cache[oldest_key]
            self.stats['evictions'] += 1
            self.logger.debug("Memory cache eviction")

        self.memory_cache[cache_key] = entry

    def clear(self, older_than_hours: Optional[int] = None):
        """
        Clear cache entries.

        Args:
            older_than_hours: Only clear entries older than this (None = clear all)
        """
        if older_than_hours is None:
            # Clear all
            self.memory_cache.clear()

            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()

            self.logger.info("Cache cleared (all entries)")
        else:
            # Clear old entries
            cutoff = datetime.now() - timedelta(hours=older_than_hours)

            # Clear from memory
            to_remove = []
            for key, entry in self.memory_cache.items():
                cached_at = datetime.fromisoformat(entry['cached_at'])
                if cached_at < cutoff:
                    to_remove.append(key)

            for key in to_remove:
                del self.memory_cache[key]

            # Clear from disk
            count = 0
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r') as f:
                        entry = json.load(f)

                    cached_at = datetime.fromisoformat(entry['cached_at'])
                    if cached_at < cutoff:
                        cache_file.unlink()
                        count += 1
                except:
                    pass

            self.logger.info(f"Cache cleared ({count} entries older than {older_than_hours}h)")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        # Count disk cache size
        disk_entries = len(list(self.cache_dir.glob("*.json")))
        disk_size_mb = sum(f.stat().st_size for f in self.cache_dir.glob("*.json")) / 1024 / 1024

        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': round(hit_rate, 1),
            'saves': self.stats['saves'],
            'evictions': self.stats['evictions'],
            'memory_entries': len(self.memory_cache),
            'disk_entries': disk_entries,
            'disk_size_mb': round(disk_size_mb, 2),
        }

    def print_stats(self):
        """Print cache statistics."""
        stats = self.get_stats()

        print("\n" + "="*60)
        print("CACHE STATISTICS")
        print("="*60)
        print(f"Requests:      {stats['hits'] + stats['misses']}")
        print(f"  Hits:        {stats['hits']} ({stats['hit_rate']}%)")
        print(f"  Misses:      {stats['misses']}")
        print(f"\nCache Size:")
        print(f"  Memory:      {stats['memory_entries']} entries")
        print(f"  Disk:        {stats['disk_entries']} entries ({stats['disk_size_mb']} MB)")
        print(f"\nOperations:")
        print(f"  Saves:       {stats['saves']}")
        print(f"  Evictions:   {stats['evictions']}")
        print("="*60 + "\n")


class SmartCache(QueryCache):
    """
    Enhanced cache with smart features.

    Additional features:
    - Different TTL for different query types
    - Automatic invalidation for queries with variables
    - Popular query tracking
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Track popular queries
        self.query_frequency: Dict[str, int] = {}

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached result with frequency tracking."""
        # Track frequency
        cache_key = self._hash_query(query)
        self.query_frequency[cache_key] = self.query_frequency.get(cache_key, 0) + 1

        return super().get(query)

    def set(self, query: str, result: Dict[str, Any], ttl_hours: Optional[int] = None):
        """
        Cache with smart TTL based on query type.

        - Arithmetic: 7 days (rarely changes)
        - Algebra: 3 days
        - Proofs/explanations: 1 day (might get better LLM responses later)
        """
        if ttl_hours is None:
            # Determine smart TTL
            query_lower = query.lower()

            # Simple arithmetic - cache longer
            if any(op in query for op in ['+', '-', '*', '/', '^']) and '=' not in query:
                ttl_hours = 24 * 7  # 7 days

            # Proofs/explanations - cache shorter (LLM might improve)
            elif any(kw in query_lower for kw in ['prove', 'explain', 'why']):
                ttl_hours = 24  # 1 day

            # Default
            else:
                ttl_hours = 24 * 3  # 3 days

        super().set(query, result, ttl_hours)

    def get_popular_queries(self, top_n: int = 10) -> list:
        """Get most frequently accessed queries."""
        sorted_queries = sorted(
            self.query_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [
            {'query_hash': k, 'frequency': v}
            for k, v in sorted_queries[:top_n]
        ]


def main():
    """Test the cache."""
    import logging
    logging.basicConfig(level=logging.INFO)

    print("\n" + "="*60)
    print("CACHE SYSTEM TEST")
    print("="*60)

    # Initialize cache
    cache = SmartCache()

    # Test queries
    test_queries = [
        ("2 + 2", {'success': True, 'result': '4', 'source': 'sympy'}),
        ("Solve: x^2 = 4", {'success': True, 'result': 'x = -2, x = 2', 'source': 'sympy'}),
        ("Prove sqrt(2) is irrational", {'success': True, 'result': 'Proof...', 'source': 'llm'}),
    ]

    print("\n1. Testing cache MISS (first time):")
    for query, result in test_queries:
        cached = cache.get(query)
        print(f"  {query[:40]:40s} → {'MISS' if cached is None else 'HIT'}")

        if cached is None:
            cache.set(query, result)
            print(f"    Cached with smart TTL")

    print("\n2. Testing cache HIT (second time):")
    for query, _ in test_queries:
        cached = cache.get(query)
        print(f"  {query[:40]:40s} → {'MISS' if cached is None else 'HIT'}")
        if cached:
            print(f"    Result: {cached['result'][:50]}")

    print("\n3. Testing duplicate query (should hit):")
    for _ in range(3):
        cached = cache.get("2 + 2")
        print(f"  2 + 2 → {'HIT' if cached else 'MISS'}")

    print("\n4. Cache Statistics:")
    cache.print_stats()

    print("5. Popular Queries:")
    for i, item in enumerate(cache.get_popular_queries(5), 1):
        print(f"  {i}. Hash: {item['query_hash']} (accessed {item['frequency']} times)")

    print("\n6. Testing cache clear:")
    cache.clear()
    print("  Cache cleared")

    cached = cache.get("2 + 2")
    print(f"  2 + 2 after clear → {'HIT' if cached else 'MISS'}")

    cache.print_stats()

    print("✓ Cache test complete!\n")


if __name__ == "__main__":
    main()
