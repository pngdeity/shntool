# Security Policy

## Supported versions

The `main` branch and the latest 3.0.x release are supported with security
fixes.

## Reporting a vulnerability

Please do not open a public issue for security problems. Instead, email
**pngdeity@tutanota.com** with:

- a description of the issue and its impact,
- steps or a sample to reproduce it,
- the affected version or commit.

You can expect an acknowledgement within 7 days and a status update within 30
days. Please allow time for a fix and release before public disclosure.

## Scope

`shntool` parses untrusted audio files and CUE sheets and launches external
helper programs. Relevant classes of issues include:

- memory-safety bugs in file or CUE parsing (buffer overflows, use-after-free),
- command or path injection when invoking helpers or generating filenames,
- denial of service from malformed input.

Findings will be credited unless you prefer otherwise.
