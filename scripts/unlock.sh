#!/usr/bin/env bash
# unlock.sh — desbloquea el spes a ciegas inyectando el PIN por adb.
#
# Motivo: la pantalla del PIN es una superficie SEGURA (anti-captura) → scrcpy
# y screencap la ven NEGRA. No se puede tocar lo que no se ve, así que en vez de
# tocar el teclado inyectamos las teclas del PIN directamente por eventos.
#
# El PIN se lee de build/pin.txt (una sola línea con los dígitos), un fichero
# LOCAL y gitignored: tu PIN nunca pasa por el chat ni por el repo.
#
# Uso:
#   echo 1234 > build/pin.txt      # (tú, una vez; sin espacios)
#   ./scripts/unlock.sh
set -euo pipefail
cd "$(dirname "$0")/.."
ADB=./tools/platform-tools/adb.exe
PINFILE=build/pin.txt

[ -f "$PINFILE" ] || { echo "ERROR: falta $PINFILE (haz: echo TUPIN > $PINFILE)"; exit 1; }
PIN="$(tr -d ' \r\n\t' < "$PINFILE")"
[ -n "$PIN" ] || { echo "ERROR: $PINFILE vacío"; exit 1; }
case "$PIN" in *[!0-9]*) echo "ERROR: el PIN debe ser solo dígitos"; exit 1;; esac

echo "[*] Despertando y revelando el teclado del PIN..."
$ADB shell input keyevent 224            # WAKEUP
$ADB shell input keyevent 82             # dismiss keyguard -> entrada PIN
sleep 0.4
$ADB shell input swipe 540 2000 540 600  # por si hace falta subir el panel
sleep 0.6

echo "[*] Inyectando el PIN (${#PIN} dígitos, a ciegas)..."
for (( i=0; i<${#PIN}; i++ )); do
  d="${PIN:$i:1}"
  $ADB shell input keyevent $((7 + d))   # KEYCODE_0=7 ... KEYCODE_9=16
done
$ADB shell input keyevent 66             # ENTER (confirma)
sleep 1.2

echo "[*] Verificando desbloqueo..."
SHOW=$($ADB shell dumpsys window 2>/dev/null | grep -m1 'mDreamingLockscreen=' || true)
FOCUS=$($ADB shell dumpsys window 2>/dev/null | grep -m1 'mCurrentFocus=' || true)
echo "    $SHOW"
echo "    $FOCUS"
if echo "$SHOW" | grep -q 'mDreamingLockscreen=false'; then
  echo "[OK] Keyguard fuera. Desbloqueado."
else
  echo "[!] Puede seguir bloqueado (¿PIN incorrecto o layout distinto?). Revisa build/desbloqueo.png"
fi
$ADB shell svc power stayon true >/dev/null 2>&1 || true
mkdir -p build
$ADB exec-out screencap -p > build/desbloqueo.png 2>/dev/null || true
echo "[*] Captura en build/desbloqueo.png"
