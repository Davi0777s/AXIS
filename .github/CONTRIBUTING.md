# Contributing to AXIS

Thank you for your interest in contributing to AXIS, a laboratory instrument for Android device research.

## Scope

AXIS is a focused, single-purpose laboratory tool. Contributions that align with its research scope are welcome:

- Bug fixes with reproduction steps
- Documentation improvements (README, CHANGELOG, SECURITY)
- Test coverage for existing modules
- Performance optimizations with benchmarks

## Out of Scope

- New features outside the stated laboratory scope
- UI redesigns without prior discussion
- Support for additional platforms (Linux/macOS) — Windows only

## Process

1. Open an issue describing the change with rationale
2. Fork and create a feature branch
3. Ensure all 81 tests pass (`python -m unittest discover -s tests`)
4. Run `python -m compileall -q axis.py src`
5. Submit PR with clear description

## Security

See [SECURITY.md](../SECURITY.md) for vulnerability reporting.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.