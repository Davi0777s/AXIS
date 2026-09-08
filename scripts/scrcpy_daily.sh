#!/usr/bin/env bash
# scrcpy_daily.sh — lanza scrcpy para USO DIARIO del spes (NO gaming).
#
# Diferencias con scrcpy_game.sh:
#   - Clava la rotación en VERTICAL (ROT=0), no en landscape. El spes tiene el panel
#     muerto y yace tumbado, así que el acelerómetro no puede fijar la orientación solo;
#     por eso hay que CLAVARLA. JUGAR.cmd la deja en landscape (ROT=1) y ese lock queda
#     guardado en el teléfono -> por eso al abrir scrcpy.exe a pelo salía en horizontal.
#     Este script la devuelve a vertical.
#   - Ratón y teclado NORMALES (sdk): puntero que se inyecta al hacer clic, no el HID de
#     GG Mouse. Así navegas el móvil con el ratón como siempre.
#   - Sin Shizuku, sin game_mode, sin GG Mouse: nada de la parafernalia de juego.
#   - Audio ENCENDIDO (por defecto scrcpy lo reenvía) para ver vídeos/llamadas con sonido.
#
# Uso:   ./scripts/scrcpy_daily.sh            (vertical, ratón normal, audio)
#        ROT=2 ./scripts/scrcpy_daily.sh      (vertical invertido, si lo ves boca abajo)
#        RES=1200 ./scripts/scrcpy_daily.sh   (max-size del stream; sube = más nitidez)
#        SERIAL=xxxxxxx ./scripts/scrcpy_daily.sh
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
SCRCPY="$ROOT/tools/scrcpy-win64-v4.1/scrcpy.exe"
ADB="$ROOT/tools/platform-tools/adb.exe"
RES="${RES:-1080}"       # max-size del stream (lado mayor). No cambia la resolución real.
FPS="${FPS:-60}"         # 60 basta de sobra para uso normal
ROT="${ROT:-0}"          # 0 = vertical (natural) | 2 = vertical invertido

# --- serial: usa $SERIAL si viene; si no, autodetecta el único equipo conectado ---
if [ -n "${SERIAL:-}" ]; then
  SARGS=(-s "$SERIAL")
else
  mapfile -t DEVS < <("$ADB" devices | awk 'NR>1 && $2=="device"{print $1}')
  if [ "${#DEVS[@]}" -eq 1 ]; then
    SARGS=(-s "${DEVS[0]}"); SERIAL="${DEVS[0]}"
    echo "[*] Serial autodetectado: $SERIAL"
  elif [ "${#DEVS[@]}" -eq 0 ]; then
    echo "[!] No hay ningún equipo en 'device'. Conecta el spes por USB."; exit 1
  else
    echo "[!] Varios equipos conectados: ${DEVS[*]}"
    echo "    Fija uno con:  SERIAL=<serial> $0"; exit 1
  fi
fi

# --- clava la rotación en VERTICAL (revierte el landscape que dejó JUGAR.cmd) ---
if [ "${ROTLOCK:-1}" = "1" ] && [ -x "$ROOT/scripts/lock_rotation.sh" ]; then
  ROT="$ROT" SERIAL="${SERIAL:-}" "$ROOT/scripts/lock_rotation.sh" \
    || echo "[!] No pude fijar la rotación vertical; sigue el arranque."
fi

echo "[*] scrcpy uso diario: vertical (ROT=$ROT) @ ${RES}px ${FPS}fps, ratón/teclado normales."
"$SCRCPY" "${SARGS[@]}" \
  --max-size="$RES" \
  --max-fps="$FPS" \
  --mouse=sdk \
  --keyboard=sdk \
  --stay-awake \
  --disable-screensaver \
  --window-title="spes (uso diario)"
