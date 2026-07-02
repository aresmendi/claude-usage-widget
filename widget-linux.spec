# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para Linux (binario onefile, empaquetado luego en AppImage)
# Uso: pyinstaller widget-linux.spec
import os
import customtkinter

_ctk_path = os.path.dirname(customtkinter.__file__)

a = Analysis(
    ["widget/main.py"],
    pathex=["."],
    binaries=[],
    datas=[
        (_ctk_path, "customtkinter"),
        ("assets/icon.png", "assets"),
    ],
    hiddenimports=[
        "pystray._xorg",
        "pystray._appindicator",
        "pystray._gtk",
        "browser_cookie3",
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
    upx=False,
    console=False,
)
