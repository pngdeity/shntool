#!/usr/bin/env python3
"""Reference-free smoke tests for a built shntool binary.

These assertions do not require a reference binary; they check that core modes
run and produce structurally expected output. Use test/differential.py for
exact behavioral comparison against another build.

Usage:
    python3 test/smoke.py --binary build/shntool
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "tools"))
import gen_fixtures  # noqa: E402

TIMEOUT_SECONDS = 60
# 1 second of 44.1 kHz stereo 16-bit PCM plus a canonical 44-byte WAVE header.
ONE_SECOND_WAV_BYTES = 44100 * 2 * 2 + 44


def run(binary: Path, work: Path, argv: list[str]) -> subprocess.CompletedProcess:
    env = dict(os.environ, LC_ALL="C", LANG="C", TZ="UTC", TERM="dumb")
    return subprocess.run(
        [str(binary), *argv],
        cwd=work,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=TIMEOUT_SECONDS,
    )


class Failures:
    def __init__(self) -> None:
        self.items: list[str] = []

    def check(self, condition: bool, message: str) -> None:
        if not condition:
            self.items.append(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    args = parser.parse_args()

    binary = args.binary.resolve()
    if not binary.is_file():
        parser.error(f"binary not found: {binary}")

    failures = Failures()
    root = Path(tempfile.mkdtemp(prefix="shntool-smoke-"))
    work = root / "work"
    gen_fixtures.generate(work)

    version = run(binary, work, ["-v"])
    failures.check(version.returncode == 0, "version exit code")
    failures.check(
        b"shntool" in version.stdout + version.stderr,
        "version output mentions shntool",
    )

    generated = run(
        binary, work, ["gen", "-P", "none", "-l", "0:01", "-o", "wav", "one"]
    )
    failures.check(generated.returncode == 0, "gen exit code")
    wavs = sorted(work.glob("*.wav"))
    failures.check(bool(wavs), "gen produced a wav file")
    silence = next((p for p in wavs if p.stat().st_size == ONE_SECOND_WAV_BYTES), None)
    failures.check(silence is not None, "gen produced a one-second wav")

    if silence is not None:
        length = run(binary, work, ["len", "-P", "none", silence.name])
        failures.check(length.returncode == 0, "len exit code")
        failures.check(
            b"0:01.00" in length.stdout + length.stderr, "len reports 0:01.00"
        )

        md5 = run(binary, work, ["hash", "-P", "none", silence.name])
        failures.check(md5.returncode == 0, "hash exit code")
        failures.check(
            re.search(rb"\b[0-9a-f]{32}\b", md5.stdout + md5.stderr) is not None,
            "hash emits an MD5 digest",
        )

        sha1 = run(binary, work, ["hash", "-P", "none", "-s", silence.name])
        failures.check(
            re.search(rb"\b[0-9a-f]{40}\b", sha1.stdout + sha1.stderr) is not None,
            "hash -s emits a SHA1 digest",
        )

        catalogued = run(binary, work, ["cat", "-P", "none", silence.name])
        failures.check(catalogued.returncode == 0, "cat exit code")
        failures.check(catalogued.stdout.startswith(b"RIFF"), "cat emits RIFF data")

        before = {p.name for p in work.glob("*.wav")}
        split = run(
            binary,
            work,
            ["split", "-P", "none", "-l", "0:00.50", "-o", "wav", "album.wav"],
        )
        failures.check(split.returncode == 0, "split exit code")
        after = {p.name for p in work.glob("*.wav")} - before
        failures.check(len(after) >= 2, "split produced multiple tracks")

    identical = run(
        binary,
        work,
        ["cmp", "-P", "none", "stereo_16_44100_1s.wav", "stereo_16_44100_1s.wav"],
    )
    failures.check(identical.returncode == 0, "cmp exit code for identical files")

    for item in failures.items:
        print(f"FAIL: {item}")
    print(f"{len(failures.items)} failures")
    return 1 if failures.items else 0


if __name__ == "__main__":
    sys.exit(main())
