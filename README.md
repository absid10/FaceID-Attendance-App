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
1. **Enrollment request** captured inside the UI and logged to `data/EnrollmentRequests.csv`.
2. **Dataset capture** (`scripts/01_create_dataset.py`) collects samples as `data/dataset/User.<user_id>.<n>.jpg`.
3. **Model training** (`scripts/02_train_model.py`) refreshes `models/trainer.yml` via LBPH.
4. **Recognition session** reads frames from the webcam and logs outcomes into `data/Attendance.csv`.

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
If you just want to run the app (no Python required), download the latest prebuilt executable from the repository **Releases** page and run it.

Notes:
- The `.exe` creates `data/` and `models/` folders next to itself on first run.
- This repo does **not** publish real face datasets or trained models in git history. Use Releases for binaries.

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
- `data/Attendance.csv`, `data/UserDetails.csv`, `data/EnrollmentRequests.csv`: CSV storage used by the app.
- `data/dataset/`: raw grayscale face crops (local-only).
- `models/trainer.yml`: LBPH model (local-only). Regenerate after dataset changes.

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
