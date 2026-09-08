#!/usr/bin/env bash
# scrcpy_game.sh — lanza scrcpy optimizado para MÍNIMA latencia (gaming) en el spes.
# Encoder HW Qualcomm (evita el fallback software que mete lag y el CodecException),
# 90fps (el panel es 90Hz), sin audio, video-buffer 0. Entrega además un mouse y un
# teclado HID VIRTUALES por el mismo cable USB (--mouse/--keyboard=uhid): así ves la
# pantalla en el PC y GG Mouse Pro captura ese mouse/teclado para mapear la mira,
# sin necesitar un hub OTG ni el cliente de Windows. Requiere GG Mouse ya activado
# (modo Shizuku o root). El ratón se captura al hacer clic en la ventana de scrcpy.
#
# Verificado en el spes (crDroid, Android 15): el único HW para h264 es
# OMX.qcom.video.encoder.avc; c2.android.avc.encoder / OMX.google.* son SOFTWARE.
# Por eso el encoder se fija explícito y se comprueba antes de lanzar (preflight):
# si un OTA lo quita, abortamos con aviso en vez de caer a software en silencio.
# Nota scrcpy 4.1: el flag es --video-buffer (el viejo --display-buffer ya no existe).
#
# Uso:   ./scripts/scrcpy_game.sh              (800px, 60fps, buf=16: config anti-tirones)
#        RES=1024 ./scripts/scrcpy_game.sh     (más nitidez; más carga de encoder)
#        RES=720  ./scripts/scrcpy_game.sh     (más margen de encoder si aún tira)
#        BR=24M   ./scripts/scrcpy_game.sh     (más bitrate = más nitidez, más USB)
#        FPS=90   ./scripts/scrcpy_game.sh     (solo si el juego rinde > 60 de verdad)
#        BUF=0    ./scripts/scrcpy_game.sh     (mínima latencia; puede reintroducir tirones)
#        BUF=32   ./scripts/scrcpy_game.sh     (máximo amortiguado, latencia +2 frames)
#        COPTS=   ./scripts/scrcpy_game.sh     (sin auto-recuperación de keyframes)
#        SCREENOFF=1 ./scripts/scrcpy_game.sh  (apaga el panel: baja SurfaceFlinger de ~70% a
#                 casi nada = más CPU para el juego. La pantalla ya está muerta, no se nota.
#                 Si un juego se PAUSA al apagar la pantalla, no uses el flag en ese juego.)
#        MOUSE=sdk ./scripts/scrcpy_game.sh    (puntero normal en vez de HID; no lo capta GG Mouse)
#        RECONNECT=1 ./scripts/scrcpy_game.sh  (relanza solo tras un corte de USB)
#        SERIAL=xxxxxxx ./scripts/scrcpy_game.sh
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
SCRCPY="$ROOT/tools/scrcpy-win64-v4.1/scrcpy.exe"
ADB="$ROOT/tools/platform-tools/adb.exe"
CODEC="${CODEC:-h264}"                                  # h264 = menor latencia de encode
ENC="${ENC:-OMX.qcom.video.encoder.avc}"               # HW Qualcomm (verificado en este ROM)
RES="${RES:-800}"       # max-size del STREAM (lado mayor). SOLO escala el vídeo al PC; NO toca la
                        # resolución real del display (1080x2400) → el HUD/keymap de GG Mouse NO se
                        # mueve. 800 = equilibrio nitidez/carga (el Encoder es EL cuello de botella
                        # en tirones: a 1024 el Venus se pasa de trabajo y arriesga frame skips).
                        # Sube a 1024 (más nitidez) si sobra, o baja a 720 para más margen.
BR="${BR:-12M}"          # bitrate de vídeo
FPS="${FPS:-60}"         # Free Fire en el spes está CAPADO a 60fps (verificado en logs: 55-61, nunca 90).
                         # Forzar 90 solo obliga al encoder a trabajar en vano y mete tirones. 60 = real.
BUF="${BUF:-16}"         # video-buffer (ms): 16 = amortigua el jitter del USB y elimina los
                         # "frames skipped" (los tirones). Añade ~1 frame de latencia (inapreciable).
                         # BUF=0 = mínima latencia bruta, pero el mínimo jitter ya se ve como tirón.
# COPTS: opciones del encoder. Default: keyframe cada ~1s + SPS/PPS por keyframe, así si el encoder
# se atasca o se pierde un paquete, el vídeo SE AUTO-RECUPERA en ~1s en vez de quedar congelado
# (el freeze de 0fps que salió en scrcpy_newd.log). Por defecto era vacío (sin auto-recuperación).
# NO usar latency=1,priority=0 en este spes: el encoder Venus se ATASCA (regresión 2026-08-04).
# i-frame-interval/repeat-headers son seguros y distintos a esa regresión.
COPTS="${COPTS:-i-frame-interval=1,repeat-headers=1}"
MOUSE="${MOUSE:-uhid}"   # uhid = mouse HID virtual (GG Mouse lo capta); sdk = puntero; disabled
KB="${KB:-uhid}"         # uhid = teclado HID virtual (GG Mouse lo capta); sdk; disabled

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

# --- preflight: el encoder pedido debe existir y ser HW ---
ENC_LINE="$("$SCRCPY" "${SARGS[@]}" --list-encoders 2>/dev/null \
             | grep -F -- "--video-encoder=$ENC" || true)"
if [ -z "$ENC_LINE" ]; then
  echo "[!] El encoder '$ENC' NO existe en este equipo. HW disponibles:"
  "$SCRCPY" "${SARGS[@]}" --list-encoders 2>/dev/null | grep -F '(hw)' || true
  echo "    Ajusta ENC=<encoder> (o CODEC) y reintenta."; exit 1
fi
if ! printf '%s' "$ENC_LINE" | grep -q '(hw)'; then
  echo "[!] '$ENC' NO es hardware (sería lag/CodecException). Línea: $ENC_LINE"; exit 1
fi
echo "[*] Encoder HW OK: $ENC ($CODEC) @ ${RES}px ${FPS}fps ${BR} buf=$BUF"

# --- asegura Shizuku + GG Mouse activos (mueren en cada reboot). SHIZUKU=0 lo salta. ---
if [ "${SHIZUKU:-1}" = "1" ] && [ -x "$ROOT/scripts/start_shizuku.sh" ]; then
  SERIAL="${SERIAL:-}" "$ROOT/scripts/start_shizuku.sh" || echo "[!] Shizuku no arrancó; el mouse en GG Mouse podría no mapear."
fi

# --- modo rendimiento: libera RAM + CPU/GPU a tope (evita los colgones). GAMEMODE=0 lo salta. ---
if [ "${GAMEMODE:-1}" = "1" ] && [ -x "$ROOT/scripts/game_mode.sh" ]; then
  SERIAL="${SERIAL:-}" "$ROOT/scripts/game_mode.sh" || true
fi

# --- renice del servidor scrcpy, EN SEGUNDO PLANO: game_mode corre ANTES del launch así que
#     pidof sale vacío. Aquí se espera a que el servidor exista (poll 20s) y se le da -15,
#     para que el capture+encode no pierda frames contra el juego. ---
(
  for i in $(seq 1 20); do
    P="$("$ADB" "${SARGS[@]}" shell 'pidof com.genymobile.scrcpy' 2>/dev/null | tr -d '\r')"
    if [ -n "$P" ]; then
      "$ADB" "${SARGS[@]}" shell "renice -n -15 -p $P >/dev/null 2>&1" || true
      break
    fi
    sleep 1
  done
) >/dev/null 2>&1 &

# --- fuerza landscape. IMPRESCINDIBLE en el spes: la pantalla está MUERTA y el teléfono
# yace tumbado, así que el acelerómetro NO puede indicar landscape → con auto-giro el juego
# se queda en VERTICAL (deformado). Por eso se clava a landscape. VA AL FINAL: GG Mouse, al
# lanzarse, resetea la rotación a 'free', así que hay que fijarla DESPUÉS o no aguanta.
# ROT=1 = landscape correcto (verificado: texto derecho); ROT=3 invierte; ROTLOCK=0 lo salta.
if [ "${ROTLOCK:-1}" = "1" ] && [ -x "$ROOT/scripts/lock_rotation.sh" ]; then
  ROT="${ROT:-1}" SERIAL="${SERIAL:-}" "$ROOT/scripts/lock_rotation.sh" || echo "[!] No pude bloquear la rotación; sigue el arranque."
fi

launch() {
  local copt_args=()
  local extra=()
  if [ "${LAT:-1}" = "1" ] && [ -n "$COPTS" ]; then
    copt_args=(--video-codec-options="$COPTS")
  fi
  if [ "${SCREENOFF:-0}" = "1" ]; then
    extra=(--turn-screen-off)
  fi
  "$SCRCPY" "${SARGS[@]}" \
    --video-codec="$CODEC" \
    --video-encoder="$ENC" \
    "${copt_args[@]}" \
    "${extra[@]}" \
    --max-size="$RES" \
    --max-fps="$FPS" \
    --video-bit-rate="$BR" \
    --no-audio \
    --video-buffer="$BUF" \
    --mouse="$MOUSE" \
    --keyboard="$KB" \
    --stay-awake \
    --disable-screensaver \
    --window-title="spes GAMING ${FPS}fps"
}

if [ "${RECONNECT:-0}" = "1" ]; then
  echo "[*] Modo RECONNECT: relanzo tras cada corte (Ctrl-C dos veces para salir)."
  while true; do
    launch || true
    echo "[*] scrcpy terminó; reintento en 2s..."
    "$ADB" "${SARGS[@]}" wait-for-device 2>/dev/null || true
    sleep 2
  done
else
  launch
fi
