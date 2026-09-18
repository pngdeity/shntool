#!/usr/bin/env python3
"""Bounded libFuzzer smoke run used by `meson test`.

Generates a tiny seed corpus of valid WAVE headers, then asks the fuzzer for a
fixed number of iterations. A nonzero exit status (a crash, a sanitizer report
or a timeout) fails the test.
"""

from __future__ import annotations

import argparse
import os
import struct
import subprocess
import sys
import tempfile


def wav_seed(rate: int, channels: int, bits: int, data: bytes) -> bytes:
    block_align = channels * bits // 8
    byte_rate = rate * block_align
    fmt = struct.pack("<HHIIHH", 1, channels, rate, byte_rate, block_align, bits)
    return (
        b"RIFF"
        + struct.pack("<I", 4 + 8 + len(fmt) + 8 + len(data))
        + b"WAVE"
        + b"fmt "
        + struct.pack("<I", len(fmt))
        + fmt
        + b"data"
        + struct.pack("<I", len(data))
        + data
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fuzzer", required=True, help="path to the fuzz binary")
    parser.add_argument("--runs", type=int, default=20000)
    parser.add_argument("--max-len", type=int, default=4096)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="shntool-fuzz-") as tmp:
        corpus = os.path.join(tmp, "corpus")
        os.makedirs(corpus)

        seeds = [
            wav_seed(44100, 2, 16, b"\x00" * 64),
            wav_seed(8000, 1, 8, b"\x00" * 16),
            wav_seed(48000, 2, 24, b"\x00" * 48),
        ]
        for index, seed in enumerate(seeds):
            with open(os.path.join(corpus, f"seed{index}.wav"), "wb") as handle:
                handle.write(seed)

        cue_seeds = [
            b'FILE "album.wav" WAVE\n'
            b"  TRACK 01 AUDIO\n"
            b'    TITLE "One"\n'
            b'    PERFORMER "A"\n'
            b"    INDEX 01 00:00:00\n",
            b"TRACK 01 AUDIO\nTITLE x\nPERFORMER y\nINDEX 01 00:00:00\n",
        ]
        for index, seed in enumerate(cue_seeds):
            with open(os.path.join(corpus, f"cue{index}.cue"), "wb") as handle:
                handle.write(seed)

        env = dict(os.environ)
        # Fuzz targets intentionally leave state behind on error paths, so leak
        # detection is disabled for the fuzzer process itself.
        env["ASAN_OPTIONS"] = "detect_leaks=0:halt_on_error=1:abort_on_error=1"
        env["UBSAN_OPTIONS"] = "halt_on_error=1:abort_on_error=1:print_stacktrace=1"

        command = [
            args.fuzzer,
            f"-runs={args.runs}",
            f"-max_len={args.max_len}",
            f"-artifact_prefix={tmp}{os.sep}",
            corpus,
        ]
        result = subprocess.run(command, env=env, check=False)

        # Meson interprets exit status 77 as "skipped", which would mask a
        # crash; map any failure to a plain nonzero status instead.
        return 0 if result.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
