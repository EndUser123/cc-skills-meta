"""Tests for gto_verify_wrapper module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


class TestGtoVerifyWrapper:
    """Smoke tests for gto_verify_wrapper main function."""

    def test_module_can_be_imported(self) -> None:
        """Test that gto_verify_wrapper can be imported."""
        from gto.hooks import gto_verify_wrapper

        assert gto_verify_wrapper is not None

    def test_has_main_function(self) -> None:
        """Test that main function exists."""
        from gto.hooks import gto_verify_wrapper

        assert hasattr(gto_verify_wrapper, "main")
        assert callable(gto_verify_wrapper.main)
