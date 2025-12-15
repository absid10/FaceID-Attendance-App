from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.storage import DEFAULT_DB_PATH, Storage
from shared.paths import data_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Merge legacy CSV data (users/attendance/requests) into the SQLite DB."
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="Path to SQLite DB (default: data/attendance.sqlite3)",
    )
    parser.add_argument(
        "--users",
        type=Path,
        default=data_dir() / "UserDetails.csv",
        help="Path to UserDetails.csv",
    )
    parser.add_argument(
        "--attendance",
        type=Path,
        default=data_dir() / "Attendance.csv",
        help="Path to Attendance.csv",
    )
    parser.add_argument(
        "--requests",
        type=Path,
        default=data_dir() / "EnrollmentRequests.csv",
        help="Path to EnrollmentRequests.csv",
    )
    parser.add_argument(
        "--skip-requests",
        action="store_true",
        help="Skip importing EnrollmentRequests.csv (avoids potential duplicates).",
    )

    args = parser.parse_args()

    store = Storage(args.db)
    summary = store.sync_from_csv(
        users_csv=args.users,
        attendance_csv=args.attendance,
        requests_csv=None if args.skip_requests else args.requests,
    )

    with store._connect() as conn:  # intentional: small admin script
        users = int(conn.execute("SELECT COUNT(*) FROM users").fetchone()[0])
        attendance = int(conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0])
        requests = int(conn.execute("SELECT COUNT(*) FROM enrollment_requests").fetchone()[0])

    print("Import summary:")
    print(f"  users_upserted: {summary['users_upserted']}")
    print(f"  attendance_inserted: {summary['attendance_inserted']}")
    print(f"  requests_inserted: {summary['requests_inserted']}")
    print("DB counts:")
    print(f"  users: {users}")
    print(f"  attendance: {attendance}")
    print(f"  requests: {requests}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
