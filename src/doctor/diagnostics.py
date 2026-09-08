"""System diagnostics engine — runs all health checks on a connected device."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


class Severity(str, Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    severity: Severity
    message: str
    details: str = ""

    @property
    def icon(self) -> str:
        return {"ok": "\u2705", "warning": "\u26a0\ufe0f", "error": "\u274c", "info": "\u2139\ufe0f"}[self.severity.value]


@dataclass
class DiagnosticsEngine:
    """Runs diagnostic checks against a connected Android device."""

    _checks: list[Callable[["DiagnosticsEngine"], CheckResult]] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        self._checks = [
            self._check_adb,
            self._check_selinux,
            self._check_props,
            self._check_fstab,
            self._check_root,
            self._check_storage,
            self._check_battery,
        ]

    def run_all(self, shell_fn: Callable[[str], str]) -> list[CheckResult]:
        results: list[CheckResult] = []
        for check in self._checks:
            try:
                results.append(check(shell_fn))
            except Exception as exc:
                results.append(CheckResult(
                    name=check.__name__,
                    severity=Severity.ERROR,
                    message=f"Check failed: {exc}",
                ))
        return results

    def _check_adb(self, shell: Callable[[str], str]) -> CheckResult:
        out = shell("echo ok")
        if "ok" in out:
            return CheckResult("ADB Connection", Severity.OK, "Device is responsive")
        return CheckResult("ADB Connection", Severity.ERROR, "Device not responding")

    def _check_selinux(self, shell: Callable[[str], str]) -> CheckResult:
        mode = shell("getenforce").strip().lower()
        if mode == "enforcing":
            return CheckResult("SELinux", Severity.OK, "SELinux is enforcing")
        if mode == "permissive":
            return CheckResult("SELinux", Severity.WARNING, "SELinux is permissive (less secure)")
        return CheckResult("SELinux", Severity.INFO, f"SELinux mode: {mode or 'unknown'}")

    def _check_props(self, shell: Callable[[str], str]) -> CheckResult:
        debug = shell("getprop ro.debuggable").strip()
        if debug == "1":
            return CheckResult("Build Props", Severity.WARNING, "Device is debuggable (userdebug/eng build)")
        return CheckResult("Build Props", Severity.OK, "Production build")

    def _check_fstab(self, shell: Callable[[str], str]) -> CheckResult:
        fstab = shell("cat /proc/mounts 2>/dev/null | head -5").strip()
        if fstab:
            count = len(fstab.splitlines())
            return CheckResult("Filesystem", Severity.OK, f"{count} mount points active")
        return CheckResult("Filesystem", Severity.WARNING, "Could not read mount points")

    def _check_root(self, shell: Callable[[str], str]) -> CheckResult:
        whoami = shell("id").strip()
        if "uid=0" in whoami:
            return CheckResult("Root Access", Severity.INFO, "Device has root access")
        return CheckResult("Root Access", Severity.OK, "No root access (standard)")

    def _check_storage(self, shell: Callable[[str], str]) -> CheckResult:
        df = shell("df /data 2>/dev/null | tail -1").strip()
        if not df:
            return CheckResult("Storage", Severity.WARNING, "Could not read storage info")
        parts = df.split()
        for part in reversed(parts):
            if part.endswith("%"):
                usage = int(part.rstrip("%"))
                sev = Severity.OK if usage < 90 else Severity.WARNING
                return CheckResult("Storage", sev, f"Data partition: {part} used")
        return CheckResult("Storage", Severity.INFO, f"Storage: {df}")

    def _check_battery(self, shell: Callable[[str], str]) -> CheckResult:
        level = shell("dumpsys battery 2>/dev/null | grep level | cut -d: -f2 | tr -d ' '").strip()
        if not level:
            return CheckResult("Battery", Severity.INFO, "Could not read battery level")
        try:
            pct = int(level)
            sev = Severity.OK if pct > 20 else Severity.WARNING
            return CheckResult("Battery", sev, f"Battery: {pct}%")
        except ValueError:
            return CheckResult("Battery", Severity.INFO, f"Battery level: {level}")
