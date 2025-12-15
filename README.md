# FaceID-Attendance-App

Modernized Tkinter desktop console for capturing, reviewing, and managing face-recognition attendance sessions. The project is split into clear frontend, backend, and automation layers so each responsibility can evolve independently.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python) ![OpenCV](https://img.shields.io/badge/OpenCV-LBPH-critical) ![Tkinter](https://img.shields.io/badge/UI-Tkinter-green)

## Table of Contents
- [Overview](#overview)
- [Architecture Overview](#architecture-overview)
- [Folder Layout](#folder-layout)
- [Features](#features)
- [Data Flow](#data-flow)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
- [Automation Scripts](#automation-scripts)
- [Data & Models](#data--models)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)

## Overview
The app combines OpenCV (Haar Cascade + LBPH) with a Tkinter control panel to streamline employee attendance. Operators can enroll new faces, run capture sessions, and export CSV rosters without touching the command line. Admin tooling keeps the dataset clean and reminds the team when retraining is required.

## Architecture Overview
```
┌───────────┐      Tk events      ┌──────────────────┐
│ Tkinter UI│ ─────────────────▶ │ backend/attendance│
│frontend/...│ ◀──────────────── │   _core.py        │
└───────────┘   status updates   └────────┬─────────┘
                                           │
                                           │ invokes
                                           ▼
                              scripts/01_create_dataset.py
                              scripts/02_train_model.py
                                           │
                                           ▼
                              data/dataset | models/trainer.yml
```

## Folder Layout
| Path | Purpose | Highlights |
| --- | --- | --- |
| `frontend/` | Tkinter desktop experience | `attendance_app.py` |
| `backend/` | Business logic and orchestration helpers | `attendance_core.py`, `requests_core.py` |
| `scripts/` | Stand-alone automation for dataset capture and model training | `01_create_dataset.py`, `02_train_model.py` |
| `data/` | Persistent CSVs and captured frames | `Attendance.csv`, `UserDetails.csv`, `dataset/` |
| `models/` | Serialized LBPH model | `trainer.yml` |
| `assets/` | Face detection assets, classifiers, UI images | `haarcascade_frontalface_default.xml` |

## Features
- Admin dashboard with live metrics, capture launch, enrollment request queue, user roster, and one-click retraining shortcut.
- User dashboard with guided capture access and self-service enrollment requests.
- Enrollment-request intake form plus approval workflow.
- User manager to retire IDs and clean up samples.
- Camera overlay with live status and match-quality readout.

## Data Flow
1. **Enrollment request** captured inside the UI and stored in `data/attendance.sqlite3`.
2. **Dataset capture** (`scripts/01_create_dataset.py`) collects samples as `data/dataset/User.<user_id>.<n>.jpg` (local-only).
3. **Model training** (`scripts/02_train_model.py`) refreshes `models/trainer.yml` via LBPH (local-only).
4. **Recognition session** reads frames from the webcam and logs outcomes into SQLite; CSV export remains available for reports.

## Quick Start
```powershell
# 1. Setup environment
py -3 -m venv .venv
\.\.venv\Scripts\activate
python -m pip install -r requirements.txt

# 2. Capture a dataset (enroll at least one user)
# Interactive:
python scripts/01_create_dataset.py

# Or non-interactive:
# python scripts/01_create_dataset.py --id 1 --name "Your Name" --samples 150

# 3. Train the model
python scripts/02_train_model.py

# 4. Launch the desktop console
python frontend/attendance_app.py
```

## Download Windows `.exe`
If you just want to run the app (no Python required), download the latest prebuilt Windows build from the repository **Releases** page.

Recommended download:
- `FaceAttendance-<version>-windows.zip` (contains the app plus a seeded `data/` folder)

### Run (Windows)
1. Go to the GitHub **Releases** page.
2. Download `FaceAttendance-<version>-windows.zip`.
3. Extract the zip to a folder you can write to (example: `Desktop\FaceAttendance`).
4. Double-click `FaceAttendance.exe`.

First run checklist:
- Accept the consent prompt.
- Open **Settings** and confirm the **Camera Index** (0 is common).
- To enable recognition, you must enroll and train once:
    - Admin Console → **Enroll New Face** → enter ID + Name → complete camera capture.
    - Admin Console → **Train Recognition Model**.
    - Admin Console → **Log Attendance Session**.

Notes:
- If the `.exe` folder is writable (portable run), it writes `data/` + `models/` next to itself.
- If installed under a protected folder (like Program Files), it falls back to `%LOCALAPPDATA%\FaceAttendance`.
- This repo does **not** publish real face datasets or trained models in git history. Use Releases for binaries.

Troubleshooting (Windows):
- **Enroll window opens then closes**: update to the latest Release and retry.
- **Camera won’t open**: close Teams/Zoom/browser tabs using the webcam; set a different Camera Index in Settings.
- **Capture says model missing**: enroll at least one user and train the model.

## Settings & Calibration
Open **Settings** in the sidebar to configure:
- Camera index
- Session duration
- LBPH threshold (higher = more tolerant matches)
- Duplicate window (minutes) to prevent multiple logs in a short period
- Privacy Mode (disables enrollment/training)

Kiosk mode:
- Launch with `--kiosk` to hide the Admin Console button.

## Build a Windows `.exe` (PyInstaller)
This produces a distributable Windows build. When run as an `.exe`, the app writes `data/` and `models/` next to the executable (so it can run from any folder).

```powershell
# 1) From the repo root, activate your venv
\.\.venv\Scripts\activate

# 2) Install runtime deps + PyInstaller
python -m pip install -r requirements.txt
python -m pip install pyinstaller

# 3) Build (one-folder distribution)
python -m PyInstaller --noconfirm --clean FaceAttendance.spec

# Output:
# dist\FaceAttendance.exe
```

Notes:
- Distribute by copying `dist\\FaceAttendance.exe`.
- On first run, the app creates `data\\` and `models\\` next to the exe.
- The GUI launches enrollment/training in a separate console by running the same exe with subcommands (`create-dataset`, `train-model`).

Publishing tip (GitHub): build locally, then upload `dist\\FaceAttendance.exe` as a Release asset.

### Automated Releases (GitHub Actions)
This repo includes a workflow that builds and attaches Windows downloads automatically when you push a tag:
- `FaceAttendance.exe`
- `FaceAttendance-<version>-windows.zip`

Example:
```powershell
git tag v1.0.0
git push origin v1.0.0
```

The Release asset will appear under the GitHub **Releases** page.

| Requirement | Notes |
| --- | --- |
| Python | 3.10+ recommended |
| Camera | Any DirectShow-compatible webcam OpenCV can access |
| OS | Developed on Windows |

## Usage Guide
**Admin Flow**
- Review pending enrollment requests → approve and enroll.
- Retrain after enrollment batches.
- Use the user manager to retire IDs.

**Operator Flow**
- Start a capture session to log attendance.
- Press `ESC` or `Q` to exit the OpenCV window.

## Automation Scripts
| Script | Purpose |
| --- | --- |
| `scripts/01_create_dataset.py` | Captures face samples into `data/dataset/`. |
| `scripts/02_train_model.py` | Trains LBPH and writes `models/trainer.yml`. |

## Data & Models
- `data/attendance.sqlite3`: primary storage for users, attendance, and enrollment requests.
- `data/Attendance.csv`, `data/UserDetails.csv`, `data/EnrollmentRequests.csv`: legacy CSV compatibility / templates (not the source of truth).
- `data/dataset/`: raw grayscale face crops (local-only).
- `models/trainer.yml`: LBPH model (local-only). Regenerate after dataset changes.

## Reports
Admins can export daily/weekly/monthly CSV reports from the Admin Console.

## Logging
The app writes logs to `logs/faceattendance.log` under the runtime directory (next to the exe for portable runs, otherwise under LocalAppData).

Privacy:
- Do **not** commit real face images or trained models to git.
- This repo includes only sanitized CSV templates; keep real data locally.

## Troubleshooting
- **Camera not found**: close Teams/Zoom or other apps using the webcam.
- **Model predicts UNKNOWN**: recapture samples with better lighting and retrain.
- **Import errors / missing `cv2.face`**: use `opencv-contrib-python` and avoid installing `opencv-python` alongside it.
- **OpenCV model read errors / huge `trainer.yml`**: retrain using `scripts/02_train_model.py`.

## Roadmap
- Optional SQLite/REST backend to replace CSVs.
- Automated retraining scheduler with notifications.
- Attendance analytics dashboard.
