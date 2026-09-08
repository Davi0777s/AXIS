#!/usr/bin/env sh
# authorize_via_recovery.sh -- with the device RAM-booted into a recovery whose
# adbd runs as root (`fastboot boot <recovery.img>`; RAM boot is NOT AVB-verified
# on an unlocked bootloader, so it runs -- unlike flashing a modified partition),
# install THIS host's adb key into the MAIN system. After a normal reboot, adbd
# trusts us with no on-screen RSA prompt, persistently.
#
# This is the path that WORKED on spes (2026-07-31): OrangeFox R12.0 -> root adb
# -> write /data/misc/adb/adb_keys -> reboot -> `adb devices` = device.
#
# Nothing is flashed. The only change is adding our pubkey to
# /data/misc/adb/adb_keys (device-encrypted storage, benign and removable).
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
ADB="$ROOT/tools/platform-tools/adb.exe"
SERIAL="${SERIAL:-cb0a4ce4}"
PUB="${PUB:-$HOME/.android/adbkey.pub}"

echo "[auth] waiting for recovery adb ..."
"$ADB" -s "$SERIAL" wait-for-recovery        # NOT wait-for-device (that waits for 'device' state)
echo "[auth] id: $("$ADB" -s "$SERIAL" shell id 2>&1)"      # expect uid=0(root)

# recovery usually automounts /data; ensure the dir exists
"$ADB" -s "$SERIAL" shell 'mount /data 2>/dev/null; mkdir -p /data/misc/adb' || true

# Inject via STDIN (not `adb push`): on Git Bash a /remote/path arg gets rewritten
# to a Windows path by MSYS. MSYS_NO_PATHCONV=1 also protects the shell command.
echo "[auth] appending pubkey to /data/misc/adb/adb_keys"
{ cat "$PUB"; echo; } | MSYS_NO_PATHCONV=1 "$ADB" -s "$SERIAL" shell 'cat >> /data/misc/adb/adb_keys'
MSYS_NO_PATHCONV=1 "$ADB" -s "$SERIAL" shell '
  sort -u /data/misc/adb/adb_keys -o /data/misc/adb/adb_keys 2>/dev/null || true
  chown 1000:2000 /data/misc/adb/adb_keys 2>/dev/null || true   # system:shell
  chmod 0640 /data/misc/adb/adb_keys 2>/dev/null || true
  restorecon /data/misc/adb/adb_keys 2>/dev/null || true        # u:object_r:adb_keys_file:s0
  echo "--- /data/misc/adb/adb_keys now:"; cat /data/misc/adb/adb_keys
'
echo "[auth] rebooting to system; after boot run scripts/see_screen.sh"
"$ADB" -s "$SERIAL" reboot
