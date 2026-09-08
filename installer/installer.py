"""AXIS-Setup — professional Windows installer for the AXIS laboratory suite.

Bootstraps a self-contained installation:
  1. Resolves and downloads the AXIS application runtime from the GitHub release.
  2. Downloads Android platform-tools (adb, fastboot) from Google's repository.
  3. Downloads scrcpy from its official GitHub release.
  4. Installs everything under the selected folder and creates shortcuts.

Runnable as plain Python (python installer/installer.py) or packaged with
PyInstaller into AXIS-Setup.exe (see installer/installer.spec).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

GITHUB_REPO = "Davi0777s/AXIS-Android-Research"
AXIS_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
PLATFORM_TOOLS_URL = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
SCRCPY_API = "https://api.github.com/repos/genymobile/scrcpy/releases/latest"
GIT_WINDOWS_URL = "https://git-scm.com/download/win"

DEFAULT_INSTALL_DIR = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "AXIS")
START_MENU_DIR = os.path.join(
    os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "AXIS"
)
DESKTOP_DIR = os.path.join(os.environ.get("USERPROFILE", ""), "Desktop")

_UA = {"User-Agent": "AXIS-Setup/1.0"}


def emit(line: str = "") -> None:
    print(line, flush=True)


def _urlopen(url: str, timeout: int = 60):
    req = urllib.request.Request(url, headers=_UA)
    return urllib.request.urlopen(req, timeout=timeout)


def http_json(url: str) -> Any:
    with _urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))


def download(url: str, dest: Path, label: str) -> None:
    """Stream a file to disk with percentage progress."""
    emit(f"[*] Downloading {label}")
    emit(f"    {url}")
    tmp = dest.with_suffix(dest.suffix + ".part")
    with _urlopen(url) as resp, open(tmp, "wb") as out:
        total = int(resp.headers.get("Content-Length", "0") or 0)
        done = 0
        last_pct = -1
        while True:
            chunk = resp.read(1 << 16)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if total:
                pct = int(100 * done / total)
                if pct != last_pct and pct % 10 == 0:
                    emit(f"    {pct:3d}%  ({done / (1 << 20):.1f} MB / {total / (1 << 20):.1f} MB)")
                    last_pct = pct
    os.replace(tmp, dest)
    emit(f"    OK ({dest.stat().st_size / (1 << 20):.1f} MB)")


def safe_extract(zip_path: Path, target: Path) -> None:
    """Extract a zip archive defending against path traversal (zip-slip)."""
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            member_path = (target / member.filename).resolve()
            if not member_path.is_relative_to(target.resolve()):
                raise RuntimeError(f"unsafe zip entry: {member.filename}")
        zf.extractall(target)


def pick_asset(assets: list[dict[str, Any]], prefix: str, suffix: str) -> dict[str, Any] | None:
    """Pick a release asset matching filename prefix + suffix (largest wins)."""
    matches = [
        a for a in assets
        if a.get("name", "").startswith(prefix) and a.get("name", "").endswith(suffix)
    ]
    if not matches:
        return None
    return max(matches, key=lambda a: a.get("size") or 0)


def latest_axis_runtime(tag: str | None = None) -> tuple[str, str]:
    """Return (download_url, asset_name) of the latest AXIS runtime zip."""
    api = AXIS_API
    if tag:
        api = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{tag}"
    data = http_json(api)
    asset = pick_asset(data.get("assets", []), "AXIS-v", ".zip")
    if asset is None:
        raise RuntimeError("No AXIS runtime asset found in the release.")
    return asset["browser_download_url"], asset["name"]


def scrcpy_dir_name(asset_name: str) -> str:
    """Map a scrcpy release asset name to its extracted directory name."""
    return asset_name[: -len(".zip")] if asset_name.endswith(".zip") else asset_name


def latest_scrcpy() -> tuple[str, str]:
    """Return (download_url, extracted_dir_name) for the latest scrcpy win64 build."""
    data = http_json(SCRCPY_API)
    asset = pick_asset(data.get("assets", []), "scrcpy-win64-", ".zip")
    if asset is None:
        raise RuntimeError("No scrcpy win64 asset found in the latest release.")
    name: str = asset["name"]
    return asset["browser_download_url"], scrcpy_dir_name(name)


def git_bash_present() -> bool:
    for candidate in (
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files (x86)\Git\bin\bash.exe",
    ):
        if os.path.isfile(candidate):
            return True
    return shutil.which("bash") is not None


def create_shortcut(lnk: Path, target: Path, workdir: Path, icon: Path) -> bool:
    ps = (
        "$w = New-Object -ComObject WScript.Shell;"
        + f"$s = $w.CreateShortcut({str(lnk)!r});"
        + f"$s.TargetPath = {str(target)!r};"
        + f"$s.WorkingDirectory = {str(workdir)!r};"
        + f"$s.IconLocation = {str(icon)!r};"
        + "$s.Save()"
    )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            check=True, capture_output=True,
        )
        return True
    except Exception as exc:  # noqa: BLE001 - non-fatal, report and continue
        emit(f"    Warning: could not create shortcut {lnk.name}: {exc}")
        return False


def run_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AXIS professional installer")
    parser.add_argument("--dir", default=DEFAULT_INSTALL_DIR, help="installation directory")
    parser.add_argument("--runtime-zip", default=None, help="use a local AXIS runtime zip instead of downloading")
    parser.add_argument("--tag", default=None, help="pin a specific AXIS release tag (default: latest)")
    parser.add_argument("--skip-tools", action="store_true", help="skip platform-tools/scrcpy downloads")
    parser.add_argument("--skip-shortcuts", action="store_true", help="do not create shortcuts")
    args = parser.parse_args(argv)

    app_dir = Path(args.dir).expanduser()
    tools_dir = app_dir / "tools"

    emit("=" * 62)
    emit("AXIS Android eXploration & Inspection Suite")
    emit("Professional installer")
    emit("=" * 62)
    emit(f"[*] Installation directory: {app_dir}")

    if not git_bash_present():
        emit("[!] Git for Windows not detected. Helper scripts need Git Bash.")
        emit(f"    Install it from {GIT_WINDOWS_URL}")

    app_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="axis-setup-") as tmp:
        tmpdir = Path(tmp)

        if args.runtime_zip:
            emit("[*] Using local runtime archive")
            runtime_zip = Path(args.runtime_zip)
            if not runtime_zip.is_file():
                emit(f"[ERROR] Runtime archive not found: {runtime_zip}")
                return 2
        else:
            url, name = latest_axis_runtime(args.tag)
            runtime_zip = tmpdir / name
            download(url, runtime_zip, "AXIS application runtime")

        if not args.skip_tools:
            pt_zip = tmpdir / "platform-tools-latest-windows.zip"
            download(PLATFORM_TOOLS_URL, pt_zip, "Android platform-tools (adb, fastboot)")
            emit("[*] Installing platform-tools")
            safe_extract(pt_zip, tools_dir)

            scr_url, scr_dir = latest_scrcpy()
            scr_zip = tmpdir / (scr_dir + ".zip")
            download(scr_url, scr_zip, "scrcpy (screen mirroring)")
            emit("[*] Installing scrcpy")
            safe_extract(scr_zip, tools_dir)

        emit("[*] Installing AXIS application")
        safe_extract(runtime_zip, app_dir)

        exe = app_dir / "AXIS.exe"
        if not exe.is_file():
            emit(f"[ERROR] AXIS.exe not found after extraction in {app_dir}")
            return 3

        if not args.skip_shortcuts:
            emit("[*] Creating shortcuts")
            icon = app_dir / "assets" / "axis.ico"
            if not icon.is_file():
                icon = exe
            if not os.path.isdir(START_MENU_DIR):
                os.makedirs(START_MENU_DIR, exist_ok=True)
            create_shortcut(Path(START_MENU_DIR) / "AXIS.lnk", exe, app_dir, icon)
            create_shortcut(Path(DESKTOP_DIR) / "AXIS.lnk", exe, app_dir, icon)

    tools_ok = (tools_dir / "platform-tools" / "adb.exe").is_file() or args.skip_tools
    scr_ok = any((tools_dir / d).is_dir() for d in os.listdir(tools_dir)
                 if d.startswith("scrcpy-win")) or args.skip_tools

    emit("-" * 62)
    emit("Installation completed.")
    emit(f"  AXIS:            {app_dir / 'AXIS.exe'}")
    emit(f"  platform-tools:  {'OK' if tools_ok else 'MISSING (adb on PATH fallback)'}")
    emit(f"  scrcpy:          {'OK' if scr_ok else 'MISSING'}")
    emit(f"  Config:          {app_dir / 'axis.toml'}")
    emit("-" * 62)
    if not tools_ok or not scr_ok:
        emit("[i] You can add tools later by running the installer again (repair mode).")
    emit("[?] Launch AXIS now? (Y/n) ", )
    answer = input().strip().lower()
    if answer in ("", "y", "yes"):
        subprocess.Popen([str(exe)], cwd=str(app_dir))
    return 0


if __name__ == "__main__":
    sys.exit(run_main())