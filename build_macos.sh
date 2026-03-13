#!/usr/bin/env bash
set -euo pipefail

PYTHON_EXE="${1:-.venv/bin/python}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_MODULE="$PROJECT_ROOT/src/oloids_auto_renamer/__main__.py"
PNG_ICON="$PROJECT_ROOT/assets/oar.png"
ICNS_ICON="$PROJECT_ROOT/assets/oar.icns"
DIST_PATH="$PROJECT_ROOT/dist"
BUILD_PATH="$PROJECT_ROOT/build"
ICONSET_PATH="$BUILD_PATH/oar.iconset"
DMG_STAGING_PATH="$BUILD_PATH/dmg"
APP_PATH="$DIST_PATH/OAR.app"
ZIP_PATH="$DIST_PATH/OAR-macOS.zip"
DMG_PATH="$DIST_PATH/OAR-macOS.dmg"

if [[ ! -x "$PYTHON_EXE" ]]; then
  echo "Python executable not found: $PYTHON_EXE"
  exit 1
fi

if [[ ! -f "$PNG_ICON" ]]; then
  echo "Required icon not found: $PNG_ICON"
  exit 1
fi

create_icns() {
  rm -rf "$ICONSET_PATH"
  mkdir -p "$ICONSET_PATH"

  sips -z 16 16 "$PNG_ICON" --out "$ICONSET_PATH/icon_16x16.png" >/dev/null
  sips -z 32 32 "$PNG_ICON" --out "$ICONSET_PATH/icon_16x16@2x.png" >/dev/null
  sips -z 32 32 "$PNG_ICON" --out "$ICONSET_PATH/icon_32x32.png" >/dev/null
  sips -z 64 64 "$PNG_ICON" --out "$ICONSET_PATH/icon_32x32@2x.png" >/dev/null
  sips -z 128 128 "$PNG_ICON" --out "$ICONSET_PATH/icon_128x128.png" >/dev/null
  sips -z 256 256 "$PNG_ICON" --out "$ICONSET_PATH/icon_128x128@2x.png" >/dev/null
  sips -z 256 256 "$PNG_ICON" --out "$ICONSET_PATH/icon_256x256.png" >/dev/null
  sips -z 512 512 "$PNG_ICON" --out "$ICONSET_PATH/icon_256x256@2x.png" >/dev/null
  sips -z 512 512 "$PNG_ICON" --out "$ICONSET_PATH/icon_512x512.png" >/dev/null
  cp "$PNG_ICON" "$ICONSET_PATH/icon_512x512@2x.png"

  iconutil -c icns "$ICONSET_PATH" -o "$ICNS_ICON"
}

create_dmg() {
  rm -rf "$DMG_STAGING_PATH"
  mkdir -p "$DMG_STAGING_PATH"
  cp -R "$APP_PATH" "$DMG_STAGING_PATH/OAR.app"
  ln -s /Applications "$DMG_STAGING_PATH/Applications"
  rm -f "$DMG_PATH"
  hdiutil create -volname "OAR" -srcfolder "$DMG_STAGING_PATH" -ov -format UDZO "$DMG_PATH" >/dev/null
}

if [[ ! -f "$ICNS_ICON" ]]; then
  create_icns
fi

"$PYTHON_EXE" -m pip install --upgrade pyinstaller

"$PYTHON_EXE" -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name OAR \
  --icon "$ICNS_ICON" \
  --add-data "$PNG_ICON:assets" \
  --hidden-import PySide6.QtMultimedia \
  --hidden-import PySide6.QtMultimediaWidgets \
  --exclude-module tkinter \
  --exclude-module unittest \
  --distpath "$DIST_PATH" \
  --workpath "$BUILD_PATH" \
  "$MAIN_MODULE"

rm -f "$ZIP_PATH"
ditto -c -k --sequesterRsrc --keepParent "$APP_PATH" "$ZIP_PATH"
create_dmg

echo

echo "Build complete:"
echo "  $APP_PATH"
echo "  $ZIP_PATH"
echo "  $DMG_PATH"
echo

echo "Share the .dmg for the most Mac-like install flow."
