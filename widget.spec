# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para Windows (.exe)
# Uso: pyinstaller widget.spec
import os
import customtkinter

_ctk_path = os.path.dirname(customtkinter.__file__)

a = Analysis(
    ["widget/main.py"],
    pathex=["."],
    binaries=[],
    datas=[
        (_ctk_path, "customtkinter"),
        ("assets/icon.ico", "assets"),
    ],
    hiddenimports=[
        "plyer.platforms.win.notification",
        "browser_cookie3",
        "pystray._win32",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="claude-usage-widget",
    debug=False,
    strip=False,
    upx=True,
    console=False,          # sin ventana de consola
    icon="assets/icon.ico",
)
