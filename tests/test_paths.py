from __future__ import annotations

import os
from pathlib import Path

from shared.paths import data_dir, models_dir, runtime_dir


def test_runtime_dir_override(tmp_path: Path) -> None:
    os.environ["FACEATTENDANCE_RUNTIME_DIR"] = str(tmp_path)
    try:
        assert runtime_dir() == tmp_path
        assert data_dir().exists()
        assert models_dir().exists()
    finally:
        os.environ.pop("FACEATTENDANCE_RUNTIME_DIR", None)
