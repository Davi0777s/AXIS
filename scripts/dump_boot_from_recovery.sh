#!/usr/bin/env sh
# dump_boot_from_recovery.sh -- with the device RAM-booted into a recovery whose
# adbd runs as root (`fastboot boot <recovery.img>`), pull the partitions we need
# to analyze and patch. Reads only; nothing is flashed or modified on device.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
ADB="$ROOT/tools/platform-tools/adb.exe"
SERIAL="${SERIAL:-cb0a4ce4}"
DEST="$ROOT/firmware/stock"; mkdir -p "$DEST"

"$ADB" -s "$SERIAL" wait-for-device
echo "[dump] adb state : $("$ADB" -s "$SERIAL" get-state 2>&1)"
echo "[dump] id        : $("$ADB" -s "$SERIAL" shell id 2>&1)"   # expect uid=0(root)

BN=/dev/block/by-name
for part in boot vendor_boot vbmeta; do
  got=""
  for suf in "" _a _b; do
    if "$ADB" -s "$SERIAL" shell "[ -e $BN/${part}${suf} ]" >/dev/null 2>&1; then
      echo "[dump] ${part}${suf} -> firmware/stock/${part}.img"
      "$ADB" -s "$SERIAL" exec-out "dd if=$BN/${part}${suf} 2>/dev/null" > "$DEST/${part}.img"
      echo "[dump]   $(wc -c < "$DEST/${part}.img") bytes"
      got=1; break
    fi
  done
  [ -n "$got" ] || echo "[dump][WARN] partition '$part' not found (any slot)"
done
echo "[dump] done. Next:"
echo "  python scripts/patch_boot_adb.py firmware/stock/boot.img -o build/boot-adb.img"
echo "  # then reboot to bootloader from recovery and:  fastboot boot build/boot-adb.img"
