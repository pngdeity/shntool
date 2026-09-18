# Changelog

All notable changes to this project are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Meson build system with `-Dmodes=` / `-Dformats=` module selection and a
  `./configure` compatibility shim.
- Differential test harness comparing behavior against a reference build,
  plus a reference-free smoke test.
- Governance documentation (README, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY)
  and REUSE licensing metadata.

### Changed

- The code builds cleanly with a C17 baseline under `-Wall -Wextra -Werror`,
  including fixes for modern (C23) compilers.
- `read_n_bytes`, `write_n_bytes`, and `write_padding` use unsigned byte
  counts.
- Applied clang-format (LLVM base).

### Removed

- Autotools build files, preserved in the `upstream-3.0.10` tag.

### Fixed

- Replaced all unbounded `strcpy`/`strcat` with bounded, always-terminating
  `st_strlcpy`/`st_strlcat`; overwriting moves now use `memmove`. Added a
  crash regression test for oversized CUE fields.
- Checked the remaining `strdup` result for allocation failure.
- Removed the unbounded `vsprintf` fallback; `vsnprintf` is guaranteed by the
  C17 baseline, so `st_vsnprintf` always bounds-checks its output.

## [3.0.10] - 2009-03-30

Upstream release by Jason Jordan. See `ChangeLog` for the full history.
