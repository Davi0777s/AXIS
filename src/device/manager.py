"""High-level device manager — detects and tracks connected devices."""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Callable

from src.device.adb import AdbClient
from src.device.fastboot import FastbootClient

_SERIAL_RE = re.compile(r"^[A-Za-z0-9._:\-+]+$")
_IDENT_MAX = 64


def sanitize_serial(value: str) -> str:
    """Validate a device serial for use in env vars and shell arguments.

    A serial arrives from `adb devices` — i.e. from the connected (possibly
    hostile) USB device. Only allow a conservative token charset; anything
    else is rejected rather than silently rewritten, so MARE scripts can
    never see shell metacharacters interpolated from a device string.
    """
    value = value.strip()
    if not value or len(value) > _IDENT_MAX or not _SERIAL_RE.match(value):
        raise ValueError(f"Invalid device serial: {value!r}")
    return value


def _clean_ident(value: str, fallback: str = "") -> str:
    """Normalize a free-form device string (model/codename) for the UI."""
    value = value.strip()
    if not value or len(value) > _IDENT_MAX:
        return fallback
    return value


@dataclass(frozen=True, slots=True)
class DeviceInfo:
    serial: str
    model: str
    state: str  # "device" | "bootloader" | "recovery" | "offline" | "unauthorized"
    android_version: str = ""
    sdk_version: str = ""
    codename: str = ""
    connection: str = "usb"  # "usb" | "wifi"


@dataclass
class DeviceManager:
    """Detects connected Android devices and maintains their info."""

    adb: AdbClient = field(default_factory=AdbClient)
    fastboot: FastbootClient = field(default_factory=FastbootClient)
    current_device: DeviceInfo | None = None
    _listeners: list[Callable[[DeviceInfo | None], None]] = field(default_factory=list, repr=False)

    def add_listener(self, callback: Callable[[DeviceInfo | None], None]) -> None:
        self._listeners.append(callback)

    def notify(self) -> None:
        for cb in self._listeners:
            cb(self.current_device)

    def refresh(self) -> DeviceInfo | None:
        """Poll connected devices and update state.

        Preserves the real transport state (``unauthorized``, ``offline``,
        ``recovery``) instead of forcing ``"device"``; props are only queried
        on an authorized device because other states can't answer ``getprop``.
        """
        adb_devices = self.adb.get_devices()
        if adb_devices:
            dev = adb_devices[0]
            try:
                serial = sanitize_serial(dev["serial"])
            except ValueError:
                serial = sanitize_serial("device")  # never trust a broken serial
            state = dev.get("state", "device")

            if state == "device":
                adb = AdbClient(serial=serial)
                model = _clean_ident(adb.get_prop("ro.product.model"))
                android = _clean_ident(adb.get_prop("ro.build.version.release"))
                sdk = _clean_ident(adb.get_prop("ro.build.version.sdk"))
                codename = _clean_ident(adb.get_prop("ro.product.device"))
                self.current_device = DeviceInfo(
                    serial=serial,
                    model=model,
                    state="device",
                    android_version=android,
                    sdk_version=sdk,
                    codename=codename,
                )
            else:
                # Not authorized yet: keep the real state so the UI can react
                # (offer ADB authorization) instead of reporting a bogus device.
                self.current_device = DeviceInfo(
                    serial=serial,
                    model=_clean_ident(dev.get("device", "")),
                    state=state,
                )
        elif self.fastboot.is_available():
            self.current_device = DeviceInfo(
                serial="fastboot",
                model="",
                state="bootloader",
            )
        else:
            self.current_device = None

        self.notify()
        return self.current_device

    def is_connected(self) -> bool:
        return self.current_device is not None and self.current_device.state == "device"

    def is_authorization_blocked(self) -> bool:
        return self.current_device is not None and (
            self.current_device.state in ("unauthorized", "offline")
        )

    def shell(self, command: str) -> str:
        if not self.is_connected():
            raise RuntimeError("No device connected")
        result = self.adb.shell(command)
        return result.stdout