"""Screen unlock — helper for devices with broken screens."""
from __future__ import annotations
from collections.abc import Callable

from src.recovery.base import FixResult


class ScreenUnlock:
    """Assists with screen unlock on devices with damaged displays."""

    DESCRIPTION = "Disable screen lock and enable stay-awake for broken screens"

    def run(self, shell_fn: Callable[[str], str]) -> FixResult:
        steps: list[str] = []

        shell_fn("settings put system screen_off_timeout 2147483647")
        steps.append("Screen timeout set to infinite")

        shell_fn("settings put global stay_on_while_plugged_in 3")
        steps.append("Stay awake while charging enabled")

        r3 = shell_fn("wm dismiss-keyguard 2>&1")
        if "not" in r3.lower() and "found" in r3.lower():
            steps.append("Keyguard dismiss attempted (may need PIN removal first)")
        else:
            steps.append("Keyguard dismissed")

        return FixResult(True, " | ".join(steps))

    def verify(self, shell_fn: Callable[[str], str]) -> str:
        timeout = shell_fn("settings get system screen_off_timeout").strip()
        stay = shell_fn("settings get global stay_on_while_plugged_in").strip()
        return f"Timeout: {timeout}ms, Stay-on: {stay}"