# FaceAttendance (FaceID Attendance App)

Windows desktop attendance app using face recognition (OpenCV) with a Tkinter UI. Operators can enroll users, train a recognition model, and log attendance sessions. Data is stored locally in SQLite.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python) ![OpenCV](https://img.shields.io/badge/OpenCV-LBPH-critical) ![Tkinter](https://img.shields.io/badge/UI-Tkinter-green)

## What this project includes
- **Desktop UI (Tkinter)** for Admin and User flows
- **Face detection + recognition** using Haar Cascade + LBPH (OpenCV contrib)
- **Local database** using SQLite (`attendance.sqlite3`)
- **Enrollment + training scripts** bundled into the Windows EXE
- **Windows distribution** via GitHub Releases (EXE + ZIP)
- **CI + Release automation** using GitHub Actions

## Table of Contents
- [Features](#features)
- [How It Works](#how-it-works)
- [Download and Run (Windows)](#download-and-run-windows)
- [Run from Source (Developers)](#run-from-source-developers)
- [Data, Storage, and Privacy](#data-storage-and-privacy)
- [Settings](#settings)
- [Build Windows EXE](#build-windows-exe)
- [Automated Releases (GitHub Actions)](#automated-releases-github-actions)
- [Troubleshooting](#troubleshooting)
- [Project Layout](#project-layout)

## Features
- **Admin Console**
    - Enroll new face (guided capture)
    - Train recognition model
    - Log attendance session
    - Manage users
    - Export reports (daily/weekly/monthly CSV)
- **User Dashboard**
    - Self-service enrollment request form
- **Safety/UX**
    - Consent prompt on first run
    - Privacy Mode (disables enrollment/training)
    - Kiosk mode option (`--kiosk`)
- **Quality**
    - Recognition uses ROI normalization (200×200) and consistent params across train/run
    - Duplicate log protection (unique constraint + optional time window)
    - Rotating file logging

## How It Works
High-level flow:
1. **Enroll**: Capture face samples to `data/dataset/`.
2. **Train**: Build LBPH model into `models/trainer.yml`.
3. **Recognize**: Run a session to match faces and log attendance.

Storage flow:
- Primary source of truth is **SQLite**: `data/attendance.sqlite3`.
- CSV files exist for compatibility/templates and exports.

## Download and Run (Windows)
If you just want to run the app (no Python required), use the GitHub **Releases** page.

Recommended download:
- `FaceAttendance-<version>-windows.zip`

Run steps:
1. Download the ZIP from **Releases**.
2. Extract it to a writable folder (example: `Desktop\FaceAttendance`).
3. Double-click `FaceAttendance.exe`.

First-time checklist (required before recognition works):
1. Accept the consent prompt.
2. Open **Settings** and confirm **Camera Index**.
3. Admin Console → **Enroll New Face** (enter ID + Name, complete capture).
4. Admin Console → **Train Recognition Model**.
5. Admin Console → **Log Attendance Session**.

End-user guide:
- See [RUN_WINDOWS.txt](RUN_WINDOWS.txt) for copy/paste instructions.

## Run from Source (Developers)
Requirements:
- Windows (developed on Windows 11)
- Python 3.10+ (CI uses Python 3.12)

```powershell
py -3 -m venv .venv
\.\.venv\Scripts\activate
python -m pip install -r requirements.txt

# Launch UI
python frontend/attendance_app.py
```

Optional (manual scripts):
```powershell
python scripts/01_create_dataset.py
python scripts/02_train_model.py
```

## Data, Storage, and Privacy
This app stores user and attendance data locally.

**SQLite (SQL database)**
- File: `data/attendance.sqlite3`
- Tables: `users`, `attendance`, `enrollment_requests`
- Schema documentation:
    - [backend/schema.sql](backend/schema.sql)
    - [docs/sql/sqlite_reference.sql](docs/sql/sqlite_reference.sql)

**Dataset and model (local-only)**
- Face samples: `data/dataset/` (images)
- Trained model: `models/trainer.yml`

**Runtime location when using the Windows EXE**
- If the EXE folder is writable: writes `data/`, `models/`, `logs/` next to the EXE (portable mode)
- Otherwise: falls back to `%LOCALAPPDATA%\FaceAttendance`

**Privacy warning**
- Do not commit real face images or trained models to Git.
- This repo is configured to ignore dataset images, model artifacts, logs, and local DB files.

## Settings
Open **Settings** in the UI to configure:
- Camera index
- Session duration (seconds)
- LBPH threshold (higher = more tolerant matches)
- Duplicate window (minutes)
- Privacy Mode

Kiosk mode:
```powershell
python frontend/attendance_app.py --kiosk
```

## Build Windows EXE
This repo uses PyInstaller to build a single EXE and then assembles an easy-to-run `release/` folder.

```powershell
\.\.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pip install pyinstaller

# Builds release/FaceAttendance.exe
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1 -Clean
```

Notes:
- The build script prefers `.venv` if present to ensure required deps (like Pillow) are included.
- In the packaged EXE, enrollment/training are run by re-invoking the same EXE with subcommands.

## Automated Releases (GitHub Actions)
When you push a `v*` tag, GitHub Actions builds and publishes:
- `FaceAttendance.exe`
- `FaceAttendance-<tag>-windows.zip`
- `checksums.sha256`

Example:
```powershell
git tag v1.0.1
git push origin v1.0.1
```

## Troubleshooting
- **Enroll popup flashes and closes**: update to the latest Release (older builds relied on console input).
- **Camera won’t open**: close Teams/Zoom/Discord/browser tabs; change Camera Index in Settings.
- **Capture says model missing**: enroll at least one user and train the model.
- **Missing `cv2.face`**: ensure you use `opencv-contrib-python` (not plain `opencv-python`).
- **Logs**: check `logs/faceattendance.log` under the runtime folder.

## Project Layout
| Path | Purpose |
| --- | --- |
| `frontend/` | Tkinter UI (`attendance_app.py`) |
| `backend/` | Core logic + SQLite storage (`storage.py`) |
| `scripts/` | Dataset capture + training scripts |
| `assets/` | Haar cascade and other bundled resources |
| `data/` | SQLite DB + CSV templates + dataset folder (local-only images) |
| `models/` | Trained model output (local-only) |
| `.github/workflows/` | CI + Release automation |
