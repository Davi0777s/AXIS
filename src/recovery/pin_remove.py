"""PIN remove — clears lock screen credential via ADB."""
from __future__ import annotations
from collections.abc import Callable

from src.recovery.base import FixResult


class PINRemove:
    """Removes lock screen PIN/pattern/password via ADB."""

    DESCRIPTION = "Remove lock screen credential (requires USB debugging)"

    def run(self, shell_fn: Callable[[str], str]) -> FixResult:
        result = shell_fn("locksettings clear --old \"\" 2>&1")
        if "cleared" in result.lower() or "success" in result.lower():
            return FixResult(True, "Lock screen credential cleared", result)

        result2 = shell_fn(
            "rm /data/system/locksettings.db* 2>&1; "
            "rm /data/system/gatekeeper.password.key 2>&1; "
            "rm /data/system/gatekeeper.pattern.key 2>&1"
        )
        return FixResult(
            False,
            "Attempted lock settings clear. May require reboot.",
            result or result2,
        )