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
| `data/` | Persistent CSVs, enrollment requests, captured frames | `Attendance.csv`, `UserDetails.csv`, `dataset/` |
| `models/` | Serialized LBPH model | `trainer.yml` |
| `assets/` | Face detection assets, classifiers, UI images | `haarcascade_frontalface_default.xml` |

## Features
- Admin dashboard with live metrics, capture launch, enrollment request queue, user roster, and one-click retraining shortcut.
- User dashboard with guided capture access and self-service enrollment requests.
- Enrollment-request intake form plus approval workflow that launches the dataset capture script with prefilled metadata.
- User manager that removes stale profiles and associated image samples while reminding admins to retrain.
- Camera overlay with live status, confidence readouts, and exit hints (ESC/Q) to keep operators informed.

## Data Flow
1. **Enrollment request** captured inside the UI and logged to `data/EnrollmentRequests.csv`.
2. **Dataset capture** (`scripts/01_create_dataset.py`) collects 60+ frames per user into `data/dataset/<user_id>/`.
3. **Model training** (`scripts/02_train_model.py`) refreshes `models/trainer.yml` via LBPH.
4. **Recognition session** reads frames from the webcam, streams predictions to the UI, and logs outcomes into `data/Attendance.csv`.
5. **Exports** are available instantly as CSV for payroll/HR integration (Excel-ready).

## Quick Start
```powershell
# 1. Setup environment
py -3 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt  # or manually install OpenCV, Pillow, NumPy, Pandas

# 2. Seed dataset and train
python scripts/01_create_dataset.py
python scripts/02_train_model.py

# 3. Launch the desktop console
python frontend/attendance_app.py
```

| Requirement | Notes |
| --- | --- |
| Python | 3.10+ recommended |
| Camera | Any DirectShow-compatible webcam OpenCV can access |
| OS | Developed on Windows, works anywhere Tkinter + OpenCV are supported |

## Usage Guide
**Admin Flow**
- Launch dashboard → review pending enrollment requests → approve and auto-start capture.
- Run retraining after each enrollment batch (shortcut button triggers `scripts/02_train_model.py`).
- Use the user manager to retire IDs; the helper wipes `data/dataset/<id>` to keep the model lean.

**Operator Flow**
- Select the capture mode you need (attendance vs. enrollment).
- Follow on-screen prompts; confidence and frame counters help you gauge capture quality.
- Press `ESC` or `Q` at any point to safely exit the overlay.

**Reporting**
- Open `data/Attendance.csv` in Excel or import into HRIS/BI tools.
- Filter by date/time or employee ID to audit sessions.

## Automation Scripts
| Script | Purpose |
| --- | --- |
| `scripts/01_create_dataset.py` | Opens the camera, captures labeled face frames, and stores them per user ID. |
| `scripts/02_train_model.py` | Ingests the dataset, trains the LBPH recognizer, and exports `models/trainer.yml`. |
| `backend/requests_core.py` | Handles enrollment CRUD, CSV writes, and validation logic. |
| `backend/attendance_core.py` | Connects the UI to OpenCV loops, logging, and retraining helpers. |

## Data & Models
- `data/Attendance.csv`: append-only log of recognition events (timestamp, ID, status).
- `data/UserDetails.csv`: canonical roster referenced throughout the UI.
- `data/EnrollmentRequests.csv`: queue of pending approvals when users self-enroll.
- `data/dataset/`: raw grayscale face crops; delete old folders to shrink the model.
- `models/trainer.yml`: LBPH weights; regenerate whenever data changes substantially.

## Troubleshooting
- **Camera not found**: confirm no other app (Teams/Zoom) is locking the webcam; restart the Tkinter app afterward.
- **Model predicts UNKNOWN**: rerun dataset capture with better lighting and ensure the face fills most of the frame; then retrain.
- **Import errors**: verify the virtual environment is active and `opencv-contrib-python` is installed (the contrib build exposes LBPH).
- **Unicode paths**: avoid non-ASCII folder names for the dataset; LBPH file I/O is ASCII-only.

## Roadmap
- Optional SQLite/REST backend to replace CSVs.
- Automated retraining scheduler with notifications.
- Attendance analytics dashboard (trend charts, export wizard).
- Cloud packaging (Docker + Azure Container Apps) for centralized deployment.
