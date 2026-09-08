#!/usr/bin/env bash
# lock_rotation.sh — CONGELA la orientación de la pantalla en landscape para el spes.
#
# Por qué hace falta: el panel está muerto pero el ACELERÓMETRO sigue vivo. Con el
# auto-giro activo (y con juegos que piden 'sensorLandscape', como Free Fire), el
# teléfono rota solo según cómo esté apoyado físicamente, flipeando entre los dos
# landscapes (90° y 270°). Eso descoloca la vista de scrcpy y, peor, ROMPE el keymap
# de GG Mouse (que está calibrado a UNA orientación fija).
#
# Cómo lo fija de verdad: 'cmd window fixed-to-user-rotation enabled' hace que hasta
# las apps que fuerzan su orientación obedezcan; 'cmd window user-rotation lock ROT'
# clava la rotación. Así ni el menú ni Free Fire se giran solos. Verificado en el spes
# (crDroid, Android 15): tras el lock, mCurrentRotation queda fijo y no flipea.
#
# ROT: 1 = landscape (90°, por defecto) | 3 = landscape invertido (270°).
#   Si en scrcpy lo ves al REVÉS (180°), relanza con ROT=3 (o ROT=1) y quedará guardado.
#
# Uso:   ./scripts/lock_rotation.sh            (landscape 90°)
#        ROT=3 ./scripts/lock_rotation.sh      (landscape invertido)
#        ROT=free ./scripts/lock_rotation.sh   (revierte al auto-giro)
#        SERIAL=xxxxxxx ./scripts/lock_rotation.sh
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
ADB="$ROOT/tools/platform-tools/adb.exe"
ROT="${ROT:-1}"

# --- serial: autodetecta el único equipo si no se fija SERIAL ---
if [ -n "${SERIAL:-}" ]; then
  SARGS=(-s "$SERIAL")
else
  mapfile -t DEVS < <("$ADB" devices | awk 'NR>1 && $2=="device"{print $1}')
  if [ "${#DEVS[@]}" -eq 1 ]; then SARGS=(-s "${DEVS[0]}")
  elif [ "${#DEVS[@]}" -eq 0 ]; then echo "[!] No hay equipo en 'device'."; exit 1
  else echo "[!] Varios equipos: ${DEVS[*]}. Fija SERIAL=<serial>"; exit 1; fi
fi
adbx() { "$ADB" "${SARGS[@]}" "$@"; }

if [ "$ROT" = "free" ]; then
  echo "[*] Revirtiendo a auto-giro..."
  adbx shell 'settings put system accelerometer_rotation 1' 2>&1 || true
  adbx shell 'cmd window user-rotation free' 2>&1 || true
  echo "[OK] Auto-giro restaurado."; exit 0
fi

echo "[*] Congelando rotación en landscape (ROT=$ROT)..."
adbx shell 'settings put system accelerometer_rotation 0' 2>&1 || true   # apaga auto-giro legacy
adbx shell 'cmd window fixed-to-user-rotation enabled' 2>&1 || true      # apps forzadas también obedecen
adbx shell "cmd window user-rotation lock $ROT" 2>&1 || true             # clava la rotación

CUR="$(adbx shell 'cmd window user-rotation' 2>/dev/null | tr -d '\r')"
if printf '%s' "$CUR" | grep -q "lock $ROT"; then
  echo "[OK] Rotación bloqueada: $CUR"
else
  echo "[!] No confirmó el lock (leí: '$CUR'). Reintenta."; exit 1
fi
