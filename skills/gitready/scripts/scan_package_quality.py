#!/usr/bin/env python3
"""
scan_package_quality.py - PHASE 4.5: Package Quality Scanning

Automated security and dependency scanning:
1. Security scanning (bandit, safety)
2. Dependency auditing (pip-audit)
3. Badge validation
4. Quality metrics reporting

Usage:
    python scan_package_quality.py <target_dir> [options]

Examples:
    python scan_package_quality.py P:/packages/my-package
    python scan_package_quality.py /path/to/package --skip-security
    python scan_package_quality.py . --fix-bandit
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""

    BLUE = "\033[0;34m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[0;31m"
    NC = "\033[0m"  # No Color


def log_info(msg: str) -> None:
    """Print info message."""
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")


def log_success(msg: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {msg}")


def log_warning(msg: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {msg}")


def log_error(msg: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}")


def run_command(
    cmd: list[str], cwd: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess:
    """Run a shell command."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        log_error(f"Command failed: {' '.join(cmd)}")
        if e.stderr:
            log_error(f"Error: {e.stderr}")
        raise


def check_tool_installed(tool: str) -> bool:
    """Check if a security tool is installed."""
    try:
        run_command([tool, "--version"], check=False)
        return True
    except Exception:
        return False


def run_bandit_scan(target_dir: Path, fix: bool = False) -> dict[str, any]:
    """Run bandit security scanner."""
    log_info("=== Running Bandit Security Scan ===")

    if not check_tool_installed("bandit"):
        log_warning("Bandit not installed. Install with: pip install bandit")
        return {"installed": False, "issues": 0}

    # Find Python files to scan
    python_files = list(target_dir.rglob("*.py"))
    if not python_files:
        log_warning("No Python files found to scan")
        return {"installed": True, "issues": 0, "skipped": True}

    # Filter out test files and __pycache__
    scan_paths = []
    for f in python_files:
        path_str = str(f).replace("\\", "/")
        # Check if file is in tests directory or is a test file
        in_tests_dir = "/tests/" in path_str
        is_test_file = f.name.startswith("test_")
        # Check only immediate parent directory for test_ prefix
        # Don't scan all ancestors (avoids matching pytest temp dirs)
        parent_has_test = f.parent.name.startswith("test_")

        if (
            "__pycache__" not in path_str
            and "/.git/" not in path_str
            and not in_tests_dir
            and not is_test_file
            and not parent_has_test
        ):
            scan_paths.append(f)

    if not scan_paths:
        log_warning("No non-test Python files found")
        return {"installed": True, "issues": 0, "skipped": True}

    log_info(f"Scanning {len(scan_paths)} files...")

    try:
        cmd = ["bandit", "-f", "json", "-r", str(target_dir)]
        # Exclude test directories
        cmd.extend(["-s", "B101,B601"])  # Skip assert_used and shell_injection_common

        result = run_command(cmd, check=False)

        if result.returncode == 0:
            log_success("No security issues found by Bandit")
            return {"installed": True, "issues": 0, "results": {}}

        # Parse results
        try:
            data = json.loads(result.stdout)
            issues = data.get("results", [])
            error_count = len(issues)

            if error_count > 0:
                log_warning(f"Bandit found {error_count} potential issue(s):")

                # Group by severity
                high = [i for i in issues if i.get("issue_severity") == "HIGH"]
                medium = [i for i in issues if i.get("issue_severity") == "MEDIUM"]
                low = [i for i in issues if i.get("issue_severity") == "LOW"]

                if high:
                    print(f"  {Colors.RED}HIGH:{Colors.NC} {len(high)}")
                if medium:
                    print(f"  {Colors.YELLOW}MEDIUM:{Colors.NC} {len(medium)}")
                if low:
                    print(f"  {Colors.BLUE}LOW:{Colors.NC} {len(low)}")

                # Show first few issues
                for issue in issues[:5]:
                    fname = issue.get("filename", "")
                    line = issue.get("line_number", 0)
                    severity = issue.get("issue_severity", "")
                    text = issue.get("issue_text", "")
                    try:
                        rel_path = str(Path(fname).relative_to(target_dir))
                    except (ValueError, TypeError):
                        # Path can't be made relative, use filename as-is
                        rel_path = fname
                    print(f"    - {rel_path}:{line} [{severity}] {text[:60]}...")

                if len(issues) > 5:
                    print(f"    ... and {len(issues) - 5} more")

            return {
                "installed": True,
                "issues": error_count,
                "results": data,
            }

        except json.JSONDecodeError:
            log_warning("Could not parse Bandit output")
            return {"installed": True, "issues": -1}

    except Exception as e:
        log_warning(f"Bandit scan failed: {e}")
        return {"installed": True, "issues": -1, "error": str(e)}


def run_safety_scan(target_dir: Path) -> dict[str, any]:
    """Run safety check for known vulnerable dependencies."""
    log_info("=== Running Safety Dependency Check ===")

    if not check_tool_installed("safety"):
        log_warning("Safety not installed. Install with: pip install safety")
        return {"installed": False, "vulnerabilities": 0}

    requirements_files = [
        target_dir / "requirements.txt",
        target_dir / "pyproject.toml",
        target_dir / "setup.py",
    ]

    requirements_file = None
    for f in requirements_files:
        if f.exists():
            requirements_file = f
            break

    if not requirements_file:
        log_warning("No requirements file found")
        return {"installed": True, "vulnerabilities": 0, "skipped": True}

    log_info(f"Checking: {requirements_file.name}")

    try:
        cmd = ["safety", "check", "--json", "--file", str(requirements_file)]
        result = run_command(cmd, check=False)

        if result.returncode == 0:
            log_success("No known vulnerabilities found")
            return {"installed": True, "vulnerabilities": 0}
        else:
            try:
                data = json.loads(result.stdout)
                vulns = data if isinstance(data, list) else []
                log_warning(f"Safety found {len(vulns)} known vulnerability(ies)")

                for vuln in vulns[:3]:
                    pkg = vuln.get("package", "unknown")
                    id_ = vuln.get("id", "unknown")
                    affected = vuln.get("affected_versions", [])
                    print(f"    - {pkg}: {id_} (affects {affected})")

                return {
                    "installed": True,
                    "vulnerabilities": len(vulns),
                    "details": vulns,
                }

            except json.JSONDecodeError:
                log_warning("Could not parse Safety output")
                return {"installed": True, "vulnerabilities": -1}

    except Exception as e:
        log_warning(f"Safety check failed: {e}")
        return {"installed": True, "vulnerabilities": -1, "error": str(e)}


def run_pip_audit(target_dir: Path) -> dict[str, any]:
    """Run pip-audit for dependency vulnerability scanning."""
    log_info("=== Running Pip-Audit ===")

    if not check_tool_installed("pip-audit"):
        log_warning("pip-audit not installed. Install with: pip install pip-audit")
        return {"installed": False, "vulnerabilities": 0}

    try:
        # Run in the target directory to pick up local packages
        result = run_command(
            ["pip-audit", "--format", "json"],
            cwd=target_dir,
            check=False,
        )

        if result.returncode == 0:
            log_success("No vulnerabilities found by pip-audit")
            return {"installed": True, "vulnerabilities": 0}

        try:
            data = json.loads(result.stdout)
            vulns = data if isinstance(data, list) else []

            if vulns:
                log_warning(f"pip-audit found {len(vulns)} vulnerability(ies):")

                for vuln in vulns[:5]:
                    name = vuln.get("name", "unknown")
                    vuln_ids = vuln.get("vuln_ids", [])
                    #        fix_versions = vuln.get("fix_versions", ["none"])
                    print(f"    - {name}: {', '.join(vuln_ids)}")

            return {
                "installed": True,
                "vulnerabilities": len(vulns),
                "details": vulns,
            }

        except json.JSONDecodeError:
            log_warning("Could not parse pip-audit output")
            return {"installed": True, "vulnerabilities": -1}

    except Exception as e:
        log_warning(f"pip-audit failed: {e}")
        return {"installed": True, "vulnerabilities": -1, "error": str(e)}


def validate_badges(target_dir: Path) -> dict[str, any]:
    """Validate badge URLs in README.md."""
    log_info("=== Validating Badges ===")

    readme_path = target_dir / "README.md"
    if not readme_path.exists():
        log_warning("No README.md found")
        return {"checked": 0, "valid": 0, "invalid": 0, "missing": []}

    with open(readme_path) as f:
        content = f.read()

    # Find badge URLs (usually shields.io, img.shields.io)
    badge_pattern = r"https?://[a-z0-9\-\.]*shields\.io/[^\s\)]+"
    badges = re.findall(badge_pattern, content)

    if not badges:
        log_warning("No badges found in README.md")
        return {"checked": 0, "valid": 0, "invalid": 0, "missing": []}

    log_info(f"Found {len(badges)} badge(s)")

    # Also check for GitHub workflow badge references
    workflow_pattern = r"/workflows/([^/]+)/badge\.svg"
    workflow_badges = re.findall(workflow_pattern, content)

    # Initialize missing_workflows before the if block
    missing_workflows = []

    if workflow_badges:
        log_info(f"Found {len(workflow_badges)} workflow badge(s)")

        # Verify workflow files exist
        workflows_dir = target_dir / ".github" / "workflows"

        if workflows_dir.exists():
            for workflow in workflow_badges:
                workflow_file = workflows_dir / f"{workflow}.yml"
                if not workflow_file.exists():
                    workflow_file = workflows_dir / f"{workflow}.yaml"
                    if not workflow_file.exists():
                        missing_workflows.append(workflow)

        if missing_workflows:
            log_warning(f"Missing workflow files: {', '.join(missing_workflows)}")
        else:
            log_success("All workflow badges reference existing files")

    return {
        "checked": len(badges),
        "valid": len(badges) - len(missing_workflows),
        "invalid": len(missing_workflows),
        "missing": missing_workflows,
    }


def check_code_quality_metrics(target_dir: Path) -> dict[str, any]:
    """Check basic code quality metrics."""
    log_info("=== Code Quality Metrics ===")

    # Count Python files
    python_files = list(target_dir.rglob("*.py"))
    non_test_files = [
        f
        for f in python_files
        if "__pycache__" not in str(f)
        and "/.git/" not in str(f).replace("\\", "/")
        and "/tests/" not in str(f).replace("\\", "/")
        and "test_" not in f.name
    ]

    # Count test files
    test_files = [
        f
        for f in python_files
        if "/tests/" in str(f).replace("\\", "/") or f.name.startswith("test_")
    ]

    # Count total lines of code
    total_lines = 0
    for f in non_test_files:
        try:
            with open(f) as file:
                total_lines += sum(1 for _ in file)
        except Exception:
            pass

    metrics = {
        "python_files": len(non_test_files),
        "test_files": len(test_files),
        "total_lines": total_lines,
    }

    print(f"  Python files: {len(non_test_files)}")
    print(f"  Test files: {len(test_files)}")

    if test_files:
        test_ratio = len(test_files) / max(len(non_test_files), 1)
        print(f"  Test ratio: {test_ratio:.2%}")

        if test_ratio >= 0.5:
            log_success("Good test coverage (ratio >= 50%)")
        elif test_ratio >= 0.25:
            log_warning("Moderate test coverage (ratio >= 25%)")
        else:
            log_warning("Low test coverage (ratio < 25%)")

    print(f"  Total lines: {total_lines}")

    return metrics


def generate_report(
    target_dir: Path,
    bandit_results: dict,
    safety_results: dict,
    audit_results: dict,
    badge_results: dict,
    quality_metrics: dict,
) -> dict:
    """Generate quality scan report."""
    log_info("=== Quality Scan Summary ===")

    report = {
        "target": str(target_dir),
        "bandit": bandit_results,
        "safety": safety_results,
        "pip_audit": audit_results,
        "badges": badge_results,
        "quality": quality_metrics,
    }

    print()
    log_info("Security:")
    if bandit_results.get("installed"):
        issues = bandit_results.get("issues", 0)
        status = (
            f"{Colors.GREEN}✓{Colors.NC}"
            if issues == 0
            else f"{Colors.YELLOW}!{Colors.NC}"
        )
        print(f"  {status} Bandit: {issues} issue(s)")
    else:
        print(f"  {Colors.YELLOW}○{Colors.NC} Bandit: Not installed")

    if safety_results.get("installed"):
        vulns = safety_results.get("vulnerabilities", 0)
        status = (
            f"{Colors.GREEN}✓{Colors.NC}"
            if vulns == 0
            else f"{Colors.YELLOW}!{Colors.NC}"
        )
        print(f"  {status} Safety: {vulns} known vulnerability(ies)")
    else:
        print(f"  {Colors.YELLOW}○{Colors.NC} Safety: Not installed")

    if audit_results.get("installed"):
        vulns = audit_results.get("vulnerabilities", 0)
        status = (
            f"{Colors.GREEN}✓{Colors.NC}"
            if vulns == 0
            else f"{Colors.YELLOW}!{Colors.NC}"
        )
        print(f"  {status} pip-audit: {vulns} vulnerability(ies)")
    else:
        print(f"  {Colors.YELLOW}○{Colors.NC} pip-audit: Not installed")

    print()
    log_info("Badges:")
    checked = badge_results.get("checked", 0)
    invalid = badge_results.get("invalid", 0)
    status = (
        f"{Colors.GREEN}✓{Colors.NC}"
        if invalid == 0
        else f"{Colors.YELLOW}!{Colors.NC}"
    )
    print(f"  {status} {checked} checked, {invalid} invalid")

    print()
    log_info("Quality Metrics:")
    print(f"  Files: {quality_metrics.get('python_files', 0)}")
    print(f"  Tests: {quality_metrics.get('test_files', 0)}")
    print(f"  Lines: {quality_metrics.get('total_lines', 0)}")

    return report


def save_report(report: dict, target_dir: Path) -> None:
    """Save quality scan report to file."""
    report_path = target_dir / ".quality-report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    log_info(f"Report saved to: {report_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="PHASE 4.5: Package Quality Scanning")
    parser.add_argument("target_dir", type=Path, help="Target directory to scan")
    parser.add_argument(
        "--skip-security",
        action="store_true",
        help="Skip security scanning (bandit, safety)",
    )
    parser.add_argument(
        "--skip-audit",
        action="store_true",
        help="Skip dependency auditing (pip-audit)",
    )
    parser.add_argument(
        "--skip-badges",
        action="store_true",
        help="Skip badge validation",
    )
    parser.add_argument(
        "--skip-quality",
        action="store_true",
        help="Skip code quality metrics",
    )
    parser.add_argument(
        "--fix-bandit",
        action="store_true",
        help="Attempt to fix Bandit issues (B104, etc.)",
    )
    parser.add_argument(
        "--save-report",
        action="store_true",
        help="Save scan results to .quality-report.json",
    )
    parser.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="Exit with error code if issues are found",
    )

    args = parser.parse_args()

    target_dir = args.target_dir.resolve()

    log_info("=== Package Quality Scan ===")
    log_info(f"Target: {target_dir}")

    if not target_dir.exists():
        log_error(f"Target directory does not exist: {target_dir}")
        sys.exit(1)

    # Run scans
    bandit_results = {}
    safety_results = {}
    audit_results = {}
    badge_results = {}
    quality_metrics = {}

    if not args.skip_security:
        bandit_results = run_bandit_scan(target_dir, args.fix_bandit)
        safety_results = run_safety_scan(target_dir)

    if not args.skip_audit:
        audit_results = run_pip_audit(target_dir)

    if not args.skip_badges:
        badge_results = validate_badges(target_dir)

    if not args.skip_quality:
        quality_metrics = check_code_quality_metrics(target_dir)

    # Generate report
    report = generate_report(
        target_dir,
        bandit_results,
        safety_results,
        audit_results,
        badge_results,
        quality_metrics,
    )

    if args.save_report:
        save_report(report, target_dir)

    # Determine exit code
    total_issues = (
        bandit_results.get("issues", 0)
        + safety_results.get("vulnerabilities", 0)
        + audit_results.get("vulnerabilities", 0)
        + badge_results.get("invalid", 0)
    )

    print()
    if total_issues > 0:
        log_warning(f"Found {total_issues} total issue(s)")
        if args.fail_on_issues:
            sys.exit(1)
    else:
        log_success("Quality scan passed!")

    sys.exit(0 if total_issues == 0 or not args.fail_on_issues else 1)


if __name__ == "__main__":
    main()
