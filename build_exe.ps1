param(
    [switch]$Clean
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if ($Clean) {
    if (Test-Path "$root\\build") { Remove-Item -Recurse -Force "$root\\build" }
    if (Test-Path "$root\\dist") { Remove-Item -Recurse -Force "$root\\dist" }
}

python -m pip install --upgrade pip | Out-Null
python -m pip install --upgrade pyinstaller | Out-Null

python -m PyInstaller --noconfirm --clean FaceAttendance.spec

Write-Host "Built: $root\\dist\\FaceAttendance.exe"
