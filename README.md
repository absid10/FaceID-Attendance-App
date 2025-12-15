<div align="center">

# 🎯 FaceID Attendance App

### *Intelligent Face Recognition Attendance System*

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-LBPH-critical?logo=opencv&logoColor=white)
![Tkinter](https://img.shields.io/badge/UI-Tkinter-green?logo=python&logoColor=white)
![License](https://img.shields.io/github/license/absid10/FaceID-Attendance-App)
![Downloads](https://img.shields.io/github/downloads/absid10/FaceID-Attendance-App/total)
![Release](https://img.shields.io/github/v/release/absid10/FaceID-Attendance-App)

**A Python-based Face ID Attendance Application that uses facial recognition to automatically mark and manage attendance. Capture faces via webcam, match them against a registered database, log check-in/check-out times, and export attendance reports.**

[📥 Download](#-download) • [✨ Features](#-features) • [📖 Documentation](#-table-of-contents) • [🚀 Quick Start](#-quick-start-windows)

</div>

---

## 📥 Download

<div align="center">

### 🪟 Windows Application (No Python Required)

**Latest Release:  v1.0.1**

[![Download ZIP](https://img.shields.io/badge/Download-Windows_ZIP-0078D4?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/absid10/FaceID-Attendance-App/releases/download/v1.0.1/FaceAttendance-v1.0.1-windows.zip)
[![Download EXE](https://img.shields.io/badge/Download-Standalone_EXE-0078D4?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/absid10/FaceID-Attendance-App/releases/download/v1.0.1/FaceAttendance.exe)

[![View All Releases](https://img.shields.io/badge/View-All_Releases-gray?style=for-the-badge&logo=github)](https://github.com/absid10/FaceID-Attendance-App/releases)

**📊 File Size:** ~50MB | **✅ Verified:** SHA256 Checksums Available

</div>

---

## 📊 Project Overview

```mermaid
graph LR
    A[👤 User Enrollment] --> B[📸 Face Capture]
    B --> C[🤖 Model Training]
    C --> D[🎯 Face Recognition]
    D --> E[📝 Attendance Logging]
    E --> F[📊 Report Export]
    
    style A fill:#4CAF50
    style C fill:#2196F3
    style E fill:#FF9800
    style F fill:#9C27B0
```

### 🔧 Technology Stack

```mermaid
pie title "Language Composition"
    "Python" : 92
    "SQL" : 4.7
    "PowerShell" : 2.2
    "Inno Setup" : 1.1
```

---

## 🖼️ App Preview

Below are in-app screenshots of the console and live capture view:

- Admin console with quick actions, model insights, and recent attendance  
  ![image2](image2)

- Live attendance capture with recognition bounding box and confidence  
  ![image1](image1)

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 👨‍💼 **Admin Console**
- ✅ **Enroll New Users** - Guided face capture process
- 🧠 **Train AI Model** - Build recognition model
- 📋 **Log Attendance** - Automated session tracking
- 👥 **User Management** - Manage registered users
- 📊 **Export Reports** - Daily/Weekly/Monthly CSV exports

</td>
<td width="50%">

### 👤 **User Dashboard**
- 📝 **Self-Service Enrollment** - Request form submission
- 🔐 **Privacy Controls** - Consent management
- 📱 **Kiosk Mode** - Dedicated attendance terminal
- 🎯 **Real-time Recognition** - Instant face matching
- 🔒 **Data Privacy** - Local-only storage

</td>
</tr>
</table>

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    A[🖥️ Tkinter UI] --> B[🎥 OpenCV Camera]
    A --> C[💾 SQLite Database]
    B --> D[🔍 Haar Cascade Detection]
    D --> E[🤖 LBPH Recognition]
    E --> F[✅ Match/No Match]
    F --> C
    C --> G[📊 CSV Reports]
    
    style A fill:#e3f2fd
    style B fill:#fff3e0
    style C fill:#f3e5f5
    style E fill:#e8f5e9
    style G fill:#fce4ec
```

---

## 🚀 Quick Start (Windows)

### Step 1: Download & Extract
```
📦 Download FaceAttendance-v1.0.1-windows.zip
📂 Extract to Desktop\FaceAttendance
🖱️ Double-click FaceAttendance.exe
```

### Step 2: Initial Setup

```mermaid
graph TD
    A[🚀 Launch App] --> B[✅ Accept Consent]
    B --> C[⚙️ Configure Camera]
    C --> D[👤 Enroll First User]
    D --> E[🧠 Train Model]
    E --> F[✨ Start Recognition]
    
    style A fill:#4CAF50,color:#fff
    style F fill:#2196F3,color:#fff
```

1. ✅ **Accept** the consent prompt  
2. ⚙️ **Open Settings** → Confirm Camera Index  
3. 👤 **Admin Console** → Enroll New Face  
4. 🧠 **Admin Console** → Train Recognition Model  
5. 📋 **Admin Console** → Log Attendance Session  

> 💡 **Tip:** See [RUN_WINDOWS.txt](RUN_WINDOWS.txt) for detailed instructions

---

## 🎯 How It Works

### Recognition Pipeline

```mermaid
sequenceDiagram
    participant U as 👤 User
    participant C as 📸 Camera
    participant D as 🔍 Detector
    participant R as 🤖 Recognizer
    participant DB as 💾 Database
    
    U->>C: Stand in front of camera
    C->>D: Capture frame
    D->>D: Detect face (Haar Cascade)
    D->>R: Extract face ROI (200x200)
    R->>R: Match against LBPH model
    R->>DB: Log attendance if confident
    DB->>U: ✅ Attendance marked!
```

### Data Flow

1. **📸 Enroll**: Capture face samples → `data/dataset/`  
2. **🧠 Train**: Build LBPH model → `models/trainer.yml`  
3. **🎯 Recognize**: Match faces → Log to SQLite  
4. **📊 Export**: Generate CSV reports  

---

## 💻 Run from Source (Developers)

### Prerequisites
- 🪟 Windows 10/11
- 🐍 Python 3.10+

### Installation

```powershell
# Create virtual environment
py -3 -m venv .venv

# Activate environment
.\.venv\Scripts\activate

# Install dependencies
python -m pip install -r requirements.txt

# Launch application
python frontend/attendance_app.py
```

### Optional Manual Scripts
```powershell
python scripts/01_create_dataset.py
python scripts/02_train_model.py
```

---

## 💾 Data Storage & Privacy

### 🗃️ Database Schema (SQLite)

**File:** `data/attendance.sqlite3`

| Table | Purpose |
|-------|---------|
| 👥 `users` | Registered user information |
| 📋 `attendance` | Check-in/out timestamps |
| 📝 `enrollment_requests` | Self-service enrollment queue |

> 📖 See [backend/schema.sql](backend/schema.sql) for full schema

### 📁 Local Storage Structure

```
FaceAttendance/
├── 📂 data/
│   ├── 💾 attendance.sqlite3      # Primary database
│   └── 📂 dataset/                # Face images (local-only)
├── 📂 models/
│   └── 🤖 trainer.yml             # Trained LBPH model
└── 📂 logs/
    └── 📄 faceattendance.log      # Application logs
```

### 🔒 Privacy & Security

- ✅ **100% Local Storage** - No cloud uploads  
- ✅ **Consent Required** - First-run privacy agreement  
- ✅ **Privacy Mode** - Disable enrollment/training  
- ⚠️ **Biometric Data** - Never commit face images to Git  
- 🔐 **Portable Mode** - Data stays with the EXE folder  

---

## ⚙️ Configuration & Settings

### Settings Panel Options

| Setting | Description | Default |
|---------|-------------|---------|
| 📹 Camera Index | Webcam device ID | 0 |
| ⏱️ Session Duration | Recognition session length | 60s |
| 🎯 LBPH Threshold | Match tolerance (higher = lenient) | 50 |
| 🔄 Duplicate Window | Prevent re-logging interval | 5 min |
| 🔒 Privacy Mode | Disable enrollment/training | Off |

### Kiosk Mode

```powershell
python frontend/attendance_app.py --kiosk
```
**Output:** `release/FaceAttendance.exe`

---

## 🤖 Automated Releases (CI/CD)

### GitHub Actions Workflow

```mermaid
graph LR
    A[📝 Create Tag] --> B[🔨 Build EXE]
    B --> C[📦 Package ZIP]
    C --> D[🔐 Generate SHA256]
    D --> E[🚀 Publish Release]
    
    style A fill:#4CAF50
    style E fill:#2196F3
```

**Trigger a release:**
```powershell
git tag v1.0.2
git push origin v1.0.2
```

**Artifacts Generated:**
- ✅ `FaceAttendance.exe`
- ✅ `FaceAttendance-v1.0.2-windows.zip`
- ✅ `checksums.sha256`

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| ⚡ Enroll popup flashes | Update to latest release |
| 📹 Camera won't open | Close other apps using camera; check Settings → Camera Index |
| 🤖 Model missing error | Enroll ≥1 user and train the model |
| ❌ Missing `cv2.face` | Install `opencv-contrib-python` instead of `opencv-python` |
| 📋 Check logs | See `logs/faceattendance.log` |

---
```
FaceID-Attendance-App/
├── 🖥️ frontend/              # Tkinter UI (attendance_app.py)
├── ⚙️ backend/               # Core logic + SQLite storage
├── 📜 scripts/               # Dataset capture + training scripts
├── 🎨 assets/                # Haar cascade + resources
├── 💾 data/                  # Database + CSV templates
├── 🤖 models/                # Trained model output
├── 🔧 .github/workflows/     # CI/CD automation
└── 📖 docs/                  # Documentation
```

---
## 📈 Project Stats

<div align="center">

![GitHub stars](https://img.shields.io/github/stars/absid10/FaceID-Attendance-App?style=social)
![GitHub forks](https://img.shields.io/github/forks/absid10/FaceID-Attendance-App?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/absid10/FaceID-Attendance-App?style=social)

</div>

---
## 📄 License

This project is open source. See the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Made with ❤️ using Python, OpenCV, and Tkinter**

[⬆ Back to Top](#-faceid-attendance-app)

</div>
