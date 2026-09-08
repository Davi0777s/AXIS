#!/usr/bin/env bash
# reinstall_wifi_sae_fix.sh
# Reinstala el RRO que desactiva el auto-upgrade a WPA3-SAE del framework WiFi,
# para que el spes conecte a redes en transición WPA2/WPA3 (p.ej. "Yovani")
# por WPA2-PSK — el firmware WCN de este equipo tiene el SAE roto.
#
# Requisitos: adb root (crDroid lo da) + AVB/verity desactivado (este ROM lo está,
# por eso /product es remontable en rw). Re-ejecutar SOLO si un OTA/reflash borra
# el overlay de /product/overlay.
#
# Uso:
#   ./reinstall_wifi_sae_fix.sh                instala + reboot + verifica al arrancar
#   ./reinstall_wifi_sae_fix.sh --verify-only  solo comprueba el overlay activo (no toca nada)
#   SERIAL=xxxxxxx ./reinstall_wifi_sae_fix.sh fuerza un serial concreto
set -euo pipefail
export MSYS_NO_PATHCONV=1
ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
ADB="$ROOT/tools/platform-tools/adb.exe"
APK="$ROOT/wifi-fix/nosae-wpa3-disable.apk"
OVERLAY_PKG="com.android.wifi.resources"
OVERLAY_RES="$OVERLAY_PKG:bool/config_wifiSaeUpgradeEnabled"

# --- serial: usa $SERIAL si viene; si no, autodetecta el único equipo conectado ---
if [ -n "${SERIAL:-}" ]; then
  ARGS=(-s "$SERIAL")
else
  mapfile -t DEVS < <("$ADB" devices | awk 'NR>1 && $2=="device"{print $1}')
  if [ "${#DEVS[@]}" -eq 1 ]; then
    ARGS=(-s "${DEVS[0]}")
    echo "[*] Serial autodetectado: ${DEVS[0]}"
  elif [ "${#DEVS[@]}" -eq 0 ]; then
    ARGS=()   # sin equipo aún: wait-for-device esperará a que aparezca
  else
    echo "[!] Varios equipos conectados: ${DEVS[*]}"
    echo "    Fija uno con:  SERIAL=<serial> $0"
    exit 1
  fi
fi

adbx() { "$ADB" "${ARGS[@]}" "$@"; }

# --- espera boot real (adbd puede responder antes de que el boot termine) ---
wait_boot() {
  adbx wait-for-device
  echo -n "[*] Esperando sys.boot_completed"
  for _ in $(seq 1 60); do
    if [ "$(adbx shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ]; then
      echo " -> listo"; return 0
    fi
    echo -n "."; sleep 2
  done
  echo; echo "[!] Timeout esperando boot_completed"; return 1
}

# --- verifica que el overlay está activo y el recurso resuelve a false ---
verify() {
  adbx wait-for-device
  echo "[*] Overlays 'nosae' registrados:"
  adbx shell cmd overlay list "$OVERLAY_PKG" | grep -i nosae || {
    echo "[!] El overlay nosae NO aparece en la lista"; return 1; }
  local val
  val="$(adbx shell cmd overlay lookup "$OVERLAY_PKG" "$OVERLAY_RES" 2>/dev/null | tr -d '\r')"
  echo "[*] $OVERLAY_RES = ${val:-<vacío>}"
  if [ "$val" = "false" ]; then
    echo "[OK] SAE auto-upgrade DESACTIVADO — el fix está activo."
    return 0
  fi
  echo "[!] Se esperaba 'false'. El fix NO está activo."
  return 1
}

# --- modo solo-verificación ---
if [ "${1:-}" = "--verify-only" ]; then
  adbx root >/dev/null 2>&1 || true
  verify
  exit $?
fi

# --- instalación ---
adbx root >/dev/null 2>&1 || true
adbx wait-for-device
[ -f "$APK" ] || { echo "[!] No existe el APK: $APK"; exit 1; }
adbx push "$APK" /data/local/tmp/nosae.apk
adbx shell 'mount -o remount,rw /product && \
  mkdir -p /product/overlay && \
  cp /data/local/tmp/nosae.apk /product/overlay/nosae.apk && \
  chmod 644 /product/overlay/nosae.apk && chown root:root /product/overlay/nosae.apk && \
  chcon u:object_r:system_file:s0 /product/overlay/nosae.apk && \
  mount -o remount,ro /product && echo "[*] instalado en /product/overlay"'

echo "[*] Reiniciando para aplicar el overlay al arranque..."
adbx reboot
wait_boot
adbx root >/dev/null 2>&1 || true
verify
