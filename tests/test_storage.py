from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from backend.storage import Storage


def test_storage_basic_flow(tmp_path: Path) -> None:
    os.environ["FACEATTENDANCE_RUNTIME_DIR"] = str(tmp_path)
    try:
        store = Storage(tmp_path / "test.sqlite3")
        store.upsert_user(1, "User1")
        users = store.users_df()
        assert not users.empty
        assert int(users.iloc[0]["Id"]) == 1

        result1 = store.log_attendance(user_id=1, user_name="User1", min_minutes_between_logs=10)
        assert result1.logged is True

        result2 = store.log_attendance(user_id=1, user_name="User1", min_minutes_between_logs=10)
        # same-day rule should block duplicates
        assert result2.logged is False

        df = store.attendance_df()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
    finally:
        os.environ.pop("FACEATTENDANCE_RUNTIME_DIR", None)
