# AXIS — Android eXploration & Inspection Suite

Engineering laboratory on desktop software for Android device connectivity, diagnostics, recovery, and automation. This repository presents the project, its scope, and its deliverables. Source code is not published.

## Project Objective

AXIS is a complete laboratory project engineered from scratch: a Windows desktop application that inspects, diagnoses, and operates an Android device through ADB, Fastboot, and screen mirroring. It demonstrates end-to-end engineering: system integration with external toolchains, binary-level boot image analysis, reactive UIs, secure subprocess handling, and shipping a portable, self-installing product.

Fully offline. Operates on a single device at a time. Everything required to run the product is handled by its installer.

## Scope

- Device state diagnostics over ADB and Fastboot, including authorization recovery
- Boot image analysis: header and payload parsing of `boot.img` / `vendor_boot_b.img`
- System diagnostics: SELinux, fstab, props, root, storage, battery
- Recovery operations: WiFi SAE fix, credential removal, screen unlock
- Daily-use and gaming automations: screen mirroring, input mapping (UHID), Shizuku, performance tuning
- Real-time gaming tuner: stream resolution, frame rate, GPU and CPU power control
- Portable Windows executable, installed and provisioned by a self-contained installer

## Architecture Overview

Thin three-tier design:

- Presentation layer: Qt 6 desktop UI (dashboard, launchers, tuner, analyzer, doctor, recovery)
- Domain logic: device manager, script runner, recovery controllers, diagnostics
- Integration layer: ADB / Fastboot / scrcpy toolchains and a bash helper toolchain

Engineering decisions by design:

- The product carries its own adb/fastboot/scrcpy; host `PATH` is sanitized so foreign builds cannot interfere (port 5037 ownership)
- Helper scripts run with positional parameters only; no shell interpolation of untrusted input
- Device-provided strings are validated and rendered as plain text
- Recovery operations require explicit confirmation; destructive actions are gated
- Runtime configuration in a single editable file; logs in the OS temp directory
- Frozen-mode detection so the executable is fully self-contained

## Engineering Practices

- 77 automated tests across UI, runner, device layer, analyzer, recovery, and assets
- Dependency surface pinned to a single runtime library, audited clean at release
- Reproducible build: one-dir executable with bundled Qt platform plugins
- CI-grade hygiene: compile checks, full suite run, secret scan before publish

## Preview

Project visuals:

![Preview 1](docs/portada.png)
![Preview 2](docs/personalizacion.png)

Installation and usage are covered in the release notes.

## Download and Install

Windows 10/11 64-bit. No Python or source code required.

1. Open the Releases page: https://github.com/Davi0777s/AXIS/releases
2. Download `AXIS-Setup.exe` from the latest release.
3. Run it. The installer downloads the application runtime and the required toolchains (adb, fastboot, scrcpy) from their official sources, installs under `%LOCALAPPDATA%\Programs\AXIS`, and creates Start Menu and Desktop shortcuts.
4. Launch AXIS from the shortcut or the installer's final prompt.

Git for Windows is recommended for the helper toolchain.

## License and Disclaimer

MIT. Intended for research and education on devices you own.

AXIS is provided "as is", without warranty of any kind, express or implied. You assume full responsibility for every operation it performs, including credential removal, overlay installation, and flashing. In no event shall the author be liable for any claim, damage, or loss arising from its use. This repository and its releases are provided for learning and engineering-showcase purposes.