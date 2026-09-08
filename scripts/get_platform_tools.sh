#!/usr/bin/env sh
# get_platform_tools.sh -- download Google's official Android platform-tools into
# tools/. We do NOT reimplement adb/fastboot: they speak the device USB protocol
# and there is no learning value in rewriting them. We pin to Google's build.
# Usage: scripts/get_platform_tools.sh
set -eu
MARE_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
DEST="$MARE_ROOT/tools"
mkdir -p "$DEST"

case "$(uname -s)" in
  Linux*)  Z=platform-tools-latest-linux.zip ;;
  Darwin*) Z=platform-tools-latest-darwin.zip ;;
  *)       Z=platform-tools-latest-windows.zip ;;
esac
URL="https://dl.google.com/android/repository/$Z"

echo "[MARE] Downloading $URL"
if   command -v curl >/dev/null 2>&1; then curl -fL -o "$DEST/$Z" "$URL"
elif command -v wget >/dev/null 2>&1; then wget -O "$DEST/$Z" "$URL"
else echo "[MARE][ERROR] need curl or wget" >&2; exit 1; fi

if command -v unzip >/dev/null 2>&1; then
  ( cd "$DEST" && unzip -o "$Z" >/dev/null && rm -f "$Z" )
  echo "[MARE] platform-tools ready at $DEST/platform-tools"
else
  echo "[MARE] downloaded to $DEST/$Z -- unzip it manually (no 'unzip' found)"
fi
