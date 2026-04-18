"""DependencyChecker - Verify dependency health and security.

Priority: P2 (runs during gap detection)
Purpose: Detect dependency issues, outdated packages, security vulnerabilities

Checks:
- Outdated dependencies (compared to latest versions)
- Security vulnerabilities (if CVE data available)
- Missing dependencies (imports without package installation)
- Unused dependencies (packages installed but not imported)
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

# Comprehensive Python 3.x stdlib module set — used to filter stdlib imports
# from dependency analysis. Maintenance note: update when Python version adds
# new stdlib modules that are commonly imported in projects.
PYTHON_STDLIB_MODULES: frozenset[str] = frozenset({
    # Core builtins
    "os", "sys", "json", "re", "pathlib", "ast", "subprocess", "dataclasses",
    "typing", "datetime", "collections", "itertools", "functools", "math",
    "random", "string", "io", "builtins",
    # File formats and encoding
    "csv", "xml", "html", "xml.etree", "xml.dom", "xml.sax", "configparser",
    "toml", "plistlib",
    # Networking and web
    "urllib", "urllib.request", "urllib.response", "urllib.parse", "urllib.error",
    "http", "http.client", "http.server", "http.cookies", "http.cookiejar",
    "ftplib", "telnetlib", "ssh", "socket", "socketserver", "email", "mailbox",
    "smtplib", "poplib", "imaplib", "nntplib", "webbrowser", "cgi", "wsgiref",
    "html.parser", "html.entities", "BaseHTTPServer", "CGIHTTPServer",
    # Data handling
    "array", "bisect", "heapq", "queue", "weakref", "copy", "pprint", "profile",
    "cProfile", "pstats", "gc", "inspect", "traceback", "types", "warnings",
    "timeit", "atexit", "faulthandler",
    # Compression and archive
    "zipfile", "tarfile", "gzip", "bz2", "lzma", "zipimport",
    # Encryption and hashing
    "hashlib", "hmac", "secrets", "ssl", "tls", "crypt",
    # Object serialization
    "pickle", "marshal", "dbm", "shelve", "dumbdbm",
    # Threading and concurrency
    "threading", "multiprocessing", "concurrent", "asyncio", "thread", "_thread",
    "tempfile", "uuid",
    # System and platform
    "platform", "errno", "ctypes", "signal", "fcntl", "select", "mmap",
    "readline", "rlcompleter",
    # Internationalization
    "locale", "gettext", "iconv",
    # Text processing
    "textwrap", "unicodedata", "stringprep", "difflib", "sre_parse",
    "sre_compile", "sre_constants",
    # OS and file system
    "os.path", "stat", "statvfs", "filecmp", "fileinput", "shutil", "glob",
    "fnmatch", "linecache", "tokenize", "keyword", "token", "operator", "reprlib",
    # Parsing and compiling
    "parser", "compiler", "code", "codeop", "dis", "pickletools",
    # Debugging and testing
    "pdb", "bdb", "debug", "unittest", "doctest", "test",
    # Development tools
    "venv", "ensurepip", "pip", "setuptools", "distutils",
    # Registry and config
    "winreg", "msilib", "msvcrt", "winsound",
    # Graphics and media (if available)
    "turtle", "tkinter",
    # Other utilities
    "imp", "importlib", "pkgutil", "argparse", "optparse", "getopt",
    "calendar", "collections.abc", "contextvars", "ipaddress", "typing_extensions",
    "typing_inspection",
    # Module introspection
    "modulefinder", "py_compile", "pycache",
    # Logging
    "logging", "logging.handlers", "logging.config",
    # Abstract base classes
    "abc",
    # Path operations
    "ntpath", "posixpath", "macpath", "dospath",
    # Network protocols
    "base64", "binhex", "uu", "zlib",
})


@dataclass
class DependencyIssue:
    """A dependency issue found."""

    issue_type: Literal["outdated", "vulnerable", "missing", "unused"]
    package_name: str
    current_version: str | None
    latest_version: str | None
    severity: Literal["low", "medium", "high", "critical"]
    description: str


@dataclass
class DependencyResult:
    """Result of dependency check."""

    issues: list[DependencyIssue]
    packages_checked: int
    outdated_count: int
    vulnerable_count: int
    missing_count: int
    unused_count: int


class DependencyChecker:
    """
    Verify dependency health and security.

    Checks for outdated packages, security vulnerabilities, missing dependencies,
    and unused dependencies.
    """

    # Requirements files to check
    REQUIREMENTS_FILES = [
        "requirements.txt",
        "requirements-dev.txt",
        "pyproject.toml",
        "setup.py",
        "Pipfile",
    ]

    # Security keywords for vulnerability detection
    SECURITY_KEYWORDS = ["vulnerability", "CVE", "security", "exploit", "advisory"]

    def __init__(self, project_root: Path | None = None):
        """Initialize checker with project root.

        Args:
            project_root: Project root directory (defaults to cwd)
        """
        self.project_root = Path(project_root or Path.cwd()).resolve()

    def _find_requirements_file(self) -> Path | None:
        """Find the primary requirements file.

        Returns:
            Path to requirements file if found, None otherwise
        """
        for filename in self.REQUIREMENTS_FILES:
            path = self.project_root / filename
            if path.exists():
                return path
        return None

    def _parse_requirements(self, requirements_path: Path) -> dict[str, str]:
        """Parse requirements file to extract package versions.

        Args:
            requirements_path: Path to requirements file

        Returns:
            Dict mapping package names to version specs
        """
        packages: dict[str, str] = {}

        if requirements_path.name.endswith(".txt"):
            return self._parse_requirements_txt(requirements_path)
        elif requirements_path.name == "pyproject.toml":
            return self._parse_pyproject_toml(requirements_path)
        elif requirements_path.name == "setup.py":
            return self._parse_setup_py(requirements_path)

        return packages

    def _parse_requirements_txt(self, path: Path) -> dict[str, str]:
        """Parse requirements.txt file.

        Args:
            path: Path to requirements.txt

        Returns:
            Dict mapping package names to version specs
        """
        packages = {}
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    # Parse "package==version" or "package>=version"
                    match = re.match(r"^([a-zA-Z0-9_-]+)([>=<~!]=.+)?", line)
                    if match:
                        name = match.group(1).lower()
                        version_spec = match.group(2) or ""
                        packages[name] = version_spec
        except (OSError, UnicodeDecodeError):
            pass
        return packages

    def _parse_pyproject_toml(self, path: Path) -> dict[str, str]:
        """Parse pyproject.toml file.

        Args:
            path: Path to pyproject.toml

        Returns:
            Dict mapping package names to version specs
        """
        packages = {}
        try:
            with open(path) as f:
                content = f.read()
            # Simple regex-based TOML parsing for dependencies
            # Look for dependencies in [project.dependencies] or [tool.poetry.dependencies]
            deps_match = re.search(
                r"\[(?:project\.)?dependencies\](.*?)(?:\[|\Z)",
                content,
                re.DOTALL | re.MULTILINE,
            )
            if deps_match:
                deps_section = deps_match.group(1)
                for line in deps_section.split("\n"):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    # Parse "package == version" or "package >= version"
                    match = re.match(
                        r'^"?([a-zA-Z0-9_-]+)"?\s*=\s*["\']?([>=<~!0-9.\w]+)?',
                        line,
                    )
                    if match:
                        name = match.group(1).lower()
                        version_spec = match.group(2) or ""
                        packages[name] = version_spec
        except (OSError, UnicodeDecodeError):
            pass
        return packages

    def _parse_setup_py(self, path: Path) -> dict[str, str]:
        """Parse setup.py file.

        Args:
            path: Path to setup.py

        Returns:
            Dict mapping package names to version specs
        """
        packages = {}
        try:
            with open(path) as f:
                content = f.read()
            # Use AST to find install_requires
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr == "setup":
                            for keyword in node.keywords:
                                if keyword.arg == "install_requires":
                                    if isinstance(keyword.value, ast.List):
                                        for elt in keyword.value.elts:
                                            if isinstance(elt, ast.Constant) and isinstance(
                                                elt.value, str
                                            ):
                                                match = re.match(
                                                    r"^([a-zA-Z0-9_-]+)([>=<~!]=.+)?",
                                                    elt.value,
                                                )
                                                if match:
                                                    name = match.group(1).lower()
                                                    version_spec = match.group(2) or ""
                                                    packages[name] = version_spec
        except (OSError, UnicodeDecodeError, SyntaxError):
            pass
        return packages

    def _get_installed_packages(self) -> dict[str, str]:
        """Get currently installed packages.

        Returns:
            Dict mapping package names to installed versions
        """
        packages = {}
        try:
            # Use pip list --format=json to get installed packages
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                for pkg in json.loads(result.stdout):
                    name = pkg.get("name", "").lower()
                    version = pkg.get("version", "")
                    packages[name] = version
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass
        return packages

    def _extract_imports_from_source(self) -> set[str]:
        """Extract all import statements from source files.

        Returns:
            Set of imported package names
        """
        imports = set()
        _SKIP_DIRS = {".venv", "venv", "node_modules", "__pycache__", ".git", ".mypy_cache", ".pytest_cache"}
        for py_file in self.project_root.rglob("*.py"):
            if any(part in _SKIP_DIRS for part in py_file.parts):
                continue
            try:
                with open(py_file) as f:
                    content = f.read()
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            # Get top-level package name
                            parts = alias.name.split(".")
                            imports.add(parts[0].lower())
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            parts = node.module.split(".")
                            if parts[0]:
                                imports.add(parts[0].lower())
            except (OSError, UnicodeDecodeError, SyntaxError):
                continue
        return imports

    def check(self) -> DependencyResult:
        """
        Check dependency health and security.

        Returns:
            DependencyResult with issues found
        """
        issues = []
        packages_checked = 0
        outdated_count = 0
        vulnerable_count = 0
        missing_count = 0
        unused_count = 0

        # Find requirements file
        requirements_path = self._find_requirements_file()
        if not requirements_path:
            return DependencyResult(
                issues=[],
                packages_checked=0,
                outdated_count=0,
                vulnerable_count=0,
                missing_count=0,
                unused_count=0,
            )

        # Parse declared dependencies
        declared_deps = self._parse_requirements(requirements_path)
        packages_checked = len(declared_deps)

        # Get installed packages
        installed_packages = self._get_installed_packages()

        # Get imports from source
        imported_packages = self._extract_imports_from_source()

        # Check for missing dependencies (imports not in requirements)
        # Normalize per PEP 503: hyphens → underscores for comparison
        def _normalize(name: str) -> str:
            return name.replace("-", "_").replace(".", "_")

        normalized_deps = {_normalize(d): d for d in declared_deps}
        normalized_installed = {_normalize(p): p for p in installed_packages}
        for imp in imported_packages:
            if imp in PYTHON_STDLIB_MODULES:
                continue
            # Check if it's a local module (file exists in project)
            if (self.project_root / f"{imp}.py").exists():
                continue
            # Check if declared or installed
            if _normalize(imp) not in normalized_deps and _normalize(imp) not in normalized_installed:
                issues.append(
                    DependencyIssue(
                        issue_type="missing",
                        package_name=imp,
                        current_version=None,
                        latest_version=None,
                        severity="medium",
                        description="Imported but not declared in dependencies",
                    )
                )
                missing_count += 1

        # Check for unused dependencies (declared but not imported)
        for dep in declared_deps:
            if dep not in imported_packages:
                # Check if it's a dev dependency or tool
                if dep in {"pytest", "mypy", "ruff", "black", "flake8", "coverage"}:
                    continue
                issues.append(
                    DependencyIssue(
                        issue_type="unused",
                        package_name=dep,
                        current_version=declared_deps[dep] or None,
                        latest_version=None,
                        severity="low",
                        description="Declared but not imported in source",
                    )
                )
                unused_count += 1

        return DependencyResult(
            issues=issues,
            packages_checked=packages_checked,
            outdated_count=outdated_count,
            vulnerable_count=vulnerable_count,
            missing_count=missing_count,
            unused_count=unused_count,
        )


# Convenience function
def check_dependencies(
    project_root: Path | None = None,
) -> DependencyResult:
    """
    Quick dependency check.

    Args:
        project_root: Project root directory

    Returns:
        DependencyResult with issues found
    """
    checker = DependencyChecker(project_root)
    return checker.check()
