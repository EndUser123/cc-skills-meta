#!/usr/bin/env python3
"""
create_findings_table.py - CKS Findings Table Migration

Purpose:
    Create a findings table in the CKS database to enable pattern recognition
    between debugRCA (/r skill) and /q skill. This table stores structured
    findings from various quality analysis tools for cross-session correlation
    and technical debt tracking.

Schema Purpose:
    The findings table stores structured quality analysis results with metadata
    to enable:
    - Cross-session pattern recognition (recurring issues)
    - Technical debt tracking over time
    - Strategic quality insights via /q skill
    - Historical analysis of debugRCA findings

Usage:
    # Run migration
    python P:/.claude/skills/cks/migrations/create_findings_table.py

    # Use as module
    from .claude.skills.cks.migrations.create_findings_table import (
        create_findings_table,
        upsert_finding,
        query_findings
    )

Database:
    - Path: P:/__csf/data/cks.db
    - Table: findings
    - Idempotent: Safe to run multiple times

Fields:
    - id: Auto-increment primary key
    - type: Finding type (REFACTOR, DEBT, OPT, DOC, SEC, BUG, PATTERN, etc.)
    - severity: Severity level (critical, high, medium, low)
    - source: Source skill/tool (debugrca, dne, arch, q, r, etc.)
    - file_path: Affected file path (optional)
    - line_number: Affected line number (optional)
    - message: Finding description (required)
    - metadata: JSON metadata for extensions (optional)
    - timestamp: ISO 8601 timestamp (auto-generated)

Indexes:
    - idx_findings_source_timestamp: Optimizes queries by source with time ordering
    - idx_findings_type: Optimizes filtering by finding type

Upsert Logic:
    - UNIQUE constraint on (source, file_path, line_number, type, message)
    - Uses INSERT OR REPLACE for idempotent operations
    - Safe for re-runs and repeated findings

Returns:
    - create_findings_table(): True on success, False on error
    - upsert_finding(): True on success, False on error
    - query_findings(): List of finding dicts or empty list on error
"""

import json
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_DB_PATH = Path(r'P:/__csf/data/cks.db')
SEVERITY_LEVELS = ['critical', 'high', 'medium', 'low']
COMMON_SOURCES = ['debugrca', 'dne', 'arch', 'q', 'r']
COMMON_TYPES = ['REFACTOR', 'DEBT', 'OPT', 'DOC', 'SEC', 'BUG', 'PATTERN', 'CLEANUP']


def create_findings_table(db_path: str | Path | None = None) -> bool:
    """Create findings table and indexes in CKS database.

    This function is idempotent - safe to run multiple times.
    Uses CREATE TABLE IF NOT EXISTS and CREATE INDEX IF NOT EXISTS.

    Args:
        db_path: Path to CKS database. Defaults to P:/__csf/data/cks.db

    Returns:
        True on success, False on error

    Example:
        >>> success = create_findings_table()
        >>> if success:
        ...     print("Findings table created successfully")
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    else:
        db_path = Path(db_path)

    # Ensure directory exists
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create database directory: {e}")
        return False

    # Check if database file exists (optional, not required)
    if not db_path.exists():
        logger.info(f"Database file does not exist, will create: {db_path}")

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Create findings table with upsert support
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                severity TEXT NOT NULL DEFAULT 'medium',
                source TEXT NOT NULL,
                file_path TEXT,
                line_number INTEGER,
                message TEXT NOT NULL,
                metadata TEXT,
                timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source, file_path, line_number, type, message)
            )
        """)

        # Create index for source-based queries with time ordering
        # Common pattern: "Show all debugrca findings from last 7 days"
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_findings_source_timestamp
            ON findings(source, timestamp DESC)
        """)

        # Create index for type-based filtering
        # Common pattern: "Show all REFACTOR findings across all sources"
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_findings_type
            ON findings(type)
        """)

        conn.commit()
        conn.close()

        logger.info(f"✓ Findings table created successfully: {db_path}")
        return True

    except sqlite3.Error as e:
        logger.error(f"SQLite error creating findings table: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error creating findings table: {e}")
        return False


def upsert_finding(
    finding_type: str,
    source: str,
    message: str,
    db_path: str | Path | None = None,
    file_path: str | None = None,
    line_number: int | None = None,
    severity: str = "medium",
    metadata: dict[str, Any] | None = None
) -> bool:
    """Insert or update a finding in the CKS findings table.

    Uses INSERT OR REPLACE for idempotent operations.
    The UNIQUE constraint on (source, file_path, line_number, type, message)
    ensures that duplicate findings are updated rather than creating duplicates.

    Args:
        finding_type: Type of finding (REFACTOR, DEBT, OPT, DOC, SEC, etc.)
        source: Source skill/tool (debugrca, dne, arch, q, r, etc.)
        message: Finding description (required)
        db_path: Path to CKS database. Defaults to P:/__csf/data/cks.db
        file_path: Affected file path (optional)
        line_number: Affected line number (optional)
        severity: Severity level (critical, high, medium, low). Default: medium
        metadata: Additional metadata as dict (optional, will be JSON serialized)

    Returns:
        True on success, False on error

    Example:
        >>> success = upsert_finding(
        ...     finding_type="REFACTOR",
        ...     source="debugrca",
        ...     message="JWT validation logic duplicated across 3 modules",
        ...     file_path="src/auth/jwt_validator.py",
        ...     line_number=45,
        ...     severity="high",
        ...     metadata={"suggested_action": "extract to shared utility"}
        ... )
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    else:
        db_path = Path(db_path)

    # Validate severity
    if severity not in SEVERITY_LEVELS:
        logger.warning(f"Invalid severity '{severity}', defaulting to 'medium'")
        severity = "medium"

    # Serialize metadata to JSON if provided
    metadata_json = None
    if metadata is not None:
        try:
            metadata_json = json.dumps(metadata, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to serialize metadata: {e}, storing without metadata")
            metadata_json = None

    # Handle NULL values for file_path and line_number
    # SQLite treats empty string as different from NULL
    file_path_value = file_path if file_path else None
    line_number_value = line_number if line_number is not None else None

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # INSERT OR REPLACE leverages the UNIQUE constraint for upsert behavior
        cursor.execute("""
            INSERT OR REPLACE INTO findings (
                type, severity, source, file_path, line_number,
                message, metadata, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            finding_type,
            severity,
            source,
            file_path_value,
            line_number_value,
            message,
            metadata_json
        ))

        conn.commit()
        conn.close()

        logger.debug(f"✓ Finding upserted: [{finding_type}] {source} - {message}")
        return True

    except sqlite3.Error as e:
        logger.error(f"SQLite error upserting finding: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error upserting finding: {e}")
        return False


def query_findings(
    source: str | None = None,
    finding_type: str | None = None,
    file_path: str | None = None,
    db_path: str | Path | None = None,
    limit: int = 100
) -> list[dict[str, Any]]:
    """Query findings from the CKS findings table with optional filters.

    Args:
        source: Filter by source (e.g., 'debugrca', 'q', 'r'). Optional.
        finding_type: Filter by finding type (e.g., 'REFACTOR', 'DEBT'). Optional.
        file_path: Filter by file path. Optional.
        db_path: Path to CKS database. Defaults to P:/__csf/data/cks.db
        limit: Maximum number of results to return. Default: 100

    Returns:
        List of finding dictionaries with keys: id, type, severity, source,
        file_path, line_number, message, metadata, timestamp.
        Returns empty list on error.

    Example:
        >>> # Get all debugrca findings from last 7 days
        >>> findings = query_findings(source="debugrca", limit=50)
        >>>
        >>> # Get all REFACTOR findings across all sources
        >>> findings = query_findings(finding_type="REFACTOR")
        >>>
        >>> # Get findings for a specific file
        >>> findings = query_findings(file_path="src/auth/jwt_validator.py")
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    else:
        db_path = Path(db_path)

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build query with filters
        query = "SELECT * FROM findings WHERE 1=1"
        params = []

        if source:
            query += " AND source = ?"
            params.append(source)

        if finding_type:
            query += " AND type = ?"
            params.append(finding_type)

        if file_path:
            query += " AND file_path = ?"
            params.append(file_path)

        # Order by timestamp descending (most recent first)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convert to list of dicts
        findings = []
        for row in rows:
            finding = dict(row)
            # Parse JSON metadata if present
            if finding.get('metadata'):
                try:
                    finding['metadata'] = json.loads(finding['metadata'])
                except json.JSONDecodeError:
                    finding['metadata'] = None
            findings.append(finding)

        conn.close()
        return findings

    except sqlite3.Error as e:
        logger.error(f"SQLite error querying findings: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error querying findings: {e}")
        return []


def get_statistics(db_path: str | Path | None = None) -> dict[str, Any]:
    """Get statistics about findings in the CKS database.

    Args:
        db_path: Path to CKS database. Defaults to P:/__csf/data/cks.db

    Returns:
        Dictionary with statistics:
        - total_findings: Total number of findings
        - by_source: Dict of {source: count}
        - by_type: Dict of {type: count}
        - by_severity: Dict of {severity: count}
        - latest_finding_timestamp: ISO timestamp of most recent finding
        Returns empty dict on error.

    Example:
        >>> stats = get_statistics()
        >>> print(f"Total findings: {stats['total_findings']}")
        >>> print(f"By source: {stats['by_source']}")
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    else:
        db_path = Path(db_path)

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Total findings
        cursor.execute("SELECT COUNT(*) FROM findings")
        total = cursor.fetchone()[0]

        # By source
        cursor.execute("""
            SELECT source, COUNT(*) as count
            FROM findings
            GROUP BY source
            ORDER BY count DESC
        """)
        by_source = {row[0]: row[1] for row in cursor.fetchall()}

        # By type
        cursor.execute("""
            SELECT type, COUNT(*) as count
            FROM findings
            GROUP BY type
            ORDER BY count DESC
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}

        # By severity
        cursor.execute("""
            SELECT severity, COUNT(*) as count
            FROM findings
            GROUP BY severity
            ORDER BY count DESC
        """)
        by_severity = {row[0]: row[1] for row in cursor.fetchall()}

        # Latest finding timestamp
        cursor.execute("SELECT MAX(timestamp) FROM findings")
        latest = cursor.fetchone()[0]

        conn.close()

        return {
            'total_findings': total,
            'by_source': by_source,
            'by_type': by_type,
            'by_severity': by_severity,
            'latest_finding_timestamp': latest
        }

    except sqlite3.Error as e:
        logger.error(f"SQLite error getting statistics: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error getting statistics: {e}")
        return {}


def main() -> int:
    """Main entry point for command-line execution.

    Creates the findings table and runs basic tests.

    Returns:
        0 on success, 1 on error
    """
    logger.info("CKS Findings Table Migration Script")
    logger.info("=" * 50)

    # Step 1: Create table
    logger.info("Step 1: Creating findings table...")
    if not create_findings_table():
        logger.error("Failed to create findings table")
        return 1

    # Step 2: Test upsert
    logger.info("\nStep 2: Testing upsert functionality...")
    test_success = upsert_finding(
        finding_type="TEST",
        source="migration_script",
        message="Test finding from migration script",
        file_path="test.py",
        line_number=1,
        severity="low",
        metadata={"test": True}
    )

    if not test_success:
        logger.error("Failed to upsert test finding")
        return 1

    # Step 3: Verify upsert
    logger.info("\nStep 3: Verifying test finding...")
    findings = query_findings(source="migration_script", limit=1)

    if not findings:
        logger.error("Failed to query test finding")
        return 1

    finding = findings[0]
    if finding['message'] != "Test finding from migration script":
        logger.error(f"Unexpected message: {finding['message']}")
        return 1

    logger.info(f"✓ Test finding verified: {finding['message']}")

    # Step 4: Show statistics
    logger.info("\nStep 4: Database statistics...")
    stats = get_statistics()

    if stats:
        logger.info(f"Total findings: {stats['total_findings']}")
        if stats['by_source']:
            logger.info(f"By source: {stats['by_source']}")
        if stats['by_type']:
            logger.info(f"By type: {stats['by_type']}")
    else:
        logger.warning("Could not retrieve statistics")

    # Step 5: Cleanup test data
    logger.info("\nStep 5: Cleaning up test data...")
    try:
        conn = sqlite3.connect(str(DEFAULT_DB_PATH))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM findings WHERE source = 'migration_script'")
        conn.commit()
        conn.close()
        logger.info("✓ Test data cleaned up")
    except Exception as e:
        logger.warning(f"Could not clean up test data: {e}")

    logger.info("\n" + "=" * 50)
    logger.info("✓ Migration completed successfully!")
    logger.info(f"Database: {DEFAULT_DB_PATH}")
    logger.info("Table: findings")
    logger.info("Ready for use by /r and /q skills")

    return 0


if __name__ == "__main__":
    sys.exit(main())
