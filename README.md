# AXIS — Android eXploration & Inspection Suite

*by Davi0777s*

Laboratory software platform for Android device research: USB connectivity analysis, bootloader diagnostics, boot image analysis, system telemetry, and controlled device automation.

## Abstract

AXIS is an offline research instrument that interrogates an Android device over its USB transport using the ADB (Android Debug Bridge) and Fastboot (bootloader) protocols, augmented with screen mirroring (scrcpy), HID input injection (UHID), and privileged automation (Shizuku). It is engineered as a laboratory toolset for device characterization, boot-chain inspection, recovery procedures, and reproducible experiment automation on hardware under explicit operator authorization.

## Research & Experimental Capabilities

- **Transport-layer diagnostics** — ADB state machine (device / unauthorized / offline) with Fastboot bootloader fallback and credential-repair workflows
- **Boot image analysis** — structural parsing of Android boot images (`boot.img` / `vendor_boot.img`), header layout, ramdisk, DTB payload boundaries
- **System telemetry** — SELinux enforcement state, fstab mount table, build properties, root status, storage topology, battery and power subsystem readings
- **Execution & performance instrumentation** — cpufreq governor, thermal throttling state, GPU power levels, UI animation policy, refresh-rate (60/90/120 Hz) constraints, encoder resolution/FPS tuning for mirroring
- **Automation primitives** — UHID mouse/keyboard injection, Shizuku ADB privilege delegation, screen projection profiles (daily use / gaming)
- **Recovery toolchain** — WiFi SAE / enterprise network fix, lock-credential removal, screen unlock, RRO overlay registrations

## Architecture

Presentation layer: Qt 6 desktop interface (dashboard, diagnostics, analyzer, recovery, tuning). Domain layer: device manager, script runner, recovery controllers. Integration layer: ADB, Fastboot, scrcpy toolchains and an isolated helper set. Subprocesses run with sanitized environments and positional arguments; device-supplied strings are treated as untrusted input and rendered in plain text. Fully offline: no telemetry, no runtime network calls.

## Engineering Methodology

- 81 automated tests spanning UI, runner, device, analyzer, recovery, and assets
- Single pinned runtime dependency (PySide6); dependency audit clean at release
- Reproducible frozen build (one-dir PyInstaller with bundled Qt platform plugins); compile verification and secret scanning before publish

## Key Index Terms

Android Debug Bridge (ADB), Fastboot bootloader protocol, boot image forensics (`boot.img`, `vendor_boot.img`, ramdisk, DTB), SELinux enforcement, fstab mount table, build properties, Unified HID (UHID) input injection, Shizuku ADB privilege delegation, scrcpy projection and streaming encoder, GPU power levels, cpufreq governor, thermal throttling, refresh-rate (60/90/120 Hz), RRO overlay, USB device transport, Android device research, mobile security, system telemetry, recovery procedures, Android automation.

## Intended Use

Research, education, and engineering validation on devices you own and are authorized to modify. Operates on a single connected device.

## Download and Install

Windows 10/11 64-bit. No Python or source code required.

1. Open the Releases page: https://github.com/Davi0777s/AXIS-Android-Research/releases
2. Download `AXIS-Setup.exe` from the latest release.
3. Run it. The installer fetches the application runtime and the official toolchains (Android platform-tools, scrcpy) and configures the environment automatically.
4. Launch AXIS from the installer shortcut.

## License & Research Disclaimer

MIT. Binaries and toolchains are distributed from their official sources. See LICENSE.

AXIS is provided "as is", without warranty of any kind, express or implied. It is intended for experimentation on devices you own and are authorized to access. You are solely responsible for every operation performed, including credential removal, overlay installation, and flashing. The author accepts no liability for any damage, data loss, or unauthorized use resulting from the software.