param(
    [string]$PythonExe = ".venv\Scripts\python.exe"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw "Python executable not found: $PythonExe"
}

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$mainModule = Join-Path $projectRoot "src\oloids_auto_renamer\__main__.py"
$iconPath = Join-Path $projectRoot "assets\oar.ico"
$pngPath = Join-Path $projectRoot "assets\oar.png"
$distPath = Join-Path $projectRoot "dist"
$buildPath = Join-Path $projectRoot "build"

& $PythonExe -m pip install --upgrade pyinstaller

& $PythonExe -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name OAR `
    --icon $iconPath `
    --add-data "$pngPath;assets" `
    --hidden-import PySide6.QtMultimedia `
    --hidden-import PySide6.QtMultimediaWidgets `
    --exclude-module tkinter `
    --exclude-module unittest `
    --distpath $distPath `
    --workpath $buildPath `
    $mainModule

Write-Host ""
Write-Host "Build complete:"
Write-Host "  $distPath\OAR\OAR.exe"
