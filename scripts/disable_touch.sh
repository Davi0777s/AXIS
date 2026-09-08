#!/usr/bin/env bash
# disable_touch.sh -- desactiva el digitizer fisico fts_ts para que el telefono
# se controle SOLO desde el PC (scrcpy inyecta por uinput, no por fts_ts).
#
# Metodo (probado en spes / crDroid 11.1.0, kernel 4.19-NigeaSilver):
#   root via `adb root` (crDroid lo permite) -> unbind del driver i2c fts_ts.
#   El kernel 4.19 NO tiene /sys/class/input/inputN/inhibited (API de Linux 5.4),
#   asi que usamos el unbind del bus i2c, que elimina el input device por completo.
#   Reversible con bind (o reboot). Re-ejecutar tras cada arranque.
set -euo pipefail
export MSYS_NO_PATHCONV=1
ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
ADB="$ROOT/tools/platform-tools/adb.exe"
SERIAL="${SERIAL:-cb0a4ce4}"
DRV=/sys/bus/i2c/drivers/fts_ts

echo "[*] Pidiendo root (adb root)..."
"$ADB" -s "$SERIAL" root >/dev/null 2>&1 || true
"$ADB" -s "$SERIAL" wait-for-device
"$ADB" -s "$SERIAL" shell 'id | grep -q uid=0' || { echo "ERROR: no hay root (adb root fallo)"; exit 1; }

# localizar el id del device fts (p.ej. 1-0038)
DEV="$("$ADB" -s "$SERIAL" shell "ls $DRV/ | grep -E '^[0-9]+-00'" | tr -d '\r' | head -1)"
if [ -z "$DEV" ]; then
  echo "[i] fts_ts ya parece desacoplado (sin device en $DRV). event4:"
  "$ADB" -s "$SERIAL" shell 'ls /dev/input/event4 2>&1'
  exit 0
fi
echo "[*] Desacoplando fts_ts device: $DEV"
"$ADB" -s "$SERIAL" shell "echo $DEV > $DRV/unbind"
sleep 1

echo "[*] Verificacion:"
echo "    driver dir: $("$ADB" -s "$SERIAL" shell "ls $DRV/ | tr '\n' ' '")"
echo "    event4    : $("$ADB" -s "$SERIAL" shell 'ls /dev/input/event4 2>&1')"
if "$ADB" -s "$SERIAL" shell 'ls /dev/input/event4' >/dev/null 2>&1; then
  echo "[!] event4 sigue existiendo; el unbind no surtio efecto."
else
  echo "[OK] Tactil fisico desactivado. Control 100% PC (scrcpy/uinput)."
fi
