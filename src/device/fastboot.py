"""Fastboot client wrapper — subprocess calls to fastboot."""
from __future__ import annotations
import os
import subprocess
from dataclasses import dataclass


def _no_window() -> int:
    return subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def _default_fastboot_path() -> str:
    from src.core.config import find_root
    root = find_root()
    candidate = os.path.join(root, "tools", "platform-tools", "fastboot.exe")
    if os.path.isfile(candidate):
        return candidate
    return "fastboot"


@dataclass(frozen=True, slots=True)
class FastbootResult:
    success: bool
    stdout: str
    stderr: str
    returncode: int


class FastbootClient:
    """Thin wrapper around the fastboot binary."""

    def __init__(self, fastboot_path: str | None = None, serial: str | None = None) -> None:
        self._fastboot = fastboot_path if fastboot_path else _default_fastboot_path()
        self._serial = serial

    def _base_cmd(self) -> list[str]:
        cmd = [self._fastboot]
        if self._serial:
            cmd.extend(["-s", self._serial])
        return cmd

    def run(self, *args: str, timeout: float = 30.0) -> FastbootResult:
        cmd = self._base_cmd() + list(args)
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=_no_window(),
            )
            return FastbootResult(
                success=proc.returncode == 0,
                stdout=proc.stdout.strip(),
                stderr=proc.stderr.strip(),
                returncode=proc.returncode,
            )
        except FileNotFoundError:
            return FastbootResult(False, "", "fastboot not found", -1)
        except subprocess.TimeoutExpired:
            return FastbootResult(False, "", "timeout", -2)

    def is_available(self) -> bool:
        # `getvar product` would wait blocked on the USB bus until timeout when
        # no device is attached; `devices` returns immediately and only reports
        # an attached transport.
        result = self.run("devices", timeout=5.0)
        if not result.success:
            return False
        return any(
            len(line.split()) >= 2
            for line in result.stdout.splitlines()
            if line.strip()
        )

    def get_vars(self) -> dict[str, str]:
        result = self.run("getvar", "all")
        vars_dict: dict[str, str] = {}
        for line in result.stderr.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                vars_dict[k.strip()] = v.strip()
        return vars_dict

    def get_device_state(self) -> str:
        result = self.run("getvar", "current-slot")
        if result.success:
            return "bootloader"
        return "unknown"