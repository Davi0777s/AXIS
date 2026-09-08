"""WiFi SAE/WPA3 fix — disables SAE mode for incompatible networks."""
from __future__ import annotations
from collections.abc import Callable

from src.recovery.base import FixResult


class WiFiFix:
    """Disables WPA3 SAE on Android devices with WiFi compatibility issues."""

    DESCRIPTION = "Disable WPA3 SAE mode for WiFi networks that don't support it"

    def run(self, shell_fn: Callable[[str], str]) -> FixResult:
        check = shell_fn("settings get global wifi_sae_disabled 2>/dev/null")
        if "1" in check:
            return FixResult(True, "SAE already disabled", check.strip())

        result = shell_fn("settings put global wifi_sae_disabled 1")
        verify = shell_fn("settings get global wifi_sae_disabled 2>/dev/null")

        if "1" in verify:
            return FixResult(True, "WPA3 SAE disabled successfully", verify.strip())
        return FixResult(False, "Failed to apply WiFi fix", result)

    def verify(self, shell_fn: Callable[[str], str]) -> str:
        return shell_fn("settings get global wifi_sae_disabled 2>/dev/null").strip()