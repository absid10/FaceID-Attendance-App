from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from shared.paths import runtime_dir


_LOGGER_CONFIGURED = False


def configure_logging(*, level: int = logging.INFO) -> None:
    """Configure root logging to a rotating file under the runtime directory.

    Safe to call multiple times.
    """

    global _LOGGER_CONFIGURED
    if _LOGGER_CONFIGURED:
        return

    logs_dir = runtime_dir() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "faceattendance.log"

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger()
    root.setLevel(level)

    file_handler = RotatingFileHandler(
        filename=str(log_file),
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(fmt)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(fmt)

    root.addHandler(file_handler)
    root.addHandler(stream_handler)

    _LOGGER_CONFIGURED = True
