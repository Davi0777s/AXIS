"""ADB client wrapper — subprocess calls to adb."""
from __future__ import annotations
import os
import subprocess
from dataclasses import dataclass


def _no_window() -> int:
    return subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def _default_adb_path() -> str:
    """Resolve AXIS's own platform-tools adb, falling back to PATH `adb`.

    A bare `adb` may resolve to a stray older install on the system PATH
    (e.g. C:\\adb = server v31) that fights with our adb over the shared
    server (port 5037). Pin to AXIS's bundled binary whenever available.
    """
    from src.core.config import find_root
    root = find_root()
    candidate = os.path.join(root, "tools", "platform-tools", "adb.exe")
    if os.path.isfile(candidate):
        return candidate
    return "adb"


@dataclass(frozen=True, slots=True)
class AdbResult:
    success: bool
    stdout: str
    stderr: str
    returncode: int


class AdbClient:
    """Thin wrapper around the adb binary."""

    def __init__(self, adb_path: str | None = None, serial: str | None = None) -> None:
        self._adb = adb_path if adb_path else _default_adb_path()
        self._serial = serial

    def _base_cmd(self) -> list[str]:
        cmd = [self._adb]
        if self._serial:
            cmd.extend(["-s", self._serial])
        return cmd

    def run(self, *args: str, timeout: float = 15.0) -> AdbResult:
        cmd = self._base_cmd() + list(args)
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=_no_window(),
            )
            return AdbResult(
                success=proc.returncode == 0,
                stdout=proc.stdout.strip(),
                stderr=proc.stderr.strip(),
                returncode=proc.returncode,
            )
        except FileNotFoundError:
            return AdbResult(False, "", "adb not found", -1)
        except subprocess.TimeoutExpired:
            return AdbResult(False, "", "timeout", -2)

    def is_available(self) -> bool:
        return self.run("version").success

    def get_devices(self) -> list[dict[str, str]]:
        """Return all ADB transports with their raw state.

        Includes ``unauthorized``, ``offline``, ``recovery`` and ``bootloader``
        so the state is not silently dropped. Only ``device`` transports are
        queried for extra props (others can't answer getprop).
        """
        result = self.run("devices", "-l")
        if not result.success:
            return []
        devices = []
        for line in result.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2:
                info = {"serial": parts[0], "state": parts[1]}
                for part in parts[2:]:
                    if ":" in part:
                        k, v = part.split(":", 1)
                        info[k] = v
                devices.append(info)
        return devices

    def get_prop(self, prop: str) -> str:
        return self.run("shell", "getprop", prop).stdout

    def shell(self, command: str) -> AdbResult:
        return self.run("shell", command)