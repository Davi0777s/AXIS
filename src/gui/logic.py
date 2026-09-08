"""Shared GUI helper actions (ADB maintenance commands)."""
from __future__ import annotations
import os
import subprocess
import sys

from src.core.config import find_root


def _git_bash_path() -> str:
    candidates = [
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
        os.path.expanduser(r"~\scoop\shims\bash.exe"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return "bash"


def _adb_path() -> str:
    candidate = os.path.join(find_root(), "tools", "platform-tools", "adb.exe")
    if os.path.isfile(candidate):
        return candidate
    return "adb"


def restart_adb_server(timeout: float = 20.0) -> None:
    """kill-server then start-server so a stale ADB daemon re-detects devices."""
    kw: dict = {
        "capture_output": True,
        "text": True,
        "timeout": timeout,
        "creationflags": subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    }
    adb = _adb_path()
    try:
        subprocess.run([adb, "kill-server"], **kw)
        subprocess.run([adb, "start-server"], **kw)
    except Exception:
        pass


def authorize_adb_repair() -> None:
    """Launch AXIS's bundled ``scripts/fix_auth.sh`` in its own console.

    Fixes an ``unauthorized`` ADB state without touching the phone screen
    (Fastboot Vol- + Power -> OrangeFox in RAM -> key injection -> reboot).
    The working directory is the project root so the script can find
    ``tools/`` and ``firmware/stock/`` next to it. The console stays open
    after completion so the user can read the result.
    """
    root = find_root()
    script = os.path.join(root, "scripts", "fix_auth.sh")
    if not os.path.isfile(script):
        return
    bash = _git_bash_path()
    kwargs: dict = {"cwd": str(root)}
    if sys.platform == "win32":
        kwargs["creationflags"] = (
            subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP
        )
    try:
        subprocess.Popen(
            [bash, "-c", "./scripts/fix_auth.sh; echo; read -p 'Pulsa Enter para cerrar...'"],
            **kwargs,
        )
    except Exception:
        pass
