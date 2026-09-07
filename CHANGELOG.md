# Changelog

All notable changes to the AXIS engineering laboratory. Sorted newest first.

## [1.0.0] - 2026-09-07

### Added

- Laboratory platform release: Android Debug Bridge (ADB) and Fastboot device diagnostics
- Boot image analysis (`boot.img` / `vendor_boot.img`), ramdisk and DTB inspection
- System telemetry: SELinux enforcement, fstab mount table, build props, storage, battery
- Recovery procedures: WiFi SAE fix, lock-credential removal, screen unlock, RRO overlays
- Automation primitives: UHID input injection, Shizuku ADB privilege delegation, scrcpy projection
- Performance instrumentation: cpufreq governor, thermal state, GPU power, refresh-rate, encoder resolution/FPS
- Qt 6 desktop interface with state-aware dashboard and launchers
- Professional self-contained installer (AXIS-Setup.exe) that provisions the runtime and official toolchains
- 81 automated tests; single pinned runtime dependency; frozen one-dir build

### Security

- Offline operation (no telemetry, no runtime network calls)
- Sanitized subprocess environments; positional arguments only; untrusted device strings rendered as plain text
- Dependency audit clean at release; secret scanning before publish