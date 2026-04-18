"""Tool error extraction and analysis for Claude Code sessions.

This module extracts tool execution errors from Claude Code session files,
filters out excluded error types, classifies errors by pattern, and
aggregates recurring errors for guideline generation.
"""

import json
import re
from pathlib import Path

# Error pattern definitions
ERROR_PATTERNS: dict[str, dict[str, str]] = {
    "connection_refused": {
        "pattern": re.compile(
            r"Connection refused|ECONNREFUSED|connect ECONNREFUSED|"
            r"Cannot connect to host|Failed to connect.*port|"
            r"errno 111|errno 61|getaddrinfo failed"
        ),
        "suggested_guideline": "Check if the service is running and accessible before connecting",
    },
    "env_undefined": {
        "pattern": re.compile(
            r"(\w+_URL|DATABASE_URL|API_KEY|SECRET|TOKEN|PASSWORD).*"
            r"(undefined|not set|is not defined|empty|null)|"
            r"Environment variable.*not found"
        ),
        "suggested_guideline": "Load .env file before accessing environment variables",
    },
    "module_not_found": {
        "pattern": re.compile(
            r"ModuleNotFoundError|No module named|"
            r"ImportError.*No module|Module not found|"
            r"cannot import name|cannot import module"
        ),
        "suggested_guideline": "Check import paths - verify project structure and dependencies",
    },
    "venv_not_found": {
        "pattern": re.compile(
            r"venv.*No such file|activate: No such file|"
            r"\.venv.*not found|virtual environment.*not found|"
            r"python.*No such file or directory"
        ),
        "suggested_guideline": "Check virtual environment location and activation",
    },
    "port_in_use": {
        "pattern": re.compile(
            r"address already in use|EADDRINUSE|"
            r"port.*already.*use|only one usage of each socket address|"
            r"OSError.*Errno 48|OSError.*Errno 98|Errno 10048",
            re.IGNORECASE,
        ),
        "suggested_guideline": "Check if service is already running on this port",
    },
    "supabase_error": {
        "pattern": re.compile(
            r"supabase|SupabaseClientError|SupabaseError|PostgresError", re.IGNORECASE
        ),
        "suggested_guideline": "Check SUPABASE_URL and SUPABASE_KEY in .env",
    },
    "postgres_error": {
        "pattern": re.compile(
            r"postgres|PostgreSQL|psycopg|PGHOST|:5432|"
            r"password authentication failed|relation.*does not exist|"
            r"duplicate key.*unique constraint|connection to server at"
        ),
        "suggested_guideline": "Check DATABASE_URL in .env for PostgreSQL connection",
    },
    "redis_error": {
        "pattern": re.compile(
            r"redis|REDIS|:6379|" r"redis\.exceptions|NOAUTH|" r"MISCONF|Loading.*in progress"
        ),
        "suggested_guideline": "Check REDIS_URL in .env for Redis connection",
    },
}


# Exclusion pattern definitions
EXCLUSION_PATTERNS: dict[str, dict[str, str]] = {
    "user_rejection": {
        "pattern": re.compile(
            r"The user doesn't want to proceed|"
            r"user declined|user rejected|"
            r"operation cancelled by user"
        ),
        "reason": "User-initiated rejections",
    },
    "claude_guardrail": {
        "pattern": re.compile(
            r"File has not been read yet|"
            r"exceeds maximum allowed tokens|"
            r"exceeds maximum token limit|"
            r"InputValidationError|"
            r"not valid JSON|invalid JSON|"
            r"token limit exceeded"
        ),
        "reason": "Claude Code guardrail messages",
    },
    "bash_syntax": {
        "pattern": re.compile(
            r"unexpected EOF while looking for matching|"
            r"syntax error near unexpected token|"
            r"syntax error.*eval|"
            r"parse error|unexpected token"
        ),
        "reason": "Bash quoting/syntax errors (global Claude behavior)",
    },
    "eisdir": {
        "pattern": re.compile(
            r"EISDIR|illegal operation on a directory|" r"Is a directory|cannot overwrite directory"
        ),
        "reason": "Directory operation errors (global Claude behavior)",
    },
}


def classify_error(content: str) -> str | None:
    """Classify an error message by matching against known patterns.

    Args:
        content: The error message content to classify

    Returns:
        The error_type if matched, None if excluded or unknown
    """
    # Check exclusions first
    for exclusion_name, exclusion_info in EXCLUSION_PATTERNS.items():
        if exclusion_info["pattern"].search(content):
            return None

    # Try to match against error patterns
    for error_type, pattern_info in ERROR_PATTERNS.items():
        if pattern_info["pattern"].search(content):
            return error_type

    # Unknown error type
    return None


def get_guideline(error_type: str) -> str:
    """Get suggested guideline for a given error type.

    Args:
        error_type: The type of error

    Returns:
        Suggested guideline string
    """
    if error_type in ERROR_PATTERNS:
        return ERROR_PATTERNS[error_type]["suggested_guideline"]
    return "No guideline available for this error type"


def extract_tool_errors(session_file: Path) -> list[dict]:
    """Extract tool execution errors from a Claude Code session file.

    Args:
        session_file: Path to the session JSON file

    Returns:
        List of error dictionaries with keys:
        - error_type: Classified error type
        - error_message: The error content
        - tool_name: Name of the tool that failed
        - suggested_guideline: Suggested fix for this error type
    """
    errors = []

    # Convert to Path object if string
    session_path = Path(session_file) if isinstance(session_file, str) else session_file

    # Handle file not found gracefully
    if not session_path.exists():
        return errors

    try:
        with open(session_path, encoding="utf-8") as f:
            session_data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return errors

    # Extract messages
    messages = session_data.get("messages", [])

    for message in messages:
        # Only process assistant messages with tool uses
        if message.get("role") != "assistant":
            continue

        tool_uses = message.get("tool_uses", [])

        for tool_use in tool_uses:
            # Check for result field
            result = tool_use.get("result")
            if not result:
                continue

            # Only extract errors
            if not result.get("is_error", False):
                continue

            # Get error content
            error_content = result.get("output", "")
            if not error_content:
                continue

            # Classify the error
            error_type = classify_error(error_content)

            # Skip if excluded or unknown
            if error_type is None:
                continue

            # Build error object
            error_obj = {
                "error_type": error_type,
                "error_message": error_content,
                "tool_name": tool_use.get("name", "Unknown"),
                "suggested_guideline": get_guideline(error_type),
            }

            errors.append(error_obj)

    return errors


def aggregate_errors(errors: list[dict], min_occurrences: int = 2) -> list[dict]:
    """Aggregate errors by type and calculate confidence scores.

    Args:
        errors: List of error dictionaries from extract_tool_errors
        min_occurrences: Minimum occurrence threshold for inclusion

    Returns:
        List of aggregated error dictionaries with keys:
        - error_type: The error type
        - occurrence_count: Number of occurrences
        - confidence: Confidence score (0.0-1.0)
        - suggested_guideline: Suggested fix for this error type
        - sample_errors: List of sample error messages
    """
    if not errors:
        return []

    # Group by error_type
    grouped: dict[str, list[dict]] = {}
    for error in errors:
        error_type = error.get("error_type")
        if error_type:
            if error_type not in grouped:
                grouped[error_type] = []
            grouped[error_type].append(error)

    # Build aggregated results
    aggregated = []

    for error_type, error_list in grouped.items():
        count = len(error_list)

        # Filter by minimum occurrences
        if count < min_occurrences:
            continue

        # Calculate confidence based on occurrence count
        if count >= 5:
            confidence = 0.90
        elif count >= 3:
            confidence = 0.85
        else:  # count == 2
            confidence = 0.70

        # Get sample errors (up to 3)
        sample_errors = []
        for error in error_list[:3]:
            sample_errors.append(error.get("error_message", ""))

        # Get suggested guideline
        suggested_guideline = get_guideline(error_type)

        # Build aggregated object
        agg_obj = {
            "error_type": error_type,
            "occurrence_count": count,
            "confidence": confidence,
            "suggested_guideline": suggested_guideline,
            "sample_errors": sample_errors,
        }

        aggregated.append(agg_obj)

    # Sort by occurrence count (descending)
    aggregated.sort(key=lambda x: x["occurrence_count"], reverse=True)

    return aggregated
