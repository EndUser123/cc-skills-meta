"""Test gitready main module."""


from core import __version__
from core.main import get_version


def test_get_version():
    """Test that get_version returns the correct version."""
    assert get_version() == __version__
    assert isinstance(get_version(), str)


def test_version_format():
    """Test that version follows semantic versioning."""
    parts = __version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
