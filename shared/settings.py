from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict

from shared.paths import data_dir


SETTINGS_FILE = data_dir() / "settings.json"


@dataclass
class Settings:
    camera_index: int = 0
    session_seconds: int = 90
    lbph_threshold: float = 90.0
    duplicate_window_minutes: int = 10
    privacy_mode: bool = False
    consent_accepted: bool = False


def _coerce_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"1", "true", "yes", "y", "on"}:
            return True
        if v in {"0", "false", "no", "n", "off"}:
            return False
    return default


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _coerce_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return default


def load_settings(path: Path = SETTINGS_FILE) -> Settings:
    if not path.exists():
        return Settings()

    try:
        raw: Dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return Settings()

    s = Settings()
    s.camera_index = _coerce_int(raw.get("camera_index"), s.camera_index)
    s.session_seconds = max(10, _coerce_int(raw.get("session_seconds"), s.session_seconds))
    s.lbph_threshold = max(1.0, _coerce_float(raw.get("lbph_threshold"), s.lbph_threshold))
    s.duplicate_window_minutes = max(
        0, _coerce_int(raw.get("duplicate_window_minutes"), s.duplicate_window_minutes)
    )
    s.privacy_mode = _coerce_bool(raw.get("privacy_mode"), s.privacy_mode)
    s.consent_accepted = _coerce_bool(raw.get("consent_accepted"), s.consent_accepted)
    return s


def save_settings(settings: Settings, path: Path = SETTINGS_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(settings)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
