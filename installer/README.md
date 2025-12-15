# Installer (Inno Setup)

This project supports building a simple Windows installer using **Inno Setup**.

## Why an installer?
- Users can install from a single `.exe` setup.
- Creates Start Menu/Desktop shortcuts.
- The app stores writable data under the user profile when installed to Program Files.

## Prerequisites
- Install Inno Setup: https://jrsoftware.org/isinfo.php

## Build
1. Build the app EXE:
   - Run `./build_exe.ps1 -Clean`
   - The runnable binary is `release/FaceAttendance.exe`
2. Open `installer/FaceAttendance.iss` in Inno Setup and click **Compile**.

## Output
- The installer will be produced under `installer/output/` (default Inno Setup behavior).
