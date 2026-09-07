# Security Policy

## Scope

AXIS is a laboratory instrument for Android device research. It is designed to operate on devices you own and are authorized to access. Security-sensitive behaviors include automated ADB operations, boot image parsing, lock-credential removal, RRO overlay installation, and flashing-adjacent workflows.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x    | Yes       |

## Reporting a Vulnerability

Please report potential vulnerabilities privately by opening a GitHub issue with the "security" label and do not include device identifiers or credentials. Include:

- Affected version and module (device, analyzer, doctor, recovery, runner, GUI)
- Reproduction steps and minimal input
- Expected versus observed behavior

Disclosure will be acknowledged within 7 days. Fixes are released through the standard release channel (AXIS-Setup.exe) with a changelog entry.

## Design Guarantees

- No telemetry; no runtime network calls by the application
- Device-supplied strings are validated and rendered as plain text
- Helper toolchains run with sanitized environments and positional parameters (no shell interpolation of untrusted input)
- Recovery and destructive actions require explicit operator confirmation

Use of this software is solely at the operator's responsibility and must be limited to authorized devices.