#!/usr/bin/env bash
# restore_apps.sh — revierte el debloat "dedicado a Free Fire": re-habilita apps que
# se apagaron con `pm disable-user`. Robusto: por defecto re-habilita TODO lo que esté
# deshabilitado; o pásale paquetes concretos para recuperar solo esos.
#   ./scripts/restore_apps.sh                 re-habilita TODO lo deshabilitado
#   ./scripts/restore_apps.sh com.spotify.music org.telegram.messenger   solo esos
#   ./scripts/restore_apps.sh --list          solo muestra lo deshabilitado, sin tocar
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
ADB="$ROOT/tools/platform-tools/adb.exe"
if [ -n "${SERIAL:-}" ]; then SARGS=(-s "$SERIAL"); else
  mapfile -t DEVS < <("$ADB" devices | awk 'NR>1 && $2=="device"{print $1}')
  [ "${#DEVS[@]}" -ge 1 ] && SARGS=(-s "${DEVS[0]}") || SARGS=()
fi
adbx() { "$ADB" "${SARGS[@]}" "$@"; }
adbx root >/dev/null 2>&1 || true

if [ "${1:-}" = "--list" ]; then
  echo "Deshabilitadas ahora:"; adbx shell 'pm list packages -d' | sed 's/package://' | tr -d '\r' | sort
  exit 0
fi

if [ "$#" -gt 0 ]; then
  TARGETS="$*"
else
  echo "[*] Re-habilitando TODAS las apps deshabilitadas..."
  TARGETS="$(adbx shell 'pm list packages -d' | sed 's/package://' | tr -d '\r')"
fi

n=0
for p in $TARGETS; do
  r="$(adbx shell pm enable "$p" 2>&1 | tr -d '\r')"
  echo "$r" | grep -qi 'new state: enabled' && { echo "ON   $p"; n=$((n+1)); } || echo "skip $p"
done
echo "[OK] Re-habilitadas: $n"
