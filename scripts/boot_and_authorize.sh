#!/usr/bin/env bash
set -euo pipefail
export MSYS_NO_PATHCONV=1
ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
ADB="$ROOT/tools/platform-tools/adb.exe"
FB="$ROOT/tools/platform-tools/fastboot.exe"
SERIAL="${SERIAL:-cb0a4ce4}"
PUB="${PUB:-$HOME/.android/adbkey.pub}"
PATCHED_REL="build/boot-adb.img"

echo "================================================================="
echo " MARE — Autorización directa con Android Boot Parcheado (adb_keys)"
echo "================================================================="
echo "[1/4] Verificando archivos..."
if [ ! -f "$ROOT/$PATCHED_REL" ]; then
  echo "ERROR: no se encuentra $ROOT/$PATCHED_REL"
  exit 1
fi
echo "     - Imagen parcheada: $PATCHED_REL"
echo "     - Clave pública   : $PUB"

echo "[2/4] Verificando modo Fastboot..."
while true; do
  state=$("$FB" devices 2>/dev/null | grep "$SERIAL" | awk '{print $2}' || true)
  if [ "$state" = "fastboot" ]; then
    echo "[OK] Dispositivo detectado en Fastboot."
    break
  fi
  printf "\r     Esperando Fastboot (Vol- + Power)..."
  sleep 1
done
echo ""

echo "[3/4] Cargando Android Boot Parcheado a RAM (fastboot boot)..."
cd "$ROOT"
"$FB" boot "$PATCHED_REL"

echo "[4/4] Esperando a que Android inicie y conecte ADB..."
for i in $(seq 1 120); do
  sleep 2
  raw=$("$ADB" devices 2>/dev/null || true)
  state=$(echo "$raw" | grep "$SERIAL" | awk '{print $2}' || true)
  printf "\r     [%2ds] Estado ADB: %-15s" "$((i*2))" "${state:-esperando}"
  
  if [ "$state" = "device" ]; then
    echo ""
    echo "[OK] ¡CONECTADO Y AUTORIZADO!"
    
    echo "[*] Obteniendo acceso root ADB..."
    "$ADB" -s "$SERIAL" root 2>&1 || true
    sleep 2
    
    echo "[*] Escribiendo clave permanente en /data/misc/adb/adb_keys..."
    "$ADB" -s "$SERIAL" shell 'mount /data 2>/dev/null; mkdir -p /data/misc/adb' 2>&1 || true
    { cat "$PUB"; echo; } | "$ADB" -s "$SERIAL" shell 'cat >> /data/misc/adb/adb_keys' 2>&1 || true
    "$ADB" -s "$SERIAL" shell '
      sort -u /data/misc/adb/adb_keys -o /data/misc/adb/adb_keys 2>/dev/null || true
      chown 1000:2000 /data/misc/adb/adb_keys 2>/dev/null || true
      chmod 0640 /data/misc/adb/adb_keys 2>/dev/null || true
      restorecon /data/misc/adb/adb_keys 2>/dev/null || true
    ' 2>&1 || true
    echo "[OK] Clave registrada en /data con éxito."
    
    echo "================================================================="
    echo " ¡PROCESO COMPLETADO! El teléfono está AUTORIZADO."
    echo " Puedes lanzar USAR.cmd o JUGAR.cmd inmediatamente."
    echo "================================================================="
    exit 0
  fi
done

echo ""
echo "[!] Tiempo de espera agotado."
exit 1
