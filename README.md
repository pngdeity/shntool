# shntool

`shntool` is a multi-purpose WAVE data processing and reporting utility,
originally written by Jason Jordan. This repository is a modernization of the
final upstream release, **3.0.10 (2009-03-30)**, preserving the command-line
interface and observable behavior while replacing the build system and
enforcing a modern quality bar.

## Status

Modernization in progress. The build has migrated from autotools to Meson, the
code compiles cleanly with a C17 baseline under `-Wall -Wextra -Werror`, and a
differential test suite verifies behavior against the pristine upstream build.
The pristine sources are preserved under the `upstream-3.0.10` tag.

## Features

Modes:

    len fix hash pad join split cat cmp cue conv info strip gen trim

Formats:

    wav aiff shn flac ape alac tak ofr tta als wv lpac la mkw bonk kxs cust term null

Most compressed formats are handled by delegating to external helper programs
(`flac`, `wvunpack`, `mac`, `shorten`, ...). Install the helpers you need and
make sure they are on `PATH`.

## Building

Requirements:

- a C17 compiler (GCC or Clang)
- Meson >= 1.1 and Ninja

```sh
meson setup build
meson compile -C build
meson install -C build
```

Mode and format modules can be selected at configure time:

```sh
meson setup build -Dmodes=len,info -Dformats=wav,flac
```

A compatibility wrapper reproduces the historical `./configure` interface:

```sh
./configure --prefix=/usr/local --with-formats=wav,flac
meson compile -C build
```

## Testing

```sh
meson test -C build
```

This runs the Unity unit tests plus a reference-free smoke test. To compare
byte-for-byte against another build, point the build at a reference binary:

```sh
meson setup build -Dreference-shntool=/path/to/reference/shntool
meson test -C build
```

Coverage-guided fuzzing of the WAVE header parser is available as an opt-in
Clang build:

```sh
CC=clang meson setup build-fuzz -Dfuzz=true
meson test -C build-fuzz
```

See `test/README.md` for details.

## Usage

```sh
shntool -h
shntool len file.wav
shntool split -f album.cue album.wav
```

Mode aliases (`shnlen`, `shnsplit`, ...) are installed alongside the binary.

## Design notes

- `doc/adr/` records architecture decisions. See
  `doc/adr/0001-preserve-upstream-architecture.md`.
- `doc/cue-conformance.md` documents how CUE-sheet constructs are handled by
  `split`, including the intentionally unsupported ones.

## Contributing

See `CONTRIBUTING.md`. Commits must be signed.

## License

GPL-2.0-or-later. See `COPYING`.
