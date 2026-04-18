"""Plan verifier for /truth skill - verifies implementation against plan commitments.

Item 15: Plan-aware truth validation.
"""

from pathlib import Path
from typing import Any


def verify_documentation_claim(claim: dict[str, str]) -> dict[str, Any]:
    """Verify that a documentation file was updated.

    Args:
        claim: Dict with 'task' and 'file' keys

    Returns:
        Dict with 'verified' (bool), 'evidence' (str), and 'details' keys
    """
    file_path = claim.get("file", "")

    if not file_path:
        return {
            "verified": False,
            "evidence": "No file path specified",
            "details": "Claim missing 'file' field"
        }

    path = Path(file_path)

    if not path.exists():
        return {
            "verified": False,
            "evidence": f"File not found: {file_path}",
            "details": f"Expected file at {file_path} does not exist"
        }

    # Check if file has content
    try:
        content = path.read_text(encoding="utf-8")
        if not content.strip():
            return {
                "verified": False,
                "evidence": f"File exists but is empty: {file_path}",
                "details": f"File at {file_path} exists but has no content"
            }

        # Get file size and modification time
        stat = path.stat()
        return {
            "verified": True,
            "evidence": f"File exists with {len(content)} bytes, modified {stat.st_mtime}",
            "details": f"File at {file_path} exists and has content"
        }
    except Exception as e:
        return {
            "verified": False,
            "evidence": f"Error reading file: {e}",
            "details": str(e)
        }


def verify_success_criterion(criterion: dict[str, str]) -> dict[str, Any]:
    """Verify that a success criterion was met.

    This is a placeholder - actual verification would depend on the criterion type.
    For now, returns unverified since we can't execute arbitrary verification commands.

    Args:
        criterion: Dict with 'description' and optional 'verification' keys

    Returns:
        Dict with 'verified' (bool), 'details' (str) keys
    """
    description = criterion.get("description", "")
    verification = criterion.get("verification", "")

    if not verification:
        # No verification method specified
        return {
            "verified": None,  # None = cannot verify
            "details": f"No verification method for: {description}"
        }

    # Placeholder: would need to parse and execute verification commands
    # For safety, we return unverified
    return {
        "verified": None,
        "details": f"Verification method specified but not executed: {verification}"
    }


def generate_plan_report(plan_path: Path) -> dict[str, Any]:
    """Generate a full verification report for a plan.

    Args:
        plan_path: Path to plan markdown file

    Returns:
        Dict with plan_id, status, documentation_checks, success_criteria_checks,
        and overall_assessment
    """
    from plan_parser import extract_plan_metadata, extract_documentation_requirements, extract_success_criteria

    # Extract plan metadata
    metadata = extract_plan_metadata(plan_path)

    # Extract documentation requirements
    doc_requirements = extract_documentation_requirements(plan_path)

    # Extract success criteria
    success_criteria = extract_success_criteria(plan_path)

    # Verify documentation requirements
    documentation_checks = []
    for req in doc_requirements:
        result = verify_documentation_claim(req)
        documentation_checks.append({
            "claim": req,
            **result
        })

    # Verify success criteria
    success_criteria_checks = []
    for criterion in success_criteria:
        result = verify_success_criterion(criterion)
        success_criteria_checks.append({
            "criterion": criterion,
            **result
        })

    # Calculate overall assessment
    doc_verified = sum(1 for c in documentation_checks if c["verified"])
    doc_total = len(documentation_checks)

    criteria_verified = sum(1 for c in success_criteria_checks if c["verified"] is True)
    criteria_total = len(success_criteria_checks)

    # Determine overall status
    if doc_total == 0 and criteria_total == 0:
        overall = "no_verification_criteria"
    elif doc_verified == doc_total and criteria_verified == criteria_total:
        overall = "all_verified"
    elif doc_verified > 0 or criteria_verified > 0:
        overall = "partially_verified"
    else:
        overall = "none_verified"

    return {
        "plan_id": plan_path.name,
        "status": metadata.get("status", "unknown"),
        "documentation_checks": documentation_checks,
        "success_criteria_checks": success_criteria_checks,
        "summary": {
            "documentation_verified": doc_verified,
            "documentation_total": doc_total,
            "criteria_verified": criteria_verified,
            "criteria_total": criteria_total,
        },
        "overall_assessment": overall,
    }
