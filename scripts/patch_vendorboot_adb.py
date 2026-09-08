#!/usr/bin/env python3
"""
patch_vendorboot_adb.py -- inject THIS host's adb pubkey as /adb_keys into a
vendor_boot image's vendor ramdisk, so adbd trusts us with no on-screen RSA
prompt.

Why vendor_boot (not boot): on spes, fastbootd allows `fetch` for vendor_boot but
NOT boot, so this is the authorization path that needs ZERO external firmware
download. The bootloader concatenates the vendor ramdisk into the initramfs, so
/adb_keys placed here lands in the rootfs where adbd reads vendor adb keys.

Method: same format-agnostic append-overlay as patch_boot_adb -- the stock vendor
ramdisk is kept BYTE-FOR-BYTE; we append an uncompressed /adb_keys cpio and only
bump the vendor_ramdisk_size field. The original header is preserved verbatim
except that one 4-byte field, minimizing the chance of a malformed header. dtb is
carried through untouched.

Install by FLASHING vendor_boot_<slot> (restorable: keep the fetched original).
Intended for an UNLOCKED bootloader, where a changed vendor_boot hash is non-fatal
(verifiedbootstate=orange).
"""
import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "host"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mare import vendorboot                      # noqa: E402
from patch_boot_adb import build_adb_keys_overlay  # noqa: E402

VENDOR_RAMDISK_SIZE_OFF = 24                     # <I> at offset 24 in the header


def _pad(buf, page):
    r = len(buf) % page
    if r:
        buf += b"\x00" * (page - r)
    return buf


def patch_vendorboot_adb(data, pubkey_line):
    vb = vendorboot.VendorBoot.from_bytes(data)
    if vb.header_version != 3:
        # spes is v3 (single vendor ramdisk, no ramdisk table). v4 carries a
        # ramdisk table whose entry sizes would have to be rewritten too; not
        # handled here on purpose to keep the header edit provably safe.
        raise SystemExit(f"only vendor_boot v3 is supported (got v{vb.header_version})")

    P = vb.page_size
    header = bytearray(data[:vb.header_size])
    overlay = build_adb_keys_overlay(pubkey_line)

    vr = vb.vendor_ramdisk
    pad = (-len(vr)) % 4                           # kernel skips NUL padding
    new_vr = vr + b"\x00" * pad + overlay
    struct.pack_into("<I", header, VENDOR_RAMDISK_SIZE_OFF, len(new_vr))

    out = bytearray()
    out += header;    _pad(out, P)
    out += new_vr;    _pad(out, P)
    out += vb.dtb;    _pad(out, P)

    ev = {
        "header_version": vb.header_version,
        "page_size": P,
        "vendor_ramdisk_before": len(vr),
        "vendor_ramdisk_after": len(new_vr),
        "overlay_bytes": len(overlay),
        "dtb_bytes": len(vb.dtb),
        "out_bytes": len(out),
    }
    return bytes(out), ev


def main(argv=None):
    ap = argparse.ArgumentParser(description="inject this host's adb key into a vendor_boot image")
    ap.add_argument("vendor_boot_in", help="stock vendor_boot image (e.g. from `fastboot fetch`)")
    ap.add_argument("-o", "--out", required=True, help="patched output image")
    ap.add_argument("--pubkey", default=os.path.expanduser("~/.android/adbkey.pub"),
                    help="host adb public key (default: ~/.android/adbkey.pub)")
    a = ap.parse_args(argv)

    with open(a.vendor_boot_in, "rb") as f:
        data = f.read()
    with open(a.pubkey, "rb") as f:
        pub = f.read()

    out, ev = patch_vendorboot_adb(data, pub)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    with open(a.out, "wb") as f:
        f.write(out)

    print(f"[vpatch] input : {a.vendor_boot_in} ({len(data)} bytes)")
    print(f"[vpatch] pubkey: {a.pubkey}")
    for k, v in ev.items():
        print(f"[vpatch]   {k}: {v}")
    print(f"[vpatch] output: {a.out} ({len(out)} bytes)")
    print(f"[vpatch] install (RESTORABLE): fastboot flash vendor_boot_b {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
