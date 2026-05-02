"""Tests for workflow_hygiene detector — detects uncommitted changes."""
import subprocess
from pathlib import Path

from skills.gto.__lib.workflow_hygiene import detect_workflow_hygiene


def _init_git_repo(tmp_path: Path) -> Path:
    """Create a git repo with one committed file."""
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=str(tmp_path), capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=str(tmp_path), capture_output=True, check=True,
    )
    (tmp_path / "README.md").write_text("# Test\n")
    subprocess.run(["git", "add", "README.md"], cwd=str(tmp_path), capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=str(tmp_path), capture_output=True, check=True,
    )
    return tmp_path


class TestWorkflowHygieneDetector:
    def test_clean_repo_returns_empty(self, tmp_path):
        root = _init_git_repo(tmp_path)
        findings = detect_workflow_hygiene(root)
        assert findings == []

    def test_modified_file_detected(self, tmp_path):
        root = _init_git_repo(tmp_path)
        (root / "README.md").write_text("# Modified\n")
        findings = detect_workflow_hygiene(root)
        assert len(findings) >= 1
        assert any(f.id == "WORKFLOW-001" for f in findings)

    def test_deleted_file_detected(self, tmp_path):
        root = _init_git_repo(tmp_path)
        (root / "README.md").unlink()
        findings = detect_workflow_hygiene(root)
        assert len(findings) >= 1
        assert any(f.id == "WORKFLOW-002" for f in findings)

    def test_no_git_returns_empty(self, tmp_path):
        findings = detect_workflow_hygiene(tmp_path)
        assert findings == []

    def test_untracked_in_packages_detected(self, tmp_path):
        root = _init_git_repo(tmp_path)
        pkg_dir = root / "packages" / "my-pkg"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "file.py").write_text("pass")
        findings = detect_workflow_hygiene(root)
        assert any(f.id == "WORKFLOW-003" for f in findings)
