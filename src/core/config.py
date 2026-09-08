"""Centralized configuration for AXIS."""
from __future__ import annotations
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]


@dataclass(frozen=True, slots=True)
class Paths:
    root: Path
    firmware: Path = field(init=False)
    build: Path = field(init=False)
    logs: Path = field(init=False)
    tools: Path = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "firmware", self.root / "firmware")
        object.__setattr__(self, "build", self.root / "build")
        object.__setattr__(self, "logs", self.root / "logs")
        object.__setattr__(self, "tools", self.root / "tools")


@dataclass(frozen=True, slots=True)
class Config:
    root: Path
    paths: Paths
    device_codename: str = ""
    device_serial: str = ""
    header_version: int = 4
    compress: str = "gzip"


def find_root(start: Path | None = None) -> Path:
    """Find project root by looking for axis.toml.

    When frozen (PyInstaller), the runtime root is the folder that holds the
    executable — a portable AXIS home that carries ``scripts/``, ``tools/``,
    ``firmware/`` and other user-supplied assets next to the app.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    p = (start or Path.cwd()).resolve()
    while True:
        if (p / "axis.toml").is_file():
            return p
        parent = p.parent
        if parent == p:
            break
        p = parent
    return Path(__file__).resolve().parent.parent.parent


def load(root: Path | None = None) -> Config:
    """Load configuration from axis.toml."""
    root = find_root(root)
    cfg_path = root / "axis.toml"
    data: dict = {}
    if cfg_path.is_file():
        with open(cfg_path, "rb") as f:
            data = tomllib.load(f)

    paths_data = data.get("paths", {})
    paths = Paths(root=root)

    device = data.get("device", {})
    build = data.get("build", {})

    return Config(
        root=root,
        paths=paths,
        device_codename=device.get("codename", ""),
        device_serial=device.get("serial", ""),
        header_version=build.get("header_version", 4),
        compress=build.get("compress", "gzip"),
    )
