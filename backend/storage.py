from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

from shared.paths import data_dir


DEFAULT_DB_PATH = data_dir() / "attendance.sqlite3"


@dataclass(frozen=True)
class AttendanceLogResult:
    logged: bool
    time_str: str


class Storage:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    ts TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_attendance_user_date ON attendance(user_id, date);
                CREATE INDEX IF NOT EXISTS idx_attendance_ts ON attendance(ts);

                CREATE TABLE IF NOT EXISTS enrollment_requests (
                    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    contact TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL
                );
                """
            )

    # ---------- Users ----------

    def users_df(self) -> pd.DataFrame:
        with self._connect() as conn:
            return pd.read_sql_query("SELECT id AS Id, name AS Name FROM users ORDER BY id", conn)

    def upsert_user(self, user_id: int, name: str) -> None:
        name = (name or "").strip()
        if not name:
            raise ValueError("Name cannot be empty")
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO users(id, name) VALUES(?, ?) "
                "ON CONFLICT(id) DO UPDATE SET name=excluded.name",
                (int(user_id), name),
            )

    def delete_user(self, user_id: int) -> None:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM users WHERE id=?", (int(user_id),))
            if cur.rowcount == 0:
                raise ValueError(f"User ID {user_id} not found")

    # ---------- Attendance ----------

    def attendance_df(self) -> pd.DataFrame:
        with self._connect() as conn:
            return pd.read_sql_query(
                "SELECT user_id AS Id, name AS Name, date AS Date, time AS Time "
                "FROM attendance ORDER BY date, time",
                conn,
            )

    def _last_log_for_user(self, user_id: int) -> Optional[Tuple[str, str]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT ts, date FROM attendance WHERE user_id=? ORDER BY ts DESC LIMIT 1",
                (int(user_id),),
            ).fetchone()
            if not row:
                return None
            return str(row["ts"]), str(row["date"])

    def log_attendance(
        self,
        *,
        user_id: int,
        user_name: str,
        min_minutes_between_logs: int = 10,
        enforce_one_per_day: bool = True,
        now: Optional[datetime] = None,
    ) -> AttendanceLogResult:
        now_dt = now or datetime.now()
        date_str = now_dt.strftime("%Y-%m-%d")
        time_str = now_dt.strftime("%H:%M:%S")
        ts_iso = now_dt.strftime("%Y-%m-%d %H:%M:%S")

        last = self._last_log_for_user(user_id)
        if last:
            last_ts, last_date = last
            if enforce_one_per_day and last_date == date_str:
                return AttendanceLogResult(logged=False, time_str=time_str)

            if min_minutes_between_logs > 0:
                try:
                    last_dt = datetime.strptime(last_ts, "%Y-%m-%d %H:%M:%S")
                    delta_min = (now_dt - last_dt).total_seconds() / 60.0
                    if delta_min < float(min_minutes_between_logs):
                        return AttendanceLogResult(logged=False, time_str=time_str)
                except Exception:
                    # If parsing fails, fall back to allowing the log.
                    pass

        with self._connect() as conn:
            conn.execute(
                "INSERT INTO attendance(user_id, name, ts, date, time) VALUES(?, ?, ?, ?, ?)",
                (int(user_id), str(user_name), ts_iso, date_str, time_str),
            )
        return AttendanceLogResult(logged=True, time_str=time_str)

    def export_attendance_csv(
        self, out_path: Path, *, period: str = "daily", now: Optional[datetime] = None
    ) -> None:
        now_dt = now or datetime.now()
        period = (period or "daily").strip().lower()

        if period == "daily":
            start = now_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "weekly":
            # Monday as start of week
            start = now_dt.replace(hour=0, minute=0, second=0, microsecond=0) - pd.Timedelta(
                days=int(now_dt.weekday())
            )
            start = start.to_pydatetime()
        elif period == "monthly":
            start = now_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            raise ValueError("period must be one of: daily, weekly, monthly")

        start_iso = start.strftime("%Y-%m-%d %H:%M:%S")
        with self._connect() as conn:
            df = pd.read_sql_query(
                "SELECT user_id AS Id, name AS Name, date AS Date, time AS Time "
                "FROM attendance WHERE ts >= ? ORDER BY ts",
                conn,
                params=(start_iso,),
            )

        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)

    # ---------- Enrollment Requests ----------

    def requests_df(self) -> pd.DataFrame:
        with self._connect() as conn:
            return pd.read_sql_query(
                "SELECT request_id AS RequestId, name AS Name, contact AS Contact, "
                "message AS Message, timestamp AS Timestamp, status AS Status "
                "FROM enrollment_requests ORDER BY request_id",
                conn,
            )

    def add_request(self, *, name: str, contact: str, message: str) -> None:
        name = name.strip()
        contact = contact.strip()
        message = message.strip()
        if not name:
            raise ValueError("Name is required.")
        if not contact:
            raise ValueError("Contact info is required.")
        if not message:
            raise ValueError("Please describe your request.")

        with self._connect() as conn:
            conn.execute(
                "INSERT INTO enrollment_requests(name, contact, message, timestamp, status) "
                "VALUES(?, ?, ?, ?, ?)",
                (
                    name,
                    contact,
                    message,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Pending",
                ),
            )

    def update_request_status(self, request_id: int, status: str) -> None:
        status = (status or "").strip()
        if not status:
            raise ValueError("Status cannot be empty")
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE enrollment_requests SET status=? WHERE request_id=?",
                (status, int(request_id)),
            )
            if cur.rowcount == 0:
                raise ValueError(f"Request ID {request_id} not found.")

    # ---------- Migration helpers (CSV -> SQLite) ----------

    def migrate_from_csv_if_needed(self) -> None:
        """Best-effort one-time import from legacy CSVs if the DB is empty."""

        users_csv = data_dir() / "UserDetails.csv"
        att_csv = data_dir() / "Attendance.csv"
        req_csv = data_dir() / "EnrollmentRequests.csv"

        with self._connect() as conn:
            user_count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
            att_count = conn.execute("SELECT COUNT(*) AS c FROM attendance").fetchone()["c"]
            req_count = conn.execute("SELECT COUNT(*) AS c FROM enrollment_requests").fetchone()[
                "c"
            ]

        if user_count == 0 and users_csv.exists():
            try:
                df = pd.read_csv(users_csv)
                if {"Id", "Name"}.issubset(df.columns):
                    for _, r in df.iterrows():
                        try:
                            self.upsert_user(int(r["Id"]), str(r["Name"]))
                        except Exception:
                            continue
            except Exception:
                pass

        if att_count == 0 and att_csv.exists():
            try:
                df = pd.read_csv(att_csv)
                cols = {"Id", "Name", "Date", "Time"}
                if cols.issubset(df.columns):
                    with self._connect() as conn:
                        for _, r in df.iterrows():
                            try:
                                user_id = int(r["Id"])
                                name = str(r["Name"])
                                date = str(r["Date"])
                                time = str(r["Time"])
                                ts = f"{date} {time}"
                                conn.execute(
                                    "INSERT INTO attendance(user_id, name, ts, date, time) VALUES(?, ?, ?, ?, ?)",
                                    (user_id, name, ts, date, time),
                                )
                            except Exception:
                                continue
            except Exception:
                pass

        if req_count == 0 and req_csv.exists():
            try:
                df = pd.read_csv(req_csv)
                if {"Name", "Contact", "Message", "Timestamp", "Status"}.issubset(df.columns):
                    with self._connect() as conn:
                        for _, r in df.iterrows():
                            try:
                                conn.execute(
                                    "INSERT INTO enrollment_requests(name, contact, message, timestamp, status) VALUES(?, ?, ?, ?, ?)",
                                    (
                                        str(r["Name"]),
                                        str(r["Contact"]),
                                        str(r["Message"]),
                                        str(r["Timestamp"]),
                                        str(r["Status"]),
                                    ),
                                )
                            except Exception:
                                continue
            except Exception:
                pass
