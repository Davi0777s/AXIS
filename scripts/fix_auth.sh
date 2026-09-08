#!/usr/bin/env bash
# fix_auth.sh -- TODO EN UNO: desde fastboot, autoriza ADB permanentemente.
# Uso: poner el telefono en fastboot (Vol- + Power) y ejecutar este script.
#   1. Arranca OrangeFox recovery en RAM (para tener root via ADB)
#   2. Espera a que ADB aparezca (polling robusto, sin hang)
#   3. Inyecta la clave publica en /data/misc/adb/adb_keys (PERMANENTE)
#   4. Rebootea a Android
#   5. Verifica que quedo autorizado
set -euo pipefail
export MSYS_NO_PATHCONV=1

ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
ADB="$ROOT/tools/platform-tools/adb.exe"
FB="$ROOT/tools/platform-tools/fastboot.exe"
SERIAL="${SERIAL:-cb0a4ce4}"
PUB="${PUB:-$HOME/.android/adbkey.pub}"
RECOVERY_IMG="$ROOT/firmware/stock/orangefox-recovery.img"
MAX_WAIT=300   # OrangeFox es no-deterministico: puede tardar hasta ~3 min

echo "============================================================"
echo "  MARE — Fix ADB Unauthorized (todo en uno)"
echo "============================================================"
echo ""

# --- Verificaciones previas ---
if [ ! -f "$FB" ]; then
  echo "[ERROR] No se encuentra fastboot: $FB"
  exit 1
fi
if [ ! -f "$ADB" ]; then
  echo "[ERROR] No se encuentra adb: $ADB"
  exit 1
fi
if [ ! -f "$RECOVERY_IMG" ]; then
  echo "[ERROR] No se encuentra OrangeFox: $RECOVERY_IMG"
  exit 1
fi
if [ ! -f "$PUB" ]; then
  echo "[ERROR] No se encuentra tu clave publica: $PUB"
  echo "        Genera una con: adb keygen ~/.android/adbkey"
  exit 1
fi

echo "[ok] Herramientas verificadas."
echo "     fastboot : $FB"
echo "     adb      : $ADB"
echo "     recovery : $RECOVERY_IMG"
echo "     pubkey   : $PUB"
echo ""

# --- Paso 0: Verificar que estamos en fastboot ---
echo "[Paso 0] Verificando modo Fastboot..."
fb_state=$("$FB" devices 2>/dev/null | grep "$SERIAL" | awk '{print $2}' || true)
if [ "$fb_state" = "fastboot" ]; then
  echo "[ok] Dispositivo en Fastboot."
else
  echo "[!] El telefono NO esta en Fastboot (estado: ${fb_state:-vacio})."
  echo "    Pon el telefono en Fastboot: Vol- + Power."
  echo "    Luego vuelve a ejecutar este script."
  exit 1
fi
echo ""

# --- Paso 1: Arrancar OrangeFox recovery en RAM ---
echo "[Paso 1] Arrancando OrangeFox recovery en RAM..."
"$FB" boot "$RECOVERY_IMG" 2>&1
echo "[ok] OrangeFox enviado al dispositivo."
echo ""

# Limpiar estado del servidor ADB antes de sondear
"$ADB" kill-server 2>/dev/null || true
"$ADB" start-server 2>/dev/null || true
echo ""

# --- Paso 2: Polling para detectar ADB en recovery ---
echo "[Paso 2] Esperando a que ADB de OrangeFox aparezca (max ${MAX_WAIT}s)..."
echo "    (Reinicia servidor ADB cada 20s para forzar re-deteccion)"
found=0
start_ts=$(date +%s)

while true; do
  now_ts=$(date +%s)
  elapsed=$(( now_ts - start_ts ))

  if [ $elapsed -ge $MAX_WAIT ]; then
    echo ""
    echo "[!] Tiempo agotado (${MAX_WAIT}s). OrangeFox no aparecio."
    echo "    Vuelve a Fastboot (Vol- + Power) y re-ejecuta."
    exit 2
  fi

  # Reiniciar ADB server periodicamente
  if [ $(( elapsed % 20 )) -eq 0 ] && [ $elapsed -gt 0 ]; then
    "$ADB" kill-server 2>/dev/null || true
    "$ADB" start-server 2>/dev/null || true
  fi

  raw=$("$ADB" devices 2>/dev/null || true)
  line=$(echo "$raw" | grep "$SERIAL" || true)
  transport=$(echo "$line" | awk '{print $2}')

  if [ -z "$transport" ]; then
    printf "\r    [%3ds] esperando...             " "$elapsed"
    sleep 3
    continue
  fi

  if [ "$transport" = "recovery" ]; then
    echo ""
    echo "[ok] ADB en estado 'recovery' (${elapsed}s)."
    found=1
    break
  elif [ "$transport" = "device" ]; then
    id_out=$("$ADB" -s "$SERIAL" shell id 2>&1 || true)
    if echo "$id_out" | grep -q "uid=0"; then
      echo ""
      echo "[ok] Root conseguido en estado 'device' (${elapsed}s)."
      found=1
      break
    fi
  elif [ "$transport" = "unauthorized" ]; then
    id_out=$("$ADB" -s "$SERIAL" shell id 2>&1 || true)
    if echo "$id_out" | grep -q "uid=0"; then
      echo ""
      echo "[ok] Root conseguido en estado 'unauthorized' (${elapsed}s)."
      found=1
      break
    fi
  fi

  printf "\r    [%3ds] estado: %-15s   " "$elapsed" "$transport"
  sleep 3
done

if [ "$found" -ne 1 ]; then
  echo "[FAIL] No se pudo obtener ADB con root."
  exit 3
fi
echo ""

# --- Paso 3: Verificar root ---
echo "[Paso 3] Verificando root..."
id_result=$("$ADB" -s "$SERIAL" shell id 2>&1)
echo "    $id_result"
if ! echo "$id_result" | grep -q "uid=0"; then
  echo "[ERROR] No tenemos root."
  exit 4
fi
echo "[ok] Root confirmado."
echo ""

# --- Paso 4: Inyectar clave ACTUAL en /data (sobrescribe, no append) ---
echo "[Paso 4] Inyectando clave publica actual en /data/misc/adb/adb_keys..."
"$ADB" -s "$SERIAL" shell 'mount /data 2>/dev/null; mkdir -p /data/misc/adb' || true
WIN_PUB="$(cygpath -w "$PUB" 2>/dev/null || echo "$PUB")"
"$ADB" -s "$SERIAL" push "$WIN_PUB" /data/local/tmp/mare_host_pubkey.txt
"$ADB" -s "$SERIAL" shell '
  cat /data/local/tmp/mare_host_pubkey.txt > /data/misc/adb/adb_keys
  rm -f /data/local/tmp/mare_host_pubkey.txt
  sort -u /data/misc/adb/adb_keys -o /data/misc/adb/adb_keys 2>/dev/null || true
  chown 1000:2000 /data/misc/adb/adb_keys 2>/dev/null || true
  chmod 0640 /data/misc/adb/adb_keys 2>/dev/null || true
  restorecon /data/misc/adb/adb_keys 2>/dev/null || true
  echo "--- Clave escrita:"
  cat /data/misc/adb/adb_keys
'
echo "[ok] Clave inyectada."
echo ""

# --- Paso 5: Reboot ---
echo "[Paso 5] Reiniciando a Android..."
"$ADB" -s "$SERIAL" reboot
echo "[ok] Reboot enviado."
echo ""

# --- Paso 6: Verificar autorizacion ---
echo "[Paso 6] Esperando que Android arranque y verificando ADB..."
"$ADB" kill-server 2>/dev/null || true
"$ADB" start-server 2>/dev/null || true

for i in $(seq 1 60); do
  sleep 3
  out=$("$ADB" devices 2>/dev/null | grep "$SERIAL" | awk '{print $2}')
  printf "\r    [%2ds] %-15s" "$((i*3))" "${out:-esperando}"
  if [ "$out" = "device" ]; then
    echo ""
    echo ""
    echo "============================================================"
    echo "  EXITO: $SERIAL = device (AUTORIZADO)"
    echo "  La clave queda guardada permanentemente."
    echo "  Ahora puedes lanzar USAR.cmd o JUGAR.cmd"
    echo "============================================================"
    exit 0
  fi
done

echo ""
echo "[!] Android no confirmo autorizacion en 3 minutos."
echo "    Ejecuta 'adb devices' para verificar manualmente."
exit 5
