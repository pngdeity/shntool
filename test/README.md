# shntool test suite

Four layers:

| Harness | Needs a reference? | Purpose |
|---|---|---|
| `test/unit/` (Unity) | no | Unit tests for pure helpers: endian conversion, bounded string copies, module helpers, WAVE header construction, and split-point parsing. |
| `test/smoke.py` | no | Runs core modes against generated fixtures and checks structural expectations. |
| `test/differential.py` | yes | Runs candidate and reference binaries over the same fixtures and compares exit code, stdout, stderr, and every produced file (SHA-256). |
| `test/fuzz/` (libFuzzer) | no | Coverage-guided fuzzing of the WAVE header parser, run for a bounded number of iterations as a regression test. |

Fixtures are generated deterministically by `test/tools/gen_fixtures.py` using
only the Python standard library, so they are independent of the program under
test and reproducible byte-for-byte.

The unit tests use [Unity](https://github.com/ThrowTheSwitch/Unity), pulled in
through the Meson wrap in `subprojects/unity.wrap`. The first configure needs
network access (or a populated `subprojects/packagecache/`).

## Running

```sh
meson setup build
meson test -C build
```

This runs the unit, smoke, and (when configured) differential tests. The
differential test runs only when `-Dreference-shntool=<path>` is set:

```sh
meson setup build -Dreference-shntool=/path/to/reference/shntool
meson test -C build --print-errorlogs
```

The harnesses can also be run directly:

```sh
build/test_convert
build/test_string
python3 test/smoke.py --binary build/shntool
python3 test/differential.py --candidate build/shntool \
                             --reference /path/to/reference/shntool
```

## Fuzzing

The WAVE header parser has a libFuzzer harness in `test/fuzz/fuzz_wave.c`.
Fuzzing needs a Clang toolchain and a dedicated build directory:

```sh
CC=clang meson setup build-fuzz -Dfuzz=true
meson compile -C build-fuzz
meson test -C build-fuzz fuzz-smoke          # bounded regression run
build-fuzz/fuzz_wave -max_len=4096 build-fuzz/corpus   # continuous fuzzing
```

Each object is built with `-fsanitize=fuzzer-no-link,address,undefined`; only
the `fuzz_wave` target links the libFuzzer runtime. `_FORTIFY_SOURCE` is
disabled in fuzz builds, and LeakSanitizer is disabled in the test environment
(this tree has known at-exit allocations); the sanitizers still abort on
overflow, use-after-free, and undefined behaviour.

## Building an upstream reference

The pristine 3.0.10 tree is preserved under the `upstream-3.0.10` tag. It does
not compile on modern compilers without the C23 fixes, so build it with the
GNU89 dialect:

```sh
git archive -o /tmp/upstream.tar upstream-3.0.10
mkdir -p /tmp/upstream && tar -xf /tmp/upstream.tar -C /tmp/upstream
cd /tmp/upstream
./configure CFLAGS="-g -O2 -std=gnu89"
make
```

## Adding cases

Append a `(name, argv)` tuple to `CASES` in `test/differential.py`. Cases must
be non-interactive: pass `-P none` to suppress progress output and prefer a
`-a`/`-z` output prefix so fixtures are never overwritten. Dependency-bearing
formats (flac, wavpack, ape, ...) are intentionally not part of the default
corpus, which uses only `wav` so it runs without external helper programs.
