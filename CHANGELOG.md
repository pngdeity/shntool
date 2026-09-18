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
- Unity unit-test suite covering endian conversion, bounded string helpers,
  module helpers, WAVE header construction, and split-point parsing.
- libFuzzer harnesses for the WAVE header parser, the ID3v2 tag detector and
  the CUE-sheet tokenizer, enabled with `-Dfuzz=true`.
- A clang-tidy static-analysis gate (`.clang-tidy`) and a CI job covering the
  Clang analyzer, with core/security/unix findings treated as errors.
- Differential coverage for encoded-format round-trips (`flac` and `ape` on the
  read and write paths, `aiff` on the read path), malformed options, missing
  inputs, ID3v2-prefixed files, and extra, trailing and odd-sized RIFF chunks.

### Changed

- The code builds cleanly with a C17 baseline under `-Wall -Wextra -Werror`,
  including fixes for modern (C23) compilers.
- `read_n_bytes`, `write_n_bytes`, and `write_padding` use unsigned byte
  counts.
- Applied clang-format (LLVM base).
- Core sources are built as a `shntool_core` static library so unit tests and
  fuzz targets can link without the program entry point.
- The `st_output`/`st_info`/`st_warning`/`st_error`/`st_help`/`st_debug*` and
  `st_snprintf` functions now carry `printf` format attributes.
- The sanitized test build now keeps LeakSanitizer enabled, so the test suite
  guards against memory leaks as well as overflows and undefined behaviour.
- `st_error` and `st_help` are declared `noreturn`, so a fatal-error call is
  known to terminate control flow.
- The differential harness waits for asynchronous output encoders to finish
  before comparing produced files.

### Removed

- Autotools build files, preserved in the `upstream-3.0.10` tag.

### Fixed

- Replaced all unbounded `strcpy`/`strcat` with bounded, always-terminating
  `st_strlcpy`/`st_strlcat`; overwriting moves now use `memmove`. Added a
  crash regression test for oversized CUE fields.
- Checked the remaining `strdup` result for allocation failure.
- Removed the unbounded `vsprintf` fallback; `vsnprintf` is guaranteed by the
  C17 baseline, so `st_vsnprintf` always bounds-checks its output.
- Fixed format-string bugs exposed by the new format attributes, including a
  swapped pair of arguments in a WAVE-chunk warning that dereferenced a bogus
  pointer, and several `%d`/`%s`/`%X` specifiers that did not match their
  argument types.
- Fixed signed left-shift undefined behaviour in `read_value_long` and the
  endian converters.
- Guarded division and modulo by zero on malformed WAVE headers
  (`rate` and `block_align`).
- Initialised `filename1`/`filename2` in `cmp` mode to silence a
  use-of-uninitialized-value path.
- Freed the `wave_info` allocated by `gen` and `join` modes, which leaked at
  exit.
- Guarded the trailing-quote test in `get_cue_field` against an empty field,
  which indexed one byte before the buffer.
- Clamped the CUE track counter to `SPLIT_MAX_PIECES` so a sheet with too many
  `TRACK` lines cannot index past the per-track arrays.
- Bounded the character-translation scan in `split` by the source string
  length, removing a potential out-of-bounds read on a full buffer.
- Guarded the internal filename cursor in `core_mode` against a negative index.

## [3.0.10] - 2009-03-30

Upstream release by Jason Jordan. See `ChangeLog` for the full history.
