# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

# NOTE: PyInstaller executes spec files via `exec()` and does not always define
# `__file__`. Assume the spec is invoked from the repo root.
project_root = Path.cwd().resolve()

# Collect binary/data-heavy deps required by the GUI and the bundled scripts.
datas = []
binaries = []
hiddenimports = []

for pkg in ("cv2", "PIL"):
    pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

# Bundle our app resources.
datas += [
    (str(project_root / "assets"), "assets"),
    # We run these scripts via runpy when the exe is invoked with a subcommand.
    (str(project_root / "scripts"), "scripts"),
]

block_cipher = None

a = Analysis(
    [str(project_root / "frontend" / "attendance_app.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="FaceAttendance",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    exclude_binaries=False,
)
