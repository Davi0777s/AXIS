#!/usr/bin/env bash
# make_magisk_boot.sh -- parchea firmware/stock/boot.img con Magisk 30.7 EN EL
# DISPOSITIVO (OrangeFox recovery con adbd root), y trae el resultado al host.
#
# NO se flashea nada: el .img resultante se arranca con `fastboot boot` (RAM,
# reversible). El parcheo se hace en el aarch64 del propio telefono con los
# binarios que extrajimos de Magisk.apk (tools/magisk-extracted/stage/).
#
# Requisitos: dispositivo RAM-booteado en recovery root (id -> uid=0) y
#             firmware/stock/boot.img ya volcado (scripts/dump_boot_from_recovery.sh).
# Salida:     firmware/patched/boot-magisk.img
set -euo pipefail
export MSYS_NO_PATHCONV=1
ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
ADB="$ROOT/tools/platform-tools/adb.exe"
SERIAL="${SERIAL:-cb0a4ce4}"
STAGE="$ROOT/tools/magisk-extracted/stage"
BOOT="$ROOT/firmware/stock/boot.img"
OUT="$ROOT/firmware/patched"; mkdir -p "$OUT"
WORK=/tmp/mpatch

[ -f "$BOOT" ] || { echo "ERROR: falta $BOOT (corre scripts/dump_boot_from_recovery.sh primero)"; exit 1; }

echo "[*] adb: $("$ADB" -s "$SERIAL" get-state 2>&1) / id: $("$ADB" -s "$SERIAL" shell id 2>&1 | head -c60)"
"$ADB" -s "$SERIAL" shell "id | grep -q uid=0" || { echo "ERROR: adbd no es root (no estas en recovery root)"; exit 1; }

echo "[*] Preparando $WORK en el dispositivo..."
"$ADB" -s "$SERIAL" shell "rm -rf $WORK; mkdir -p $WORK; mount -o remount,exec /tmp 2>/dev/null; true"

echo "[*] Empujando binarios Magisk + boot.img..."
for f in magiskboot magiskinit magisk busybox init-ld stub.apk boot_patch.sh util_functions.sh; do
  "$ADB" -s "$SERIAL" push "$STAGE/$f" "$WORK/$f" >/dev/null
done
"$ADB" -s "$SERIAL" push "$BOOT" "$WORK/boot.img" >/dev/null

echo "[*] Parcheando en el dispositivo (KEEPVERITY/KEEPFORCEENCRYPT=true)..."
"$ADB" -s "$SERIAL" shell "cd $WORK && chmod 755 magiskboot magiskinit magisk busybox boot_patch.sh init-ld && \
  KEEPVERITY=true KEEPFORCEENCRYPT=true RECOVERYMODE=false sh boot_patch.sh boot.img" 2>&1 | sed 's/^/    /'

echo "[*] ¿Se genero new-boot.img?"
"$ADB" -s "$SERIAL" shell "[ -f $WORK/new-boot.img ]" || { echo "ERROR: el parcheo no produjo new-boot.img"; exit 1; }

echo "[*] Trayendo el boot parcheado -> firmware/patched/boot-magisk.img"
"$ADB" -s "$SERIAL" pull "$WORK/new-boot.img" "$OUT/boot-magisk.img" >/dev/null
echo "[OK] $(wc -c < "$OUT/boot-magisk.img") bytes en firmware/patched/boot-magisk.img"
echo
echo "Siguiente:"
echo "  \"$ADB\" -s $SERIAL reboot bootloader        # desde recovery root, SIN combo"
echo "  \"$ROOT/tools/platform-tools/fastboot.exe\" boot firmware/patched/boot-magisk.img"
echo "  # -> Android arranca CON root en RAM; luego: scripts/disable_touch.sh"
