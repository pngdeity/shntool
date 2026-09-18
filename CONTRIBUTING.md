# Contributing

## Prerequisites

- A C17 compiler (GCC or Clang).
- Meson >= 1.1 and Ninja. On Arch Linux install `meson`, or use
  `uv tool install meson`.
- Optional: `clang-format` and `clang-tidy` (LLVM) for style and analysis.

## Build and test

```sh
meson setup build
meson compile -C build
meson test -C build
```

The build treats warnings as errors by default. Disable that for exploratory
work with `-Dwerror=false`.

## Continuous integration

`.github/workflows/ci.yml` runs on pushes to `main` and on pull requests:

- `build-test` (GCC and Clang): builds a reference from the `upstream-3.0.10`
  tag and runs the unit, smoke, and differential tests against it.
- `fuzz` (Clang): sanitizer build with the bounded libFuzzer regression runs.
- `subset`: a reduced `-Dmodes=len,info -Dformats=wav` build and its unit tests.
- `lint`: REUSE compliance (required) and clang-format (advisory).

PRs are expected to keep the pipeline green.

## Style

- Formatting is enforced by clang-format using `.clang-format` (LLVM base,
  include sorting disabled). Run it before committing:

  ```sh
  clang-format -i include/*.h src/*.c
  ```

- Static analysis: `run-clang-tidy -p build`.
- Keep diffs focused and consistent with the surrounding code.

## Commits

- Commits must be signed: `git commit -S`.
- Keep formatting-only changes in their own commit.
- Use a short prefix where it helps: `build:`, `test:`, `docs:`, `fix:`,
  `style:`, `chore:`.

## Adding a mode or format module

1. Add `src/mode_<name>.c` or `src/format_<name>.c` implementing the module
   struct (see `doc/modules.howto`).
2. Register the source in the `mode_files` or `format_files` dictionary in
   `meson.build`.
3. Add coverage to the test suite.

## Tests

`meson test -C build` runs the Unity unit tests, the smoke test, and (when a
reference is configured) the differential oracle. Changes that affect behavior
should be reflected in `test/`. Prefer adding a differential case over editing
existing expectations; pure helpers belong in `test/unit/`.

For parser changes, also build and run the fuzzer:

```sh
CC=clang meson setup build-fuzz -Dfuzz=true
meson test -C build-fuzz
```

See `test/README.md` for the full test strategy.

## Reporting issues

For security issues, follow `SECURITY.md` instead of opening a public issue.
