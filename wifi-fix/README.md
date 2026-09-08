# WiFi fix — desactivar auto-upgrade a WPA3-SAE (spes / crDroid)

## Problema
El spes (crDroid 11.1.0, kernel 4.19-NigeaSilver, chip WCN `wcnss 5.2.022.12B`) **no
conectaba a la red de casa `Yovani`** (SSIDs divididos 2.4/5G). Causa: el router está
en **transición WPA2/WPA3** (`[RSN-PSK+SAE-CCMP][MFPC]`); Android **auto-upgradea a
WPA3-SAE** y la autenticación SAE **falla** (`Authentication failure reason=2`) — bug
del firmware WiFi. WPA2-PSK funciona perfecto (probado con otros hotspots).

El framework re-fuerza SAE en cada operación de config; el único interruptor es el
recurso `com.android.wifi.resources:bool/config_wifiSaeUpgradeEnabled` (leído por
`WifiGlobals` al arrancar). No hay switch runtime que persista → **RRO**.

## Solución (permanente, 100% device-side)
Un **RRO estático** (`nosae-wpa3-disable.apk`) que pone `config_wifiSaeUpgradeEnabled=false`,
instalado en `/product/overlay/` (posible porque **AVB/verity está desactivado** en este
ROM → `/product` se remonta rw). Al arrancar, el sistema lo aplica → el framework deja de
forzar SAE → `Yovani` conecta por **WPA2-PSK**.

Verificado: `Yovani_2.4` IP 192.168.40.5, WPA2-PSK, ping 8.8.8.8 ~6ms, DNS OK.

## Archivos
- `nosae-wpa3-disable.apk` — el RRO firmado (target `com.android.wifi.resources`,
  overlayable `WifiCustomization`, `isStatic`).
- `AndroidManifest.xml`, `config.xml` — fuentes del overlay.
- `reinstall_wifi_sae_fix.sh` — reinstala el APK en `/product/overlay` + reboot y
  **verifica solo** que el overlay quedó activo (`config_wifiSaeUpgradeEnabled=false`).
  Autodetecta el serial y espera `sys.boot_completed`. Sólo hace falta si un OTA/reflash
  lo borra. Comprobación rápida sin tocar nada: `./reinstall_wifi_sae_fix.sh --verify-only`.

## Cómo se construyó (por si hay que rehacerlo)
Toolchain: Android build-tools r34 (`aapt2`, `apksigner`, `zipalign`) + JDK 17.
```
aapt2 compile --dir res -o compiled.zip
aapt2 link -o unsigned.apk --manifest AndroidManifest.xml -I framework-res.apk \
  --min-sdk-version 30 --target-sdk-version 34 compiled.zip
zipalign -f 4 unsigned.apk aligned.apk
keytool -genkeypair -keystore key.jks -alias rro -keyalg RSA -keysize 2048 \
  -validity 10000 -storepass android -keypass android -dname CN=lab-rro
java -jar apksigner.jar sign --ks key.jks --ks-pass pass:android --out nosae.apk aligned.apk
```
Verificar tras instalar+reboot:
`adb shell cmd overlay list | grep nosae`  → `[x] com.lab.nosae`
`adb shell cmd overlay lookup com.android.wifi.resources com.android.wifi.resources:bool/config_wifiSaeUpgradeEnabled` → `false`
