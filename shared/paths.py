from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False)) and hasattr(sys, "_MEIPASS")


def bundle_dir() -> Path:
    """Directory containing bundled read-only resources.

    - Dev: repo root
    - PyInstaller: sys._MEIPASS
    """

    if is_frozen():
        return Path(getattr(sys, "_MEIPASS")).resolve()
    return Path(__file__).resolve().parents[1]


def runtime_dir() -> Path:
    """Writable runtime directory.

    - Dev: repo root
    - PyInstaller: folder containing the .exe
    """

    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def assets_dir() -> Path:
    return bundle_dir() / "assets"


def data_dir() -> Path:
    path = runtime_dir() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def models_dir() -> Path:
    path = runtime_dir() / "models"
    path.mkdir(parents=True, exist_ok=True)
    return path
