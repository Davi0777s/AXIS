#!/usr/bin/env bash
# game_mode.sh — "modo rendimiento" SIN sobrecalentamiento para el spes (adb root, sin Magisk).
# El spes es 4 GB de RAM: los COLGONES en Free Fire eran por presión de memoria
# (swap 98% lleno, el low-memory-killer mata apps -> tirones). Eso se arregló.
# Los TIRONES que quedaban (2026-08-28) eran TÉRMICOS + DE CADENCIA, no de potencia:
#   - CPU "performance" x8 + GPU clavada a 1114MHz (min_pwrlevel=0) mantenían el SoC en
#     ~63°C, el techo de throttle (gpu-step=64°C, cpu-step~63°C) → el gobernador térmico
#     bajaba clocks en oleadas = tirón periódico. Ahora: CPU schedutil (rampa a demanda,
#     idlea sola) y GPU con margen para bajar (min_pwrlevel=n-1) + force_no_nap (sin el
#     micro-tirón del nap, SIN el calor de estar clavado al máximo).
#   - el display iba a 90Hz contra el juego a 60fps = latido de cadencia. Se fija el panel
#     a 60Hz (la pantalla está muerta, nadie lo nota; el SurfaceFlinger lo confirmó).
# Los ajustes de gobernador/GPU se pierden en cada reboot, por eso se reaplican aquí.
# scrcpy_game.sh lo llama solo.
#
# Uso:   ./scripts/game_mode.sh              (aplica todo y muestra RAM + térmicas)
#        GAME=com.dts.freefireth ./scripts/game_mode.sh   (renice a otro juego)
#        SERIAL=xxxxxxx ./scripts/game_mode.sh
set -euo pipefail
export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'
ROOT="$(cd -- "$(dirname -- "$0")/.." && pwd)"
ADB="$ROOT/tools/platform-tools/adb.exe"
GAME="${GAME:-com.dts.freefireth}"

if [ -n "${SERIAL:-}" ]; then SARGS=(-s "$SERIAL"); else
  mapfile -t DEVS < <("$ADB" devices | awk 'NR>1 && $2=="device"{print $1}')
  if [ "${#DEVS[@]}" -eq 1 ]; then SARGS=(-s "${DEVS[0]}")
  elif [ "${#DEVS[@]}" -eq 0 ]; then SARGS=()
  else echo "[!] Varios equipos. Fija SERIAL=<serial>"; exit 1; fi
fi
adbx() { "$ADB" "${SARGS[@]}" "$@"; }
adbx root >/dev/null 2>&1 || true; adbx wait-for-device

echo "[*] RAM antes:"; adbx shell 'cat /proc/meminfo | grep -iE "MemAvailable|SwapFree" | tr "\n" " "; echo'

# 1) libera RAM: mata procesos de fondo + caches
adbx shell 'am kill-all >/dev/null 2>&1; sync; echo 3 > /proc/sys/vm/drop_caches 2>/dev/null; echo 1 > /proc/sys/vm/compact_memory 2>/dev/null'

# 2) CPU -> schedutil (rampa a demanda, idlea sola). "performance" x8 = máx sostenido = 63°C
#    constante = el step-governor térmico baja clocks en oleadas = el tirón periódico restante.
adbx shell 'for c in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo schedutil > $c 2>/dev/null; done'

# 2b) DESBLOQUEO DEL TECHO TÉRMICO (verificado 2026-08-28 con top + cooling_devices).
#     FALLA CLAVE: los cooling_devices "thermal-cpufreq-*" arrancan PIDADOS (big en step 2/6
#     => scaling_max 1.766GHz en vez de los 2.4GHz disponibles; little 1.190 en vez de 1.9).
#     Así el juego nunca podía subir en los frames duros = tirón. Soltar cur_state=0 + subir
#     scaling_max_freq devuelve el 100% del rango y AGUANTA con 62°C (el límite real son
#     trip_points a 95-110°C, normal). Se re-mitiga solo si de verdad se calienta de más.
adbx shell 'for cd in /sys/class/thermal/cooling_device*; do
  t=$(cat $cd/type 2>/dev/null)
  case "$t" in
    thermal-cpufreq-*) id=${t#"thermal-cpufreq-"}; pol=/sys/devices/system/cpu/cpufreq/policy$id
      echo 0 > $cd/cur_state 2>/dev/null || true
      maxf=$(cat $pol/scaling_available_frequencies 2>/dev/null | tr " " "\n" | sort -n | tail -1)
      [ -n "$maxf" ] && echo $maxf > $pol/scaling_max_freq 2>/dev/null || true
      echo "[CPU] policy$id max=...$(cat $pol/scaling_max_freq 2>/dev/null) (disponible=$maxf)" ;;
  esac
done; true'

# 3) GPU (Adreno/kgsl): margen para idlear + sin micro-nap.
#    CLAVE VERIFICADA en el kernel 4.19 NigeaSilver: lo que de verdad fija el rango son
#    min_pwrlevel/max_pwrlevel (nivel mayor = menor frecuencia). Con ambos a 0 el GPU quedaba
#    clavado a 1114MHz 24/7 (fuente de calor). Rango correcto: min=n-1 (PODER bajar) y max=0
#    (poder subir). Governor msm-adreno-tz = rampa agresiva solo cuando hay carga 3D real.
#    force_no_nap / force_*_on evitan el nap de 10ms que causa micro-tirones al compositor.
adbx shell 'K=/sys/class/kgsl/kgsl-3d0; n=$(cat $K/num_pwrlevels 2>/dev/null); n=${n:-6}; echo $((n-1)) > $K/min_pwrlevel 2>/dev/null; echo 0 > $K/max_pwrlevel 2>/dev/null; for x in force_no_nap force_clk_on force_bus_on force_rail_on; do echo 1 > $K/$x 2>/dev/null; done; echo 0 > $K/bus_split 2>/dev/null; true'

# 3b) GPU -> SUELO DE FRECUENCIA (verificado 2026-08-28): con el governor tz el GPU se quedaba
#     a 785MHz con 75% de ocupación en escenas animadas (lobby/loading) => frames >16ms =>
#     el STREAM SE CONGELA hasta que la pantalla deja de moverse. Subir el suelo a 1025MHz
#     baja la ocupación a ~60% (margen de sobra) y el freeze desaparece. Térmicas OK (54-58°C).
#     Fíjalo con GPU_MIN=785 / 465 si quieres menos consumo. Se pierde en cada reboot.
GPU_MIN="${GPU_MIN:-1025}"
adbx shell "K=/sys/class/kgsl/kgsl-3d0; echo ${GPU_MIN}000000 > \$K/devfreq/min_freq 2>/dev/null; echo \"[GPU] suelo=\$(cat \$K/devfreq/min_freq)\""

# 4) display: fija el panel a 60Hz (cadencia 1:1 con el juego a 60fps; antes 90Hz vs 60 = beat).
adbx shell 'settings put global min_refresh_rate 60 2>/dev/null; settings put global peak_refresh_rate 60 2>/dev/null; settings put system min_refresh_rate 60 2>/dev/null; settings put system peak_refresh_rate 60 2>/dev/null; true'

# 5) menos thrashing de swap (el ROM lo trae en 200, el máximo)
adbx shell 'echo 30 > /proc/sys/vm/swappiness 2>/dev/null'

# 6) prioridad alta al juego si está corriendo
adbx shell "pid=\$(pidof $GAME 2>/dev/null); [ -n \"\$pid\" ] && for p in \$pid; do renice -n -10 -p \$p >/dev/null 2>&1; done; true"

# 7) quita animaciones de UI (menos trabajo del compositor en transiciones/solapas)
adbx shell 'settings put global window_animation_scale 0 2>/dev/null; settings put global transition_animation_scale 0 2>/dev/null; settings put global animator_duration_scale 0 2>/dev/null; true'

echo "[*] RAM después:"; adbx shell 'cat /proc/meminfo | grep -iE "MemAvailable|SwapFree" | tr "\n" " "; echo'
echo "[*] Térmicas (throttle ~64°C GPU / ~63°C CPU):"; adbx shell 'for z in /sys/class/thermal/thermal_zone*; do t=$(cat $z/type 2>/dev/null); case "$t" in gpu-step|gpu-usr|cpu-1-0-usr|hepta-cpu-max-step) printf "%s=%sC  " "$t" "$(cat $z/temp 2>/dev/null)";; esac; done; echo'
adbx shell 'K=/sys/class/kgsl/kgsl-3d0; echo "[GPU] min_pwr=$(cat $K/min_pwrlevel 2>/dev/null) max_pwr=$(cat $K/max_pwrlevel 2>/dev/null) gpuclk=$(cat $K/gpuclk 2>/dev/null)"'
echo "[OK] Modo rendimiento aplicado (CPU=schedutil+max desbloqueado, GPU=idle+sin nap, swap=30, refresh=60Hz)."