# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for the AXIS-Setup installer (one-file, console).
a = Analysis(
    ["installer.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=["PySide6", "PyQt5", "shiboken6"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="AXIS-Setup",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)