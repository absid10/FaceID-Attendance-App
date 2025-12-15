param(
    [switch]$Clean
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $py = $venvPython
} else {
    $py = "python"
}

if ($Clean) {
    if (Test-Path "$root\\build") { Remove-Item -Recurse -Force "$root\\build" }
    if (Test-Path "$root\\dist") { Remove-Item -Recurse -Force "$root\\dist" }
    if (Test-Path "$root\\release") { Remove-Item -Recurse -Force "$root\\release" }
}

& $py -m pip install --upgrade pip | Out-Null
& $py -m pip install -r (Join-Path $root 'requirements.txt') | Out-Null
& $py -m pip install --upgrade pyinstaller | Out-Null

& $py -m PyInstaller --noconfirm --clean FaceAttendance.spec

$release = Join-Path $root 'release'
New-Item -ItemType Directory -Force -Path $release | Out-Null

$builtExe = Join-Path $root 'dist\\FaceAttendance.exe'
$releaseExe = Join-Path $release 'FaceAttendance.exe'
Copy-Item -Force $builtExe $releaseExe

# Place runtime-writable folders next to the exe for easy double-click runs.
if ((Test-Path (Join-Path $root 'dist\\data')) -and -not (Test-Path (Join-Path $release 'data'))) {
    Move-Item -Force (Join-Path $root 'dist\\data') (Join-Path $release 'data')
}
if ((Test-Path (Join-Path $root 'dist\\models')) -and -not (Test-Path (Join-Path $release 'models'))) {
    Move-Item -Force (Join-Path $root 'dist\\models') (Join-Path $release 'models')
}

New-Item -ItemType Directory -Force -Path (Join-Path $release 'data') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $release 'models') | Out-Null

# Seed release/data with CSV templates if missing (does not copy any dataset images).
$seedFiles = @('Attendance.csv','UserDetails.csv','EnrollmentRequests.csv')
foreach ($f in $seedFiles) {
    $src = Join-Path $root (Join-Path 'data' $f)
    $dst = Join-Path $release (Join-Path 'data' $f)
    if ((Test-Path $src) -and -not (Test-Path $dst)) {
        Copy-Item -Force $src $dst
    }
}

Write-Host "Built (onefile): $builtExe"
Write-Host "Ready to run (double-click): $releaseExe"
