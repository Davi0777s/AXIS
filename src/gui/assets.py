"""Runtime asset resolution (PySide6 icons/images) for AXIS.

Works both from a source checkout (``assets/`` next to ``axis.toml``) and
from a PyInstaller-frozen bundle (assets shipped inside ``sys._MEIPASS``).
"""
from __future__ import annotations
import os
import sys
from pathlib import Path


def _asset_base() -> Path:
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        if (exe_dir / "assets").is_dir():
            return exe_dir
        return Path(getattr(sys, "_MEIPASS", exe_dir))
    from src.core.config import find_root
    return find_root()


def asset_path(name: str) -> Path:
    return _asset_base() / "assets" / name


def asset_exists(name: str) -> bool:
    return asset_path(name).is_file()


def load_icon(name: str):
    """Build a QIcon for an asset, or None if it cannot be loaded."""
    from PySide6.QtGui import QIcon
    p = asset_path(name)
    if not p.is_file():
        return None
    return QIcon(str(p))