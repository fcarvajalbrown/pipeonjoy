# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✓         |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Email **fcarvajalbrown@gmail.com** with:
- A description of the vulnerability
- Steps to reproduce
- Potential impact

You will receive a response within 72 hours. If confirmed, a patch will be released and you will be credited in the changelog unless you prefer anonymity.

## Scope

pipeonjoy is a fully offline desktop application. It makes no network calls at runtime and stores no user data outside the local `outputs/` directory. The primary attack surface is malformed input files (MIDI, WAV, SF2 soundfonts) passed to third-party libraries (FluidSynth, pydub).
