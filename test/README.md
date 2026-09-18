# shntool test suite

Four layers:

| Harness | Needs a reference? | Purpose |
|---|---|---|
| `test/unit/` (Unity) | no | Unit tests for pure helpers: endian conversion, bounded string copies, module helpers, WAVE header construction, and split-point parsing. |
| `test/smoke.py` | no | Runs core modes against generated fixtures and checks structural expectations. |
| `test/differential.py` | yes | Runs candidate and reference binaries over the same fixtures and compares exit code, stdout, stderr, and every produced file (SHA-256). Covers every mode, encoded-format round-trips, negative/error paths and RIFF edge cases. |
| `test/fuzz/` (libFuzzer) | no | Coverage-guided fuzzing of the WAVE header parser, the ID3v2 tag detector and the CUE-sheet tokenizer, run for a bounded number of iterations each as regression tests. |

Base fixtures are generated deterministically by `test/tools/gen_fixtures.py`
using only the Python standard library, so they are independent of the program
under test and reproducible byte-for-byte. `test/tools/make_format_fixtures.py`
additionally encodes them into `flac`, `ape` and `aiff` with the external
`flac`, `mac` and `sox` helpers; differential cases that need a helper skip
themselves when it is not installed.

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

libFuzzer harnesses live in `test/fuzz/`:

| Target | Entry point under test |
|---|---|
| `fuzz_wave` | `verify_wav_header_internal()` (RIFF/fmt/data chunk parsing) |
| `fuzz_id3v2` | `check_for_id3v2_tag()` (ID3v2 header validation and size parsing) |
| `fuzz_cue` | CUE-sheet tokenizer (`get_cue_keyword`/`get_cue_field`/`extract`) |

Fuzzing needs a Clang toolchain and a dedicated build directory:

```sh
CC=clang meson setup build-fuzz -Dfuzz=true
meson compile -C build-fuzz
meson test -C build-fuzz                      # bounded regression runs
build-fuzz/fuzz_cue -max_len=16384 build-fuzz/corpus   # continuous fuzzing
```

Each object is built with `-fsanitize=fuzzer-no-link,address,undefined` and
`-DST_FUZZ` (which exposes the CUE tokenizer hooks); only the fuzz targets link
the libFuzzer runtime. `_FORTIFY_SOURCE` is disabled in fuzz builds. The
sanitizers abort on overflow, use-after-free and undefined behaviour, and
LeakSanitizer reports lost allocations, so the sanitized test run also guards
against memory leaks. Leak detection is disabled only for the fuzzer process
itself, whose error paths intentionally abandon state.

## Static analysis

`clang-tidy` runs over the Meson compilation database with the checks selected
in `.clang-tidy`: the Clang static analyzer, with core, security and unix
findings treated as errors. It needs a `compile_commands.json`, which Meson
generates at configure time:

```sh
meson setup build
run-clang-tidy -p build
```

## Building an upstream reference

The pristine 3.0.10 tree is preserved under the `upstream-3.0.10` tag. It does
not compile on modern compilers without the C23 fixes, so build it with the
GNU89 dialect. CI does this automatically for every `build-test` job, so the
steps below are only needed locally:

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
`-a`/`-z` output prefix so fixtures are never overwritten.

Cases whose fixtures come from an external helper (flac, ape, aiff) are added
through the `_add(name, argv, format)` helper, which records the required
format in `CASE_REQUIRES`; the case is skipped when that helper is unavailable
instead of failing. The suite already covers read/write round-trips for each
encoded format, malformed options and missing inputs, and RIFF edge cases
(ID3v2-prefixed files, extra and trailing chunks, odd-sized data).

Because shntool does not wait for its output encoder subprocess (the unused
`close_and_wait()` in upstream), the harness only snapshots a working tree once
it has stopped changing (`stable_snapshot`). This keeps the comparison
deterministic without hiding behavioral differences.
