#!/usr/bin/env sh
# get_busybox.sh -- place a statically-linked aarch64 BusyBox at
# ramdisk/system/bin/busybox, the single binary MARE v0 boots on top of.
#
# Provenance is YOUR decision on purpose (MARE avoids silently pulling opaque
# blobs). Two supported paths:
#
#   (a) Trusted prebuilt -- supply a URL you vet, ideally with a checksum:
#         BUSYBOX_URL=https://…/busybox-aarch64 \
#         BUSYBOX_SHA256=<64-hex> scripts/get_busybox.sh
#
#   (b) Build from source (most transparent; Etapa D territory). Roughly:
#         git clone https://git.busybox.net/busybox && cd busybox
#         make defconfig
#         # set CONFIG_STATIC=y ; cross-compile with the Android NDK aarch64:
#         make CROSS_COMPILE=aarch64-linux-android- CONFIG_STATIC=y
#         cp busybox <MARE>/ramdisk/system/bin/busybox
#
# The result MUST be static (no runtime libs exist in MARE's rootfs) and aarch64.
set -eu

MARE_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
DEST_DIR="$MARE_ROOT/ramdisk/system/bin"
DEST="$DEST_DIR/busybox"

if [ -z "${BUSYBOX_URL:-}" ]; then
  echo "[MARE] BUSYBOX_URL is not set." >&2
  echo "[MARE] Provide a vetted static aarch64 busybox URL, e.g.:" >&2
  echo "         BUSYBOX_URL=https://…/busybox-aarch64 \\" >&2
  echo "         BUSYBOX_SHA256=<sha256> scripts/get_busybox.sh" >&2
  echo "[MARE] …or build from source (see the header of this script)." >&2
  exit 2
fi

mkdir -p "$DEST_DIR"
echo "[MARE] Downloading busybox from $BUSYBOX_URL"
if   command -v curl >/dev/null 2>&1; then curl -fL -o "$DEST" "$BUSYBOX_URL"
elif command -v wget >/dev/null 2>&1; then wget -O "$DEST" "$BUSYBOX_URL"
else echo "[MARE][ERROR] need curl or wget" >&2; exit 1; fi

if [ -n "${BUSYBOX_SHA256:-}" ]; then
  echo "[MARE] Verifying sha256"
  if command -v sha256sum >/dev/null 2>&1; then
    echo "$BUSYBOX_SHA256  $DEST" | sha256sum -c - \
      || { echo "[MARE][ERROR] checksum mismatch -- removing" >&2; rm -f "$DEST"; exit 1; }
  else
    echo "[MARE][WARN] sha256sum not found; skipping verification" >&2
  fi
else
  echo "[MARE][WARN] no BUSYBOX_SHA256 given; provenance unverified" >&2
fi

chmod 0755 "$DEST"

# Sanity: confirm it is a static aarch64 ELF, if `file` is available. We cannot
# execute an aarch64 binary on the x86 host, so inspection is the best we can do.
if command -v file >/dev/null 2>&1; then
  echo "[MARE] $(file -b "$DEST")"
  case "$(file -b "$DEST")" in
    *aarch64*statically*|*ARM\ aarch64*static*) : ;;
    *aarch64*) echo "[MARE][WARN] aarch64 but not detected as static -- verify CONFIG_STATIC" >&2 ;;
    *) echo "[MARE][WARN] does not look like an aarch64 ELF -- wrong arch?" >&2 ;;
  esac
fi

echo "[MARE] busybox ready at ${DEST#"$MARE_ROOT/"}"
