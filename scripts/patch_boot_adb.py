#!/usr/bin/env python3
"""
patch_boot_adb.py -- make a stock boot.img trust THIS host's adb key, so a
screen-dead device can authorize adb WITHOUT the on-screen RSA prompt.

Why this is the whole game: the only thing between us and seeing the screen on
the PC is a one-time adb authorization, and the RSA "Allow" dialog needs a screen
tap we cannot give. adbd trusts any pubkey listed in /adb_keys (read from the
rootfs, i.e. the boot ramdisk) even on a secure `user` build -- so we put ours
there.

Method: concatenated-initramfs overlay (format-agnostic, no decompression).
The Linux kernel unpacks MULTIPLE cpio archives concatenated in the ramdisk area,
each optionally compressed, skipping NUL padding between them, with files in
later archives overriding earlier ones. So instead of decompressing the stock
ramdisk (which may be gzip, xz, or the LZ4 *legacy* frame that stdlib cannot
handle), we leave it byte-for-byte untouched and append a tiny UNCOMPRESSED cpio
that contains just /adb_keys. This works regardless of the stock compression and
pulls in zero third-party libraries.

Reversible by design: the output is meant for `fastboot boot` (RAM only); nothing
is ever flashed. The stale AVB signature is stripped (an unlocked bootloader does
not verify it on `fastboot boot`, and unsigned is the cleanest input). Reuses the
MARE toolchain (bootimg + cpio); no new image logic.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "host"))
from mare import bootimg, cpio, compression   # noqa: E402


def build_adb_keys_overlay(pubkey_line):
    """A minimal uncompressed newc cpio carrying only /adb_keys (one pubkey per
    line, single trailing newline)."""
    ov = cpio.CpioArchive()
    ov.set_file("adb_keys", pubkey_line.strip() + b"\n", 0o644)
    return ov.to_bytes()


def patch_boot_adb(data, pubkey_line):
    """Take raw boot.img bytes + a host adb pubkey line; return (patched_bytes,
    evidence_dict). The stock ramdisk is preserved verbatim; our overlay is
    appended after 4-byte NUL padding (which the kernel skips between archives)."""
    img = bootimg.BootImage.from_bytes(data)
    stock = img.ramdisk
    comp = compression.detect(stock)
    overlay = build_adb_keys_overlay(pubkey_line)

    pad = (-len(stock)) % 4
    img.ramdisk = stock + (b"\x00" * pad) + overlay

    stripped = bool(img.signature)
    img.signature = b""
    ev = {
        "header_version": img.header_version,
        "stock_ramdisk_compression": comp,       # informational; not touched
        "stock_ramdisk_bytes": len(stock),
        "method": "append uncompressed /adb_keys cpio overlay (format-agnostic)",
        "overlay_bytes": len(overlay),
        "avb_signature": "stripped" if stripped else "none",
    }
    return img.to_bytes(), ev


def main(argv=None):
    ap = argparse.ArgumentParser(description="patch a boot.img to trust this host's adb key")
    ap.add_argument("boot_in", help="stock boot.img (from `dd` in recovery or the fastboot ROM)")
    ap.add_argument("-o", "--out", required=True, help="patched output image")
    ap.add_argument("--pubkey", default=os.path.expanduser("~/.android/adbkey.pub"),
                    help="host adb public key (default: ~/.android/adbkey.pub)")
    a = ap.parse_args(argv)

    with open(a.boot_in, "rb") as f:
        data = f.read()
    with open(a.pubkey, "rb") as f:
        pub = f.read()

    out, ev = patch_boot_adb(data, pub)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    with open(a.out, "wb") as f:
        f.write(out)

    print(f"[patch] input : {a.boot_in} ({len(data)} bytes)")
    print(f"[patch] pubkey: {a.pubkey}")
    for k, v in ev.items():
        print(f"[patch]   {k}: {v}")
    print(f"[patch] output: {a.out} ({len(out)} bytes)")
    print(f"[patch] next  : fastboot boot {a.out}   (RAM only; nothing is flashed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
