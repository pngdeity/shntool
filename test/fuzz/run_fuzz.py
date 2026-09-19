#!/usr/bin/env python3
"""Run a libFuzzer target against a seeded corpus.

Used by `meson test` for a bounded regression run, and by the scheduled fuzzing
workflow for a wall-clock-budgeted run that captures the evolved corpus.

Every run starts from a few built-in structural seeds and, when ``--seeds`` is
given, the committed corpus for the target. Pass ``--output-corpus`` to copy the
resulting corpus (including newly discovered units) somewhere durable.
"""

from __future__ import annotations

import argparse
import os
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

TARGETS = ("fuzz_wave", "fuzz_id3v2", "fuzz_cue")


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


def riff_chunk(chunk_id: bytes, payload: bytes) -> bytes:
    chunk = chunk_id + struct.pack("<I", len(payload)) + payload
    if len(payload) % 2:
        chunk += b"\x00"
    return chunk


def wav_with_extra_chunk(rate: int, channels: int, bits: int, data: bytes) -> bytes:
    block_align = channels * bits // 8
    fmt = struct.pack(
        "<HHIIHH", 1, channels, rate, rate * block_align, block_align, bits
    )
    body = (
        riff_chunk(b"fmt ", fmt)
        + riff_chunk(b"JUNK", b"\x00" * 8)
        + riff_chunk(b"data", data)
    )
    return b"RIFF" + struct.pack("<I", 4 + len(body)) + b"WAVE" + body


def id3v2_tag(payload: bytes, minor: int = 4, flags: int = 0) -> bytes:
    size = len(payload)
    synchsafe = bytes(
        [(size >> 21) & 0x7F, (size >> 14) & 0x7F, (size >> 7) & 0x7F, size & 0x7F]
    )
    return b"ID3" + bytes([minor, 0, flags]) + synchsafe + payload


def seeds_for(target: str) -> dict[str, bytes]:
    canonical = wav_seed(44100, 2, 16, b"\x00" * 64)

    if target == "fuzz_wave":
        return {
            "canonical.wav": canonical,
            "empty_data.wav": wav_seed(44100, 2, 16, b""),
            "mono8.wav": wav_seed(8000, 1, 8, b"\x01" * 15),
            "extra_chunk.wav": wav_with_extra_chunk(44100, 2, 16, b"\x00" * 32),
            "truncated.wav": canonical[:20],
            "id3v2.wav": id3v2_tag(b"\x00" * 16) + canonical,
        }

    if target == "fuzz_id3v2":
        return {
            "v4.bin": id3v2_tag(b"\x00" * 32),
            "v3.bin": id3v2_tag(b"\x00" * 8, minor=3),
            "short.bin": b"ID3",
            "zeros.bin": b"\x00" * 16,
            "max_size.bin": b"ID3\x04\x00\x00\x7f\x7f\x7f\x7f",
        }

    if target == "fuzz_cue":
        return {
            "album.cue": (
                b'FILE "album.wav" WAVE\n'
                b"  TRACK 01 AUDIO\n"
                b'    TITLE "One"\n'
                b'    PERFORMER "A"\n'
                b"    INDEX 01 00:00:00\n"
                b"  TRACK 02 AUDIO\n"
                b'    TITLE "Two"\n'
                b"    INDEX 01 00:01:00\n"
            ),
            "minimal.cue": b"TRACK 01 AUDIO\nINDEX 01 00:00:00\n",
            "rem.cue": b'REM GENRE "Rock"\nFILE "a.wav" WAVE\n',
        }

    return {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fuzzer", help="path to the fuzz binary")
    parser.add_argument("--target", choices=TARGETS)
    parser.add_argument("--max-len", type=int, default=4096)
    parser.add_argument("--runs", type=int, default=20000)
    parser.add_argument("--max-total-time", type=int, default=0)
    parser.add_argument("--seeds", type=Path, action="append", default=[])
    parser.add_argument("--dictionary", type=Path)
    parser.add_argument("--emit-seeds", type=Path)
    parser.add_argument("--output-corpus", type=Path)
    args = parser.parse_args()

    target = args.target
    if target is None and args.fuzzer:
        target = os.path.basename(args.fuzzer)
    if target not in TARGETS:
        parser.error("--target is required when it cannot be inferred from --fuzzer")

    if args.emit_seeds:
        args.emit_seeds.mkdir(parents=True, exist_ok=True)
        for name, data in seeds_for(target).items():
            (args.emit_seeds / name).write_bytes(data)
        return 0

    if not args.fuzzer:
        parser.error("--fuzzer is required")

    with tempfile.TemporaryDirectory(prefix="shntool-fuzz-") as tmp:
        corpus = Path(tmp) / "corpus"
        corpus.mkdir()

        for name, data in seeds_for(target).items():
            (corpus / name).write_bytes(data)

        for seed_dir in args.seeds:
            if not seed_dir.is_dir():
                continue
            for path in sorted(seed_dir.iterdir()):
                if path.is_file():
                    shutil.copyfile(path, corpus / path.name)

        env = dict(os.environ)
        # Fuzz targets intentionally leave state behind on error paths, so leak
        # detection is disabled for the fuzzer process itself.
        env["ASAN_OPTIONS"] = "detect_leaks=0:halt_on_error=1:abort_on_error=1"
        env["UBSAN_OPTIONS"] = "halt_on_error=1:abort_on_error=1:print_stacktrace=1"

        command = [
            args.fuzzer,
            f"-max_len={args.max_len}",
            f"-artifact_prefix={tmp}{os.sep}",
        ]
        if args.max_total_time > 0:
            command.append(f"-max_total_time={args.max_total_time}")
        else:
            command.append(f"-runs={args.runs}")
        if args.dictionary:
            command.append(f"-dict={args.dictionary}")
        command.append(str(corpus))

        result = subprocess.run(command, env=env, check=False)

        if args.output_corpus:
            args.output_corpus.mkdir(parents=True, exist_ok=True)
            for path in corpus.iterdir():
                if path.is_file():
                    shutil.copyfile(path, args.output_corpus / path.name)

        # Meson interprets exit status 77 as "skipped", which would mask a
        # crash; map any failure to a plain nonzero status instead.
        return 0 if result.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
