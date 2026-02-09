# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for ft1000mp CLI."""

a = Analysis(
    ['cli.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'serial.tools.list_ports',
        'serial.tools.list_ports_windows',
        'serial.tools.list_ports_linux',
        'serial.tools.list_ports_posix',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ft1000mp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
)
