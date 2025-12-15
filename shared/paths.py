from __future__ import annotations

import os
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
    - PyInstaller: folder containing the .exe (portable) OR LocalAppData fallback
    """

    override = os.getenv("FACEATTENDANCE_RUNTIME_DIR")
    if override:
        return Path(override).expanduser().resolve()

    if is_frozen():
        exe_dir = Path(sys.executable).resolve().parent
        # Prefer portable behavior when possible (write next to exe).
        try:
            test_path = exe_dir / ".faceattendance_write_test"
            test_path.write_text("ok", encoding="utf-8")
            test_path.unlink(missing_ok=True)
            return exe_dir
        except OSError:
            base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
            if base:
                return (Path(base) / "FaceAttendance").resolve()
            # Last resort: fall back to exe directory.
            return exe_dir
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
