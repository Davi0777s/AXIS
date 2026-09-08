#!/usr/bin/env sh
# see_screen.sh -- THE goal. With adb AUTHORIZED, prove we can see the screen (a
# PNG from the device framebuffer) and mirror it live with scrcpy. The dead panel
# is irrelevant: screencap/scrcpy read the software-composited framebuffer.
#
# IMPORTANT: a sleeping display composites to BLACK. We force it awake first
# (this is why an early capture came out all-black on spes).
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
ADB="$ROOT/tools/platform-tools/adb.exe"
SCRCPY="$(ls "$ROOT"/tools/scrcpy-win64-*/scrcpy.exe 2>/dev/null | head -1 || true)"
SERIAL="${SERIAL:-cb0a4ce4}"
export ADB

echo "[see] waiting for authorized device $SERIAL ..."
"$ADB" -s "$SERIAL" wait-for-device
state=$("$ADB" -s "$SERIAL" get-state 2>/dev/null || echo unknown)
if [ "$state" != "device" ]; then
  echo "[see][ERROR] device is '$state' (need 'device'). Authorize adb first:" >&2
  echo "             fastboot boot <recovery.img> && scripts/authorize_via_recovery.sh" >&2
  exit 1
fi

# wake the display (asleep -> black capture) and keep it on while plugged
MSYS_NO_PATHCONV=1 "$ADB" -s "$SERIAL" shell 'svc power stayon true; input keyevent KEYCODE_WAKEUP; sleep 1' || true

mkdir -p "$ROOT/build"
OUT="$ROOT/build/pantalla.png"
echo "[see] capturing framebuffer -> build/pantalla.png"
"$ADB" -s "$SERIAL" exec-out screencap -p > "$OUT"
echo "[see] captured $(wc -c < "$OUT") bytes ($("$ADB" -s "$SERIAL" shell wm size 2>/dev/null))"

if [ -n "$SCRCPY" ]; then
  echo "[see] launching scrcpy (live, interactive)..."
  "$SCRCPY" -s "$SERIAL" --stay-awake --window-title "spes (dead panel) - MARE"
else
  echo "[see][WARN] scrcpy not found under tools/; the PNG proof is in build/" >&2
fi
