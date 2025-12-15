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
                CREATE UNIQUE INDEX IF NOT EXISTS uniq_attendance_user_ts ON attendance(user_id, ts);

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

        if user_count == 0 or att_count == 0 or req_count == 0:
            self.sync_from_csv(
                users_csv=users_csv if user_count == 0 else None,
                attendance_csv=att_csv if att_count == 0 else None,
                requests_csv=req_csv if req_count == 0 else None,
            )

    def sync_from_csv(
        self,
        *,
        users_csv: Optional[Path] = None,
        attendance_csv: Optional[Path] = None,
        requests_csv: Optional[Path] = None,
    ) -> dict[str, int]:
        """Merge legacy CSV data into SQLite.

        Safe to re-run for users + attendance:
        - users are upserted by id
        - attendance uses INSERT OR IGNORE keyed by (user_id, ts)
        """

        users_csv = _default_path_if_exists(users_csv)
        attendance_csv = _default_path_if_exists(attendance_csv)
        requests_csv = _default_path_if_exists(requests_csv)

        summary = {"users_upserted": 0, "attendance_inserted": 0, "requests_inserted": 0}

        if users_csv:
            summary["users_upserted"] = _upsert_users(self, _read_csv_safe(users_csv))

        with self._connect() as conn:
            if attendance_csv:
                summary["attendance_inserted"] = _insert_attendance_rows(
                    conn, _read_csv_safe(attendance_csv)
                )
            if requests_csv:
                summary["requests_inserted"] = _insert_request_rows(conn, _read_csv_safe(requests_csv))

        return summary


def users_count_safe(path: Path) -> bool:
    try:
        return path.exists() and path.stat().st_size > 0
    except Exception:
        return False


def _read_csv_safe(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _as_str(value) -> str:
    try:
        return str(value)
    except Exception:
        return ""


def _as_int(value):
    try:
        return int(value)
    except Exception:
        return None


def _as_ts(date_str: str, time_str: str) -> str:
    date_str = (date_str or "").strip()
    time_str = (time_str or "").strip()
    if not date_str or not time_str:
        return ""
    return f"{date_str} {time_str}"


def _coerce_time(t: str) -> str:
    # Keep as-is; assume HH:MM:SS.
    return (t or "").strip()


def _coerce_date(d: str) -> str:
    # Keep as-is; assume YYYY-MM-DD.
    return (d or "").strip()


def _normalize_status(s: str) -> str:
    s = (s or "").strip()
    return s if s else "Pending"


def _normalize_message(s: str) -> str:
    return (s or "").strip()


def _normalize_contact(s: str) -> str:
    return (s or "").strip()


def _normalize_name(s: str) -> str:
    return (s or "").strip()


def _normalize_timestamp(s: str) -> str:
    return (s or "").strip()


def _should_import_df(df: pd.DataFrame, required: set[str]) -> bool:
    return df is not None and not getattr(df, "empty", True) and required.issubset(set(df.columns))


def _safe_iterrows(df: pd.DataFrame):
    try:
        return df.iterrows()
    except Exception:
        return []


def _insert_attendance_rows(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    inserted = 0
    required = {"Id", "Name", "Date", "Time"}
    if not _should_import_df(df, required):
        return 0
    for _, r in _safe_iterrows(df):
        user_id = _as_int(r.get("Id"))
        if user_id is None:
            continue
        name = _as_str(r.get("Name"))
        date = _coerce_date(_as_str(r.get("Date")))
        time = _coerce_time(_as_str(r.get("Time")))
        ts = _as_ts(date, time)
        if not ts:
            continue
        cur = conn.execute(
            "INSERT OR IGNORE INTO attendance(user_id, name, ts, date, time) VALUES(?, ?, ?, ?, ?)",
            (user_id, name, ts, date, time),
        )
        inserted += int(cur.rowcount or 0)
    return inserted


def _insert_request_rows(conn: sqlite3.Connection, df: pd.DataFrame) -> int:
    inserted = 0
    required = {"Name", "Contact", "Message", "Timestamp", "Status"}
    if not _should_import_df(df, required):
        return 0
    for _, r in _safe_iterrows(df):
        name = _normalize_name(_as_str(r.get("Name")))
        contact = _normalize_contact(_as_str(r.get("Contact")))
        message = _normalize_message(_as_str(r.get("Message")))
        ts = _normalize_timestamp(_as_str(r.get("Timestamp")))
        status = _normalize_status(_as_str(r.get("Status")))
        if not (name and contact and message and ts):
            continue
        conn.execute(
            "INSERT INTO enrollment_requests(name, contact, message, timestamp, status) VALUES(?, ?, ?, ?, ?)",
            (name, contact, message, ts, status),
        )
        inserted += 1
    return inserted


def _upsert_users(store: "Storage", df: pd.DataFrame) -> int:
    inserted = 0
    required = {"Id", "Name"}
    if not _should_import_df(df, required):
        return 0
    for _, r in _safe_iterrows(df):
        user_id = _as_int(r.get("Id"))
        name = _normalize_name(_as_str(r.get("Name")))
        if user_id is None or not name:
            continue
        store.upsert_user(user_id, name)
        inserted += 1
    return inserted


def _default_path_if_exists(p: Optional[Path]) -> Optional[Path]:
    if p is None:
        return None
    try:
        return p if p.exists() else None
    except Exception:
        return None
