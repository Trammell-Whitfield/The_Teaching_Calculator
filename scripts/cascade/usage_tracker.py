#!/usr/bin/env python3
"""
Wolfram Alpha API Usage Tracker
Enforces hard limits to protect free tier quota (2,000 queries/month)
"""

import os
import json
from datetime import datetime
from pathlib import Path


class UsageTracker:
    """
    Tracks and enforces Wolfram Alpha API usage limits.

    Budget Structure:
    - Monthly limit: 2,000 queries (Wolfram free tier)
    - Development budget: 1,000 queries
    - Production reserve: 1,000 queries
    """

    # Hard limits
    MONTHLY_LIMIT = 2000
    DEVELOPMENT_BUDGET = 1000
    PRODUCTION_RESERVE = 1000

    # Warning thresholds
    DEV_WARNING_THRESHOLD = 0.90  # Warn at 90% of dev budget
    PROD_WARNING_THRESHOLD = 0.90  # Warn at 90% of prod budget

    def __init__(self, usage_file=None):
        """
        Initialize usage tracker.

        Args:
            usage_file: Path to usage JSON file (default: data/usage/wolfram_usage.json)
        """
        if usage_file is None:
            project_root = Path(__file__).parent.parent.parent
            usage_file = project_root / "data" / "usage" / "wolfram_usage.json"

        self.usage_file = Path(usage_file)
        self.usage_file.parent.mkdir(parents=True, exist_ok=True)

        # Load or initialize usage data
        self.data = self._load_usage()

    def _load_usage(self):
        """Load usage data from file or create new."""
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)

                # Reset if new month
                current_month = datetime.now().strftime("%Y-%m")
                if data.get("current_month") != current_month:
                    data = self._create_new_month_data(current_month)
                    self._save_usage(data)

                return data
            except (json.JSONDecodeError, KeyError):
                # Corrupted file, create new
                return self._create_initial_data()
        else:
            # First time setup
            return self._create_initial_data()

    def _create_initial_data(self):
        """Create initial usage data structure."""
        current_month = datetime.now().strftime("%Y-%m")
        data = self._create_new_month_data(current_month)
        self._save_usage(data)
        return data

    def _create_new_month_data(self, month):
        """Create fresh data structure for new month."""
        return {
            "monthly_limit": self.MONTHLY_LIMIT,
            "development_budget": self.DEVELOPMENT_BUDGET,
            "production_reserve": self.PRODUCTION_RESERVE,
            "current_month": month,
            "total_queries_used": 0,
            "dev_queries_used": 0,
            "prod_queries_used": 0,
            "history": {},
            "last_updated": datetime.now().isoformat()
        }

    def _save_usage(self, data=None):
        """Save usage data to file."""
        if data is None:
            data = self.data

        data["last_updated"] = datetime.now().isoformat()

        with open(self.usage_file, 'w') as f:
            json.dump(data, f, indent=2)

    def can_make_query(self, is_dev=True, force=False):
        """
        Check if we can make an API query without exceeding limits.

        Args:
            is_dev: True for development queries, False for production
            force: Override limits (DANGEROUS - use with extreme caution)

        Returns:
            tuple: (bool, str) - (can_query, reason_if_not)
        """
        if force:
            return True, "FORCED (limit override enabled)"

        # Check monthly limit first
        if self.data["total_queries_used"] >= self.MONTHLY_LIMIT:
            return False, f"MONTHLY LIMIT EXCEEDED ({self.MONTHLY_LIMIT} queries/month)"

        # Check specific budget
        if is_dev:
            if self.data["dev_queries_used"] >= self.DEVELOPMENT_BUDGET:
                return False, f"DEVELOPMENT BUDGET EXCEEDED ({self.DEVELOPMENT_BUDGET} queries)"
        else:
            if self.data["prod_queries_used"] >= self.PRODUCTION_RESERVE:
                return False, f"PRODUCTION RESERVE EXCEEDED ({self.PRODUCTION_RESERVE} queries)"

        return True, "OK"

    def record_query(self, is_dev=True, force=False):
        """
        Record a query after it's been made.

        Args:
            is_dev: True for development queries, False for production
            force: Was this a forced query?

        Returns:
            dict: Updated usage statistics
        """
        # Increment counters
        self.data["total_queries_used"] += 1

        if is_dev:
            self.data["dev_queries_used"] += 1
        else:
            self.data["prod_queries_used"] += 1

        # Record in daily history
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in self.data["history"]:
            self.data["history"][today] = 0
        self.data["history"][today] += 1

        # Save to disk
        self._save_usage()

        # Check for warnings
        self._check_warnings(is_dev)

        return self.get_usage_stats()

    def _check_warnings(self, is_dev=True):
        """Check if we're approaching limits and print warnings."""
        if is_dev:
            budget = self.DEVELOPMENT_BUDGET
            used = self.data["dev_queries_used"]
            threshold = self.DEV_WARNING_THRESHOLD
            budget_name = "DEVELOPMENT"
        else:
            budget = self.PRODUCTION_RESERVE
            used = self.data["prod_queries_used"]
            threshold = self.PROD_WARNING_THRESHOLD
            budget_name = "PRODUCTION"

        percentage_used = used / budget

        if percentage_used >= threshold:
            remaining = budget - used
            print(f"\n⚠️  WARNING: {budget_name} BUDGET AT {percentage_used*100:.1f}%")
            print(f"    Used: {used}/{budget} queries")
            print(f"    Remaining: {remaining} queries")
            print(f"    Approach limit with caution!\n")

    def get_usage_stats(self):
        """
        Get current usage statistics.

        Returns:
            dict: Comprehensive usage statistics
        """
        return {
            "month": self.data["current_month"],
            "total": {
                "used": self.data["total_queries_used"],
                "limit": self.MONTHLY_LIMIT,
                "remaining": self.MONTHLY_LIMIT - self.data["total_queries_used"],
                "percentage": (self.data["total_queries_used"] / self.MONTHLY_LIMIT) * 100
            },
            "development": {
                "used": self.data["dev_queries_used"],
                "budget": self.DEVELOPMENT_BUDGET,
                "remaining": self.DEVELOPMENT_BUDGET - self.data["dev_queries_used"],
                "percentage": (self.data["dev_queries_used"] / self.DEVELOPMENT_BUDGET) * 100
            },
            "production": {
                "used": self.data["prod_queries_used"],
                "reserve": self.PRODUCTION_RESERVE,
                "remaining": self.PRODUCTION_RESERVE - self.data["prod_queries_used"],
                "percentage": (self.data["prod_queries_used"] / self.PRODUCTION_RESERVE) * 100
            }
        }

    def print_usage_stats(self, detailed=False):
        """
        Print formatted usage statistics.

        Args:
            detailed: Show daily history
        """
        stats = self.get_usage_stats()

        print("\n" + "=" * 60)
        print("Wolfram Alpha API Usage - {}".format(stats["month"]))
        print("=" * 60)

        print("\n📊 OVERALL USAGE:")
        print(f"   Total: {stats['total']['used']}/{stats['total']['limit']} queries")
        print(f"   Remaining: {stats['total']['remaining']} queries")
        print(f"   Usage: {stats['total']['percentage']:.1f}%")

        print("\n🔧 DEVELOPMENT BUDGET:")
        print(f"   Used: {stats['development']['used']}/{stats['development']['budget']} queries")
        print(f"   Remaining: {stats['development']['remaining']} queries")
        print(f"   Usage: {stats['development']['percentage']:.1f}%")

        print("\n🚀 PRODUCTION RESERVE:")
        print(f"   Used: {stats['production']['used']}/{stats['production']['reserve']} queries")
        print(f"   Remaining: {stats['production']['remaining']} queries")
        print(f"   Usage: {stats['production']['percentage']:.1f}%")

        if detailed and self.data["history"]:
            print("\n📅 DAILY HISTORY:")
            for date, count in sorted(self.data["history"].items(), reverse=True)[:7]:
                print(f"   {date}: {count} queries")

        print("=" * 60 + "\n")

    def reset_month(self, confirm=False):
        """
        Reset usage for new month (USE WITH CAUTION).

        Args:
            confirm: Must be True to actually reset

        Returns:
            bool: True if reset successful
        """
        if not confirm:
            print("⚠️  WARNING: reset_month() requires confirm=True")
            print("   This will reset all usage counters!")
            return False

        current_month = datetime.now().strftime("%Y-%m")
        self.data = self._create_new_month_data(current_month)
        self._save_usage()

        print(f"✓ Usage reset for {current_month}")
        return True

    def estimate_queries_needed(self, total_queries, cached_queries):
        """
        Estimate how many API queries will be needed.

        Args:
            total_queries: Total number of queries to process
            cached_queries: Number of queries available in cache

        Returns:
            dict: Estimation breakdown
        """
        api_calls_needed = total_queries - cached_queries
        stats = self.get_usage_stats()

        return {
            "total_queries": total_queries,
            "cache_hits": cached_queries,
            "api_calls_needed": api_calls_needed,
            "current_usage": stats["development"]["used"],
            "after_test_usage": stats["development"]["used"] + api_calls_needed,
            "remaining_after": stats["development"]["remaining"] - api_calls_needed,
            "safe_to_proceed": api_calls_needed <= stats["development"]["remaining"]
        }


def main():
    """Test usage tracker functionality."""
    tracker = UsageTracker()

    # Show current stats
    tracker.print_usage_stats(detailed=True)

    # Simulate some queries
    print("\n🧪 Testing query recording...\n")

    for i in range(3):
        can_query, reason = tracker.can_make_query(is_dev=True)

        if can_query:
            print(f"Query {i+1}: ✓ Allowed - {reason}")
            tracker.record_query(is_dev=True)
        else:
            print(f"Query {i+1}: ✗ BLOCKED - {reason}")

    # Show updated stats
    tracker.print_usage_stats()

    # Test estimation
    print("\n📈 Estimation example:")
    estimate = tracker.estimate_queries_needed(total_queries=50, cached_queries=10)
    print(f"   Total queries: {estimate['total_queries']}")
    print(f"   Cache hits: {estimate['cache_hits']}")
    print(f"   API calls needed: {estimate['api_calls_needed']}")
    print(f"   Current usage: {estimate['current_usage']}")
    print(f"   After test: {estimate['after_test_usage']}")
    print(f"   Remaining: {estimate['remaining_after']}")
    print(f"   Safe to proceed: {'✓' if estimate['safe_to_proceed'] else '✗'}\n")


if __name__ == "__main__":
    main()
