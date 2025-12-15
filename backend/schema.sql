-- FaceAttendance SQLite schema
--
-- Notes:
-- - This file exists to document the DB and to enable GitHub to detect SQL.
-- - The live schema is created in backend/storage.py (kept in sync with this file).

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attendance (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name    TEXT NOT NULL,
    ts      TEXT NOT NULL,
    date    TEXT NOT NULL,
    time    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_attendance_user_date ON attendance(user_id, date);
CREATE INDEX IF NOT EXISTS idx_attendance_ts ON attendance(ts);
CREATE UNIQUE INDEX IF NOT EXISTS uniq_attendance_user_ts ON attendance(user_id, ts);

CREATE TABLE IF NOT EXISTS enrollment_requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    contact    TEXT NOT NULL,
    message    TEXT NOT NULL,
    timestamp  TEXT NOT NULL,
    status     TEXT NOT NULL
);
