#!/usr/bin/env python
"""
cks_health_check.py - Check Constitutional Knowledge System health

Run: python P:/.claude/skills/_tools/cks_health_check.py
Returns exit code 0 if healthy, 1 if issues found

Checks:
1. Database accessibility
2. Entry count (minimum threshold)
3. Embedding coverage (entries with embeddings)
4. Index staleness (DB mtime vs skill mtimes)
5. Recent activity (entries in last 7 days)
6. Database size (warn on bloat)
"""

import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Thresholds
MIN_ENTRIES = 100  # Minimum expected entries
EMBEDDING_COVERAGE_WARN = 0.90  # Warn if <90% have embeddings
STALE_DAYS = 7  # Warn if no updates in 7 days
DB_SIZE_WARN_MB = 50  # Warn if DB exceeds 50MB
RECENT_ACTIVITY_DAYS = 7

# Paths
CKS_DB_PATH = Path(r"P:/__csf/data/cks.db")
SKILLS_DIR = Path(r"P:/.claude/skills")
COMMANDS_DIR = Path(r"P:/__csf/src/commands")


def get_db_stats() -> dict:
    """Get CKS database statistics."""
    stats = {
        "accessible": False,
        "total_entries": 0,
        "with_embeddings": 0,
        "recent_entries": 0,
        "oldest_entry": None,
        "newest_entry": None,
        "size_mb": 0,
        "last_modified": None,
    }

    if not CKS_DB_PATH.exists():
        return stats

    try:
        conn = sqlite3.connect(str(CKS_DB_PATH))
        cursor = conn.cursor()

        # Total entries
        cursor.execute("SELECT COUNT(*) FROM entries")
        stats["total_entries"] = cursor.fetchone()[0]

        # Entries with embeddings
        cursor.execute("SELECT COUNT(*) FROM entries WHERE embedding IS NOT NULL")
        stats["with_embeddings"] = cursor.fetchone()[0]

        # Recent entries
        week_ago = (datetime.now(timezone.utc) - timedelta(days=RECENT_ACTIVITY_DAYS)).isoformat()
        cursor.execute("SELECT COUNT(*) FROM entries WHERE created_at > ?", (week_ago,))
        stats["recent_entries"] = cursor.fetchone()[0]

        # Date range
        cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM entries")
        oldest, newest = cursor.fetchone()
        stats["oldest_entry"] = oldest
        stats["newest_entry"] = newest

        conn.close()
        stats["accessible"] = True

        # File stats
        stats["size_mb"] = CKS_DB_PATH.stat().st_size / (1024 * 1024)
        stats["last_modified"] = datetime.fromtimestamp(
            CKS_DB_PATH.stat().st_mtime, tz=timezone.utc
        )

    except Exception as e:
        stats["error"] = str(e)

    return stats


def check_index_staleness() -> tuple[bool, list[str]]:
    """Check if CKS index is stale compared to source files.

    Note: SKILL.md files are NOT indexed by CKS - they are skill documentation.
    CKS stores knowledge entries (lessons, patterns, decisions) separately.
    """
    stale_sources = []

    if not CKS_DB_PATH.exists():
        return False, []

    db_mtime = CKS_DB_PATH.stat().st_mtime

    # Check commands directory (limit to avoid noise)
    # Note: We DON'T check SKILLS_DIR because SKILL.md files are not CKS content
    if COMMANDS_DIR.exists():
        for cmd_file in list(COMMANDS_DIR.rglob("*.py"))[:50]:
            if cmd_file.stat().st_mtime > db_mtime:
                rel_path = cmd_file.relative_to(COMMANDS_DIR)
                stale_sources.append(f"commands/{rel_path}")
                if len(stale_sources) > 10:
                    stale_sources.append("... (truncated)")
                    break

    return len(stale_sources) > 5, stale_sources[:10]


def main():
    issues = []
    warnings = []

    # 1. Get database stats
    stats = get_db_stats()

    if not stats["accessible"]:
        issues.append(f"CKS database not accessible: {stats.get('error', 'unknown')}")
        print("❌ CKS HEALTH CHECK FAILED")
        print(f"   Database: {CKS_DB_PATH}")
        print("\n❌ ISSUES:")
        for i in issues:
            print(f"   • {i}")
        return 1

    # 2. Check entry count
    if stats["total_entries"] < MIN_ENTRIES:
        warnings.append(f"Low entry count: {stats['total_entries']} (<{MIN_ENTRIES})")

    # 3. Check embedding coverage
    if stats["total_entries"] > 0:
        coverage = stats["with_embeddings"] / stats["total_entries"]
        if coverage < EMBEDDING_COVERAGE_WARN:
            issues.append(f"Embedding coverage: {coverage:.0%} (<{EMBEDDING_COVERAGE_WARN:.0%})")

    # 4. Check database size
    if stats["size_mb"] > DB_SIZE_WARN_MB:
        warnings.append(f"Database size: {stats['size_mb']:.1f}MB (>{DB_SIZE_WARN_MB}MB)")

    # 5. Check staleness
    if stats["last_modified"]:
        days_old = (datetime.now(timezone.utc) - stats["last_modified"]).days
        if days_old > STALE_DAYS:
            warnings.append(f"No updates in {days_old} days")

    # 6. Check recent activity
    if stats["recent_entries"] == 0 and stats["total_entries"] > MIN_ENTRIES:
        warnings.append("No new entries in last 7 days")

    # 7. Check index staleness vs source files
    is_stale, stale_sources = check_index_staleness()
    if is_stale:
        warnings.append(f"Index may be stale: {len(stale_sources)} source files newer than DB")

    # Output
    coverage_pct = (
        (stats["with_embeddings"] / stats["total_entries"] * 100)
        if stats["total_entries"] > 0
        else 0
    )

    if issues or warnings:
        print("⚠️  CKS HEALTH CHECK")
        print(
            f"   Entries: {stats['total_entries']} | Embeddings: {coverage_pct:.0f}% | Size: {stats['size_mb']:.1f}MB | Recent: {stats['recent_entries']}"
        )

        if issues:
            print("\n❌ ISSUES (action required):")
            for i in issues:
                print(f"   • {i}")

        if warnings:
            print("\n⚡ WARNINGS:")
            for w in warnings:
                print(f"   • {w}")

        print("\nRun: /cks or claude 'rebuild CKS embeddings'")
        return 1
    else:
        print(
            f"✅ CKS healthy ({stats['total_entries']} entries, {coverage_pct:.0f}% embeddings, {stats['size_mb']:.1f}MB)"
        )
        return 0


if __name__ == "__main__":
    sys.exit(main())
