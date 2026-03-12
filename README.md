# OAR

`OAR` stands for `oloids auto renamer`. It is a local-first desktop utility for AI video workflows focused on Kling videos and Higgsfield images.

## Features

- Watch a selected folder for new downloads
- Detect Kling and Higgsfield files using local regex rules
- Rename files with a lightweight date-based pattern
- Route Kling videos and Higgsfield images into separate folders
- Create day folders automatically like `[0311]`
- Store logs, settings, presets, and undo history in SQLite
- Undo recent processed actions from the GUI
- Preview images and videos from recent activity
- Filter logs by project in the app

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
set PYTHONPATH=src
python -m oloids_auto_renamer
```

## Build Windows App

Use the included PowerShell build script to create a smaller packaged app with `PyInstaller`.

```powershell
.\build_windows.ps1
```

If your virtual environment uses a different Python path:

```powershell
.\build_windows.ps1 -PythonExe ".venv\Scripts\python.exe"
```

Build output:

```text
dist\OAR\OAR.exe
```

## Lightweight Packaging Notes

The current build script trims a few unnecessary pieces for distribution:

- `--clean` to avoid stale build artifacts
- `--exclude-module tkinter`
- `--exclude-module unittest`
- only adds the app icon/image assets needed at runtime
- keeps multimedia imports explicit for video preview support

## Project Notes

Recent cleanup included:

- removing unused header/preview UI code from the main window
- reducing background render cost
- removing the shell drop shadow effect
- simplifying the main UI hierarchy for easier maintenance
