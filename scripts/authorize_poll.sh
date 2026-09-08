#!/usr/bin/env bash
# authorize_poll.sh -- igual que authorize_via_recovery.sh pero usa POLLING
# en lugar de wait-for-recovery, que se bloquea cuando adbd aparece como
# "unauthorized" antes de llegar a "recovery".
# Referencia: memoria del proyecto 2026-07-31 linea 70:
#   "Don't use adb wait-for-recovery after a recovery boot — it hung;
#    poll adb devices with a timeout instead."
set -u
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
ADB="$ROOT/tools/platform-tools/adb.exe"
FB="$ROOT/tools/platform-tools/fastboot.exe"
SERIAL="${SERIAL:-cb0a4ce4}"
PUB="${PUB:-$HOME/.android/adbkey.pub}"
RECOVERY_IMG="$ROOT/firmware/stock/orangefox-recovery.img"
MAX_WAIT=180   # segundos maximos esperando a OrangeFox adbd

echo "======================================================"
echo " authorize_poll.sh — autorizacion robusta via recovery"
echo "======================================================"

# 1. Verificar que tengamos la clave publica
if [ ! -f "$PUB" ]; then
  echo "[ERROR] No encuentro la clave publica en: $PUB"
  echo "        Genera una con:  adb keygen ~/.android/adbkey"
  exit 1
fi
echo "[ok] Clave publica encontrada: $PUB"

# 2. Reiniciar al bootloader regular (por si estamos en fastbootd)
echo "[*] Reiniciando al bootloader..."
"$FB" reboot bootloader 2>&1 || true
sleep 5

# Esperar a que aparezca en fastboot
echo "[*] Esperando a fastboot..."
for i in $(seq 1 30); do
  state=$("$FB" devices 2>/dev/null | grep "$SERIAL" | awk '{print $2}')
  if [ "$state" = "fastboot" ]; then
    echo "[ok] Dispositivo en fastboot."
    break
  fi
  echo "    ... intento $i/30 ($state)"
  sleep 2
done

# 3. fastboot boot OrangeFox en RAM
echo "[*] Arrancando OrangeFox en RAM (fastboot boot)..."
"$FB" boot "$RECOVERY_IMG" 2>&1
echo "[*] OrangeFox enviado. Esperando que su adbd aparezca (max ${MAX_WAIT}s)..."
echo "    (NOTA: es no-deterministico; si no aparece en ${MAX_WAIT}s reintentaremos)"

# 4. POLLING en lugar de wait-for-recovery
found=0
start_ts=$(date +%s)
while true; do
  now_ts=$(date +%s)
  elapsed=$(( now_ts - start_ts ))
  if [ $elapsed -ge $MAX_WAIT ]; then
    echo "[!] Tiempo agotado (${MAX_WAIT}s). OrangeFox adbd no enumero."
    echo "    Intentando de nuevo automaticamente..."
    break
  fi

  # Reiniciar el servidor ADB periodicamente para forzar re-deteccion
  if [ $(( elapsed % 20 )) -eq 0 ] && [ $elapsed -gt 0 ]; then
    echo "    [adb] kill-server + start-server para re-detectar..."
    "$ADB" kill-server 2>/dev/null; "$ADB" start-server 2>/dev/null
  fi

  raw=$("$ADB" devices 2>/dev/null)
  # Buscamos el serial en cualquier estado (recovery, device, unauthorized)
  line=$(echo "$raw" | grep "$SERIAL" || true)
  transport=$(echo "$line" | awk '{print $2}')

  if [ -z "$transport" ]; then
    printf "\r    [%3ds] esperando... (adb devices vacio)    " "$elapsed"
    sleep 3
    continue
  fi

  if [ "$transport" = "recovery" ]; then
    echo ""
    echo "[OK] OrangeFox en estado 'recovery' (${elapsed}s). adbd activo!"
    found=1
    break
  elif [ "$transport" = "device" ]; then
    echo ""
    echo "[!] Dispositivo en estado 'device' (Android, no recovery) — ${elapsed}s"
    echo "    OrangeFox no se activo o ya rebooteo. Verificando si es recovery de OrangeFox..."
    # A veces reporta 'device' en lugar de 'recovery'
    id_out=$(MSYS_NO_PATHCONV=1 "$ADB" -s "$SERIAL" shell id 2>&1)
    if echo "$id_out" | grep -q "uid=0"; then
      echo "[OK] Tenemos root (uid=0) aunque reporta 'device'. Continuamos."
      found=1
      break
    else
      echo "[!] Es Android normal (sin root). OrangeFox ya rebooteo. Reintentando..."
      break
    fi
  elif [ "$transport" = "unauthorized" ]; then
    echo ""
    echo "[?] Estado 'unauthorized' (${elapsed}s). Puede ser OrangeFox iniciando o Android."
    # Intentar shell de todas formas — en OrangeFox a veces autoriza igualmente
    id_out=$(MSYS_NO_PATHCONV=1 "$ADB" -s "$SERIAL" shell id 2>&1 || true)
    if echo "$id_out" | grep -q "uid=0"; then
      echo "[OK] Shell con root conseguido (uid=0) en estado unauthorized!"
      found=1
      break
    fi
    echo "    Esperando que cambie de estado..."
    sleep 3
    continue
  else
    printf "\r    [%3ds] estado: %-20s   " "$elapsed" "$transport"
    sleep 3
    continue
  fi
done

if [ $found -ne 1 ]; then
  echo "[FAIL] No se pudo conectar al recovery. El proceso terminó sin inyectar la clave."
  echo "       Vuelve al fastboot (Vol- + Power) y ejecuta este script de nuevo."
  exit 2
fi

# 5. Verificar root
echo "[*] Verificando acceso root..."
id_result=$(MSYS_NO_PATHCONV=1 "$ADB" -s "$SERIAL" shell id 2>&1)
echo "    id: $id_result"
if ! echo "$id_result" | grep -q "uid=0"; then
  echo "[ERROR] No tenemos root. OrangeFox no es root o no es el recovery esperado."
  exit 3
fi

# 6. Montar /data y crear directorio
echo "[*] Preparando /data/misc/adb/ ..."
MSYS_NO_PATHCONV=1 "$ADB" -s "$SERIAL" shell 'mount /data 2>/dev/null; mkdir -p /data/misc/adb' || true

# 7. Inyectar la clave via STDIN (no adb push — Git Bash reescribe rutas)
echo "[*] Inyectando clave publica en /data/misc/adb/adb_keys ..."
{ cat "$PUB"; echo; } | MSYS_NO_PATHCONV=1 "$ADB" -s "$SERIAL" shell 'cat >> /data/misc/adb/adb_keys'

# 8. Corregir permisos y SELinux label (igual que la receta original)
MSYS_NO_PATHCONV=1 "$ADB" -s "$SERIAL" shell '
  sort -u /data/misc/adb/adb_keys -o /data/misc/adb/adb_keys 2>/dev/null || true
  chown 1000:2000 /data/misc/adb/adb_keys 2>/dev/null || true   # system:shell
  chmod 0640 /data/misc/adb/adb_keys 2>/dev/null || true
  restorecon /data/misc/adb/adb_keys 2>/dev/null || true        # u:object_r:adb_keys_file:s0
  echo "--- /data/misc/adb/adb_keys ahora:"
  cat /data/misc/adb/adb_keys
'

# 9. Reboot al sistema Android
echo "[*] Clave inyectada. Reiniciando a Android..."
MSYS_NO_PATHCONV=1 "$ADB" -s "$SERIAL" reboot

echo ""
echo "======================================================"
echo " Esperando que Android arranque (puede tardar 30-60s)."
echo " Cuando arranque, verifica con:  adb devices"
echo " Debe aparecer:  cb0a4ce4   device"
echo "======================================================"

# 10. Polling para confirmar que Android volvio autorizado
echo "[*] Polling hasta ver 'device' autorizado..."
for i in $(seq 1 60); do
  sleep 3
  out=$("$ADB" devices 2>/dev/null | grep "$SERIAL" | awk '{print $2}')
  echo "    [${i}] estado: ${out:-<no detectado>}"
  if [ "$out" = "device" ]; then
    echo ""
    echo "======================================================"
    echo " EXITO: cb0a4ce4 = device (AUTORIZADO)"
    echo " Ahora puedes lanzar USAR.cmd o JUGAR.cmd"
    echo "======================================================"
    exit 0
  fi
done
echo "[!] Android no aparecio como 'device' en 3 minutos."
echo "    Revisa 'adb devices' manualmente."
