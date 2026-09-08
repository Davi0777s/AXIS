# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for AXIS (onedir / portable-folder build).

The executable is designed to live at the root of a portable AXIS home:
``AXIS.exe`` plus ``scripts/``, ``wifi-fix/``, ``assets/``, ``axis.toml``
and (user-supplied) ``tools/`` + ``firmware/`` next to it. ``build_exe.ps1``
copies those folders into ``dist/AXIS/`` after the build.
"""
import os

import PySide6

## Include Qt plugins so the frozen app is self-contained (Qt otherwise
## falls back to the machine's site-packages PySide6 and breaks on a
## machine where PySide6 is not installed).
_QT_PLUGIN_DIR = os.path.join(os.path.dirname(PySide6.__file__), "plugins")
_PLUGIN_SUBDIRS = (
    "platforms",          # qwindows/qminimal/qoffscreen (QPA)
    "imageformats",       # qsvg, qico, qjpeg, ... (skull-icon.svg)
    "iconengines",        # SVG icon engine
    "styles",             # e.g. windowsvista / fusion style plugins
    "platforminputcontexts",
    "generic",
    "tls",
    "networkinformation",
)
_datas = [("assets", "assets"), ("axis.toml", ".")]
for _sub in _PLUGIN_SUBDIRS:
    _src = os.path.join(_QT_PLUGIN_DIR, _sub)
    if os.path.isdir(_src):
        _datas.append((_src, os.path.join("PySide6", "plugins", _sub)))

block_cipher = None

a = Analysis(
    ["axis.py"],
    pathex=[],
    binaries=[],
    datas=_datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AXIS",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["assets/axis.ico"],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="AXIS",
)