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



## Download Ready-Made macOS Build

If you want other Mac users to download and install OAR directly from GitHub:

1. Push this repository to GitHub
2. Create a tag like `v0.1.0`
3. Push the tag

```bash
git tag v0.1.0
git push origin v0.1.0
```

GitHub Actions will build:

- `OAR-macOS.dmg`
- `OAR-macOS.zip`

You can then share the files from the GitHub release page.

Recommended Mac install flow:

1. Download `OAR-macOS.dmg`
2. Open the DMG
3. Drag `OAR.app` into `Applications`
4. On first launch, right-click `OAR.app` and choose `Open`

Note:

- this works best for quick sharing
- Gatekeeper may still warn because the app is not yet signed and notarized
## Build macOS App

Build the macOS `.app` bundle on a Mac machine.

```bash
chmod +x build_macos.sh
./build_macos.sh
```

If your virtual environment uses a different Python path:

```bash
./build_macos.sh /path/to/venv/bin/python
```

Build output:

```text
dist/OAR.app
```

Notes:

- macOS apps must be built on macOS
- the script generates `assets/oar.icns` from `assets/oar.png` automatically
- for sharing, compress `dist/OAR.app` into a `.zip`
- Gatekeeper may warn on another Mac unless the app is signed and notarized
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


