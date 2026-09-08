#!/usr/bin/env bash
# start_shizuku.sh — arranca el servidor Shizuku (como ROOT, vía adb root) para que
# GG Mouse Pro quede activado tras un reinicio, SIN cliente de Windows ni Magisk.
#
# Por qué hace falta: Shizuku muere en cada reboot y, sin Magisk, no se autoarranca
# en el boot. Como el spes tiene la pantalla muerta y SIEMPRE se juega desde el PC
# (scrcpy), lo natural es encender Shizuku desde aquí. Es idempotente: si ya corre,
# no hace nada. scrcpy_game.sh lo llama solo al lanzar.
#
# Uso:   ./scripts/start_shizuku.sh              (arranca + verifica)
#        SERIAL=xxxxxxx ./scripts/start_shizuku.sh
set -euo pipefail
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'
ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
ADB="$ROOT/tools/platform-tools/adb.exe"
PKG="com.zjx.ztezscreenshot"                      # GG Mouse Pro
START_SH="/storage/emulated/0/Android/data/moe.shizuku.privileged.api/start.sh"

# --- serial: autodetecta el único equipo si no se fija SERIAL ---
if [ -n "${SERIAL:-}" ]; then
  SARGS=(-s "$SERIAL")
else
  mapfile -t DEVS < <("$ADB" devices | awk 'NR>1 && $2=="device"{print $1}')
  if [ "${#DEVS[@]}" -eq 1 ]; then SARGS=(-s "${DEVS[0]}")
  elif [ "${#DEVS[@]}" -eq 0 ]; then SARGS=()
  else echo "[!] Varios equipos: ${DEVS[*]}. Fija SERIAL=<serial>"; exit 1; fi
fi
adbx() { "$ADB" "${SARGS[@]}" "$@"; }

adbx root >/dev/null 2>&1 || true
adbx wait-for-device

# --- Shizuku: SIEMPRE reinicia fresco. Un shizuku_server que sobrevive a un
# 'stop; start' (reinicio de framework) queda ZOMBI: el proceso vive pero perdió
# el binder al system_server nuevo y NO inyecta. Por eso se mata y se relanza. ---
echo "[*] (Re)arrancando Shizuku fresco (como root)..."
adbx shell 'kill -9 $(pidof shizuku_server) 2>/dev/null; true'
sleep 1
adbx shell "sh $START_SH" 2>&1 | grep -iE 'starting server|exit with' || true
sleep 2

# --- verifica servidor root ---
if adbx shell 'ps -A -o USER,NAME | grep -q "root .*shizuku_server"'; then
  echo "[OK] shizuku_server corriendo como root."
else
  echo "[!] Shizuku no quedó activo. Abre la app Shizuku y reintenta."; exit 1
fi

# --- (RE)ACTIVA GG Mouse. CLAVE: si GG Mouse ya estaba abierto ANTES de que Shizuku
# arrancara, se quedó "No activado" y traerlo al frente con 'monkey' NO re-dispara la
# activación (no vuelve a buscar Shizuku). Por eso lo MATAMOS y lo relanzamos en frío:
# al arrancar con shizuku_server ya vivo, se conecta por binder y lanza su servicio de
# inyección 'com.zjx.ztezscreenshot:activate_service' COMO ROOT. Verificado en el spes. ---
echo "[*] Reactivando GG Mouse en frío (force-stop + relanzar)..."
adbx shell "am force-stop $PKG" >/dev/null 2>&1 || true
sleep 1
adbx shell "monkey -p $PKG -c android.intent.category.LAUNCHER 1" >/dev/null 2>&1 || true

# --- espera hasta 15s a que aparezca el servicio de inyección root ---
ACTIVATED=0
for i in $(seq 1 15); do
  if adbx shell "ps -A -o USER,NAME | grep -q 'root .*$PKG:activate_service'"; then
    ACTIVATED=1; break
  fi
  sleep 1
done
if [ "$ACTIVATED" = "1" ]; then
  echo "[OK] GG Mouse ACTIVADO (servicio de inyección root vivo)."
else
  echo "[!] GG Mouse no lanzó su servicio de inyección. Revisa que el permiso Shizuku"
  echo "    siga concedido (Shizuku → Apps → GG Mouse) y reintenta."; exit 1
fi
