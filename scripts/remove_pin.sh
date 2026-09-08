#!/usr/bin/env bash
# remove_pin.sh -- ELIMINA el PIN del dispositivo y desactiva el bloqueo de
# pantalla por completo, para que arranque DIRECTO al escritorio (acceso
# inmediato desde el PC). Usa el mecanismo oficial `locksettings`, que re-cifra
# el almacenamiento FBE al estado "sin credencial" de forma segura (NO borra
# ficheros de gatekeeper/synthetic-password a mano: eso bricka /data).
#
# El PIN ACTUAL se lee de build/pin.txt (local, gitignored): se necesita como
# --old para autorizar el borrado. Tu PIN no pasa por el chat ni por el repo.
#
# Uso:  echo TUPIN > build/pin.txt   &&   ./scripts/remove_pin.sh
set -euo pipefail
export MSYS_NO_PATHCONV=1
ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
ADB="$ROOT/tools/platform-tools/adb.exe"
SERIAL="${SERIAL:-cb0a4ce4}"
PINFILE="$ROOT/build/pin.txt"

[ -f "$PINFILE" ] || { echo "ERROR: falta build/pin.txt (haz: echo TUPIN > build/pin.txt)"; exit 1; }
PIN="$(tr -d ' \r\n\t' < "$PINFILE")"
[ -n "$PIN" ] || { echo "ERROR: build/pin.txt vacio"; exit 1; }

echo "[*] Asegurando root..."
"$ADB" -s "$SERIAL" root >/dev/null 2>&1 || true
"$ADB" -s "$SERIAL" wait-for-device
"$ADB" -s "$SERIAL" shell 'id | grep -q uid=0' || { echo "ERROR: sin root"; exit 1; }

echo "[*] Verificando el PIN actual..."
if ! "$ADB" -s "$SERIAL" shell "locksettings verify --old '$PIN'" 2>&1 | grep -qi "successful"; then
  echo "ERROR: el PIN de build/pin.txt no verifica. Corrige el fichero y reintenta."
  "$ADB" -s "$SERIAL" shell "locksettings verify --old '$PIN'" 2>&1 | head -2
  exit 1
fi
echo "    PIN correcto."

echo "[*] Eliminando la credencial (locksettings clear)..."
"$ADB" -s "$SERIAL" shell "locksettings clear --old '$PIN'" 2>&1 | sed 's/^/    /'

echo "[*] Desactivando el keyguard por completo (arranque directo)..."
"$ADB" -s "$SERIAL" shell "locksettings set-disabled true" 2>&1 | sed 's/^/    /'

echo "[*] Estado final:"
echo "    get-disabled = $("$ADB" -s "$SERIAL" shell 'locksettings get-disabled' 2>&1)"
echo "    verify       = $("$ADB" -s "$SERIAL" shell 'locksettings verify' 2>&1 | head -1)"

echo "[*] Despertando y capturando para confirmar que NO hay bloqueo..."
"$ADB" -s "$SERIAL" shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1 || true
"$ADB" -s "$SERIAL" shell svc power stayon true >/dev/null 2>&1 || true
sleep 1
mkdir -p "$ROOT/build"
"$ADB" -s "$SERIAL" exec-out screencap -p > "$ROOT/build/sin_pin.png" 2>/dev/null || true
echo "[OK] PIN eliminado y bloqueo desactivado. Captura en build/sin_pin.png"
echo "     (Si build/sin_pin.png muestra el LAUNCHER y no un teclado, listo.)"

# Borrado seguro del fichero del PIN: ya no se necesita y no debe quedar en disco.
if command -v shred >/dev/null 2>&1; then shred -u "$PINFILE" 2>/dev/null || rm -f "$PINFILE"; else rm -f "$PINFILE"; fi
echo "[*] build/pin.txt eliminado del disco."
