# shntool test suite

Two layers:

| Harness | Needs a reference? | Purpose |
|---|---|---|
| `test/smoke.py` | no | Runs core modes against generated fixtures and checks structural expectations. |
| `test/differential.py` | yes | Runs candidate and reference binaries over the same fixtures and compares exit code, stdout, stderr, and every produced file (SHA-256). |

Fixtures are generated deterministically by `test/tools/gen_fixtures.py` using
only the Python standard library, so they are independent of the program under
test and reproducible byte-for-byte.

## Running

```sh
meson setup build
meson test -C build
```

The smoke test always runs. The differential test runs only when
`-Dreference-shntool=<path>` is set:

```sh
meson setup build -Dreference-shntool=/path/to/reference/shntool
meson test -C build --print-errorlogs
```

Either harness can also be run directly:

```sh
python3 test/smoke.py --binary build/shntool
python3 test/differential.py --candidate build/shntool \
                             --reference /path/to/reference/shntool
```

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
