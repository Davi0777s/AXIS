"""Subprocess runner for executing AXIS bash helper scripts."""
from __future__ import annotations
import subprocess
import os
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from threading import Thread, Event

_SCRIPT_RE = re.compile(r"^[A-Za-z0-9_./\-]+$")
_SCRIPT_MAX = 128


def _script_cmd(bash: str, root: str, script_path: str) -> list[str]:
    """Build the bash invocation without interpolating user-controlled paths.

    ``root`` and ``script_path`` are passed as positional parameters
    (``$1``/``$2``) rather than spliced into the ``-c`` program text, so a
    value containing quotes or ``$()`` cannot break out of the quotes.
    """
    return [bash, "-c", 'cd "$1" && exec bash "$2"', "axis-run", root, script_path]


def _git_bash_path() -> str:
    """Find Git Bash on Windows."""
    candidates = [
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
        os.path.expanduser(r"~\scoop\shims\bash.exe"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return "bash"


@dataclass
class ScriptResult:
    success: bool
    output: str
    returncode: int


class ScriptRunner:
    """Runs AXIS bash scripts with live output streaming."""

    def __init__(self, root: str | None = None) -> None:
        self._root = self._resolve_root(root)
        self._bash = _git_bash_path()
        self._process: subprocess.Popen[str] | None = None
        self._stop_event = Event()

    @staticmethod
    def _resolve_root(root: str | None) -> str:
        """Resolve the system root that actually holds scripts/ (AXIS itself).

        AXIS is self-contained: its own folder carries scripts/, tools/ and
        wifi-fix/. A legacy sibling ``MARE`` folder is accepted as a fallback
        for pre-consolidation installs.
        """
        from src.core.config import find_root

        project = str(find_root())
        candidates: list[str] = []
        if root:
            candidates.append(root)
        if project not in candidates:
            candidates.append(project)
        candidates.append(os.path.join(project.rstrip("\\/"), "..", "MARE"))

        for c in candidates:
            if c and os.path.isdir(os.path.join(c, "scripts")):
                return c
        return candidates[0] if candidates else project

    @property
    def root(self) -> str:
        return self._root

    def _build_env(self, env_overrides: dict[str, str] | None = None) -> dict[str, str]:
        """Build a clean env for child processes.

        Neutralizes stray ADB installs (e.g. C:\\adb with an old server) that live
        in the system PATH and fight with MARE's platform-tools over port 5037.
        AXIS's own tools dir is put FIRST so scripts and scrcpy always use the
        correct adb version.
        """
        env = os.environ.copy()
        env["MSYS_NO_PATHCONV"] = "1"
        env["MSYS2_ARG_CONV_EXCL"] = "*"

        path_entries = env.get("PATH", "").split(os.pathsep)

        # Remove any directory containing an adb.exe we don't own.
        platform_tools = os.path.join(self._root, "tools", "platform-tools")
        filtered: list[str] = []
        for entry in path_entries:
            if not entry:
                continue
            candidate = os.path.join(entry, "adb.exe")
            if os.path.isfile(candidate) and not os.path.samefile(candidate, os.path.join(platform_tools, "adb.exe")):
                continue
            filtered.append(entry)

        # AXIS tools first so bare `adb` resolves to the correct version.
        if platform_tools not in filtered:
            filtered.insert(0, platform_tools)
        env["PATH"] = os.pathsep.join(filtered)

        if env_overrides:
            env.update(env_overrides)
        return env

    def run_script(
        self,
        script_rel: str,
        env_overrides: dict[str, str] | None = None,
        on_output: Callable[[str], None] | None = None,
        timeout: float = 120.0,
    ) -> ScriptResult:
        # Boundary validation: the script name must be a plain relative path,
        # and its resolved target must live inside the project root. This keeps a
        # caller from injecting shell metacharacters or traversing out of the
        # allowlisted scripts directory.
        if (
            not script_rel
            or len(script_rel) > _SCRIPT_MAX
            or not _SCRIPT_RE.match(script_rel)
            or script_rel.startswith(("/", "\\"))
        ):
            return ScriptResult(False, f"Invalid script path: {script_rel!r}", -4)

        base = os.path.realpath(self._root)
        script_path = os.path.join(self._root, script_rel)
        target = os.path.realpath(script_path)
        if not (target == base or target.startswith(base + os.sep)):
            return ScriptResult(False, "Script path escapes project root", -4)

        if not os.path.isfile(script_path):
            return ScriptResult(False, f"Script not found: {script_rel}", -1)

        env = self._build_env(env_overrides)

        # The paths are passed as positional parameters (`$1`, `$2`) instead of
        # being interpolated into the -c string: a value containing quotes or
        # `` $() `` cannot break out of the double quotes.
        cmd = _script_cmd(self._bash, self._root, script_path)
        output_lines: list[str] = []
        self._stop_event.clear()

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )

            assert self._process.stdout is not None
            for line in self._process.stdout:
                if self._stop_event.is_set():
                    self._process.kill()
                    break
                clean = line.rstrip("\n\r")
                if clean:
                    output_lines.append(clean)
                    if on_output:
                        on_output(clean)

            self._process.wait(timeout=timeout if timeout and timeout > 0 else None)
            rc = self._process.returncode
            return ScriptResult(rc == 0, "\n".join(output_lines), rc)

        except subprocess.TimeoutExpired:
            if self._process:
                self._process.kill()
            return ScriptResult(False, "Script timed out", -2)
        except Exception as exc:
            return ScriptResult(False, f"Error: {exc}", -3)
        finally:
            self._process = None

    def run_script_async(
        self,
        script_rel: str,
        env_overrides: dict[str, str] | None = None,
        on_output: Callable[[str], None] | None = None,
        on_done: Callable[[ScriptResult], None] | None = None,
    ) -> Thread:
        def _worker() -> None:
            result = self.run_script(script_rel, env_overrides, on_output)
            if on_done:
                on_done(result)

        t = Thread(target=_worker, daemon=True)
        t.start()
        return t

    def stop(self) -> None:
        self._stop_event.set()
        if self._process:
            self._process.kill()

    def run_adb(
        self,
        *args: str,
        serial: str | None = None,
        timeout: float = 15.0,
    ) -> ScriptResult:
        adb_path = os.path.join(self._root, "tools", "platform-tools", "adb.exe")
        if not os.path.isfile(adb_path):
            adb_path = "adb"
        cmd = [adb_path]
        if serial:
            cmd.extend(["-s", serial])
        cmd.extend(args)
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            return ScriptResult(proc.returncode == 0, proc.stdout.strip(), proc.returncode)
        except FileNotFoundError:
            return ScriptResult(False, "adb not found", -1)
        except subprocess.TimeoutExpired:
            return ScriptResult(False, "timeout", -2)

    def get_scrcpy_path(self) -> str | None:
        tools = os.path.join(self._root, "tools")
        if not os.path.isdir(tools):
            return None
        for d in os.listdir(tools):
            if d.startswith("scrcpy-win"):
                candidate = os.path.join(tools, d, "scrcpy.exe")
                if os.path.isfile(candidate):
                    return candidate
        return None
