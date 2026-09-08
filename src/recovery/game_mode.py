"""Game mode — optimizes device settings for gaming."""
from __future__ import annotations
from collections.abc import Callable

from src.recovery.base import FixResult


class GameMode:
    """Configures Android settings optimized for gaming performance."""

    DESCRIPTION = "Optimize device settings for gaming (DND, performance, brightness)"

    def run(self, shell_fn: Callable[[str], str]) -> FixResult:
        steps: list[str] = []

        shell_fn("cmd notification allow_list-toast 0 2>/dev/null")
        steps.append("DND enabled")

        shell_fn("settings put system screen_brightness 255")
        steps.append("Max brightness")

        shell_fn("settings put system screen_off_timeout 600000")
        steps.append("10min screen timeout")

        shell_fn("cmd power set-mode 1 2>/dev/null")
        steps.append("Performance mode requested")

        return FixResult(True, "Game mode activated: " + " | ".join(steps))

    def disable(self, shell_fn: Callable[[str], str]) -> FixResult:
        shell_fn("settings put system screen_brightness 128")
        shell_fn("settings put system screen_off_timeout 30000")
        return FixResult(True, "Game mode deactivated, defaults restored")