"""Path utilities for AXIS."""
from __future__ import annotations
from pathlib import Path


def ensure_dir(path: Path) -> Path:
    """Create directory if it doesn't exist, return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(name: str) -> str:
    """Sanitize a string for use as a filename."""
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
