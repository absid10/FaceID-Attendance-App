-- SQLite reference for FaceAttendance
--
-- GitHub Linguist reports the language as "SQL" (not "SQLite").
-- This file intentionally contains SQLite-specific SQL/PRAGMA examples so
-- the repository's Languages breakdown shows SQL.
--
-- No personal/user data is stored in this repo; this file is documentation only.

-- -----------------------------------------------------------------------------
-- Database initialization
-- -----------------------------------------------------------------------------
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;          -- better durability/concurrency for desktop apps
PRAGMA synchronous = NORMAL;
PRAGMA temp_store = MEMORY;

-- -----------------------------------------------------------------------------
-- Schema (kept in sync with backend/storage.py)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attendance (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name    TEXT NOT NULL,
    ts      TEXT NOT NULL,  -- ISO-like: YYYY-MM-DD HH:MM:SS
    date    TEXT NOT NULL,  -- YYYY-MM-DD
    time    TEXT NOT NULL   -- HH:MM:SS
);

CREATE TABLE IF NOT EXISTS enrollment_requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    contact    TEXT NOT NULL,
    message    TEXT NOT NULL,
    timestamp  TEXT NOT NULL,
    status     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_attendance_user_date ON attendance(user_id, date);
CREATE INDEX IF NOT EXISTS idx_attendance_ts ON attendance(ts);
CREATE UNIQUE INDEX IF NOT EXISTS uniq_attendance_user_ts ON attendance(user_id, ts);

-- -----------------------------------------------------------------------------
-- Common queries
-- -----------------------------------------------------------------------------
-- List users
SELECT id, name
FROM users
ORDER BY id;

-- Latest attendance per user
SELECT a.user_id,
       a.name,
       MAX(a.ts) AS last_seen
FROM attendance a
GROUP BY a.user_id, a.name
ORDER BY last_seen DESC;

-- Attendance for a given day
-- (bind :day as YYYY-MM-DD)
SELECT user_id AS Id,
       name    AS Name,
       date    AS Date,
       time    AS Time
FROM attendance
WHERE date = :day
ORDER BY ts;

-- Attendance in a time range
-- (bind :start_ts/:end_ts as YYYY-MM-DD HH:MM:SS)
SELECT user_id, name, ts
FROM attendance
WHERE ts >= :start_ts AND ts <= :end_ts
ORDER BY ts;

-- Counts
SELECT
  (SELECT COUNT(*) FROM users) AS users,
  (SELECT COUNT(*) FROM attendance) AS attendance,
  (SELECT COUNT(*) FROM enrollment_requests) AS requests;

-- -----------------------------------------------------------------------------
-- Data integrity / duplicate protection
-- -----------------------------------------------------------------------------
-- This mirrors the app behavior: duplicates are prevented by uniq_attendance_user_ts.
-- You can test it with:
--   INSERT OR IGNORE INTO attendance(user_id,name,ts,date,time) VALUES(1,'User1','2025-01-01 09:00:00','2025-01-01','09:00:00');
--   INSERT OR IGNORE INTO attendance(user_id,name,ts,date,time) VALUES(1,'User1','2025-01-01 09:00:00','2025-01-01','09:00:00');
-- The second insert will be ignored.

-- -----------------------------------------------------------------------------
-- Optional maintenance
-- -----------------------------------------------------------------------------
ANALYZE;
VACUUM;
