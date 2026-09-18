#!/usr/bin/env python3
"""Encode WAV fixtures into formats used by the differential suite.

Only formats whose external helper is present are produced. The files are
generated once and identical bytes are handed to both the candidate and the
reference binary, so helper nondeterminism cannot affect the comparison.

Formats and helpers:

    flac  -> flac
    ape   -> mac
    aiff  -> sox

Other formats shntool supports (shn, tta, ofr, ...) need helpers that are not
widely installed, and are intentionally omitted.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

# format -> (helper executable, command builder)
ENCODERS = {
    "flac": ("flac", lambda src, dst: ["flac", "-s", "-o", str(dst), str(src)]),
    "ape": ("mac", lambda src, dst: ["mac", str(src), str(dst), "-c2000"]),
    "aiff": ("sox", lambda src, dst: ["sox", str(src), str(dst)]),
}

# WAV stems in the fixture set worth encoding (all present after
# gen_fixtures.generate()).
STEMS = (
    "stereo_16_44100_1s",
    "mono_16_44100_1s",
    "stereo_16_44100_1s_tone",
    "tiny_stereo_16_44100",
    "album",
)


def available_formats() -> set[str]:
    """Return the formats whose helper is on PATH."""
    return {fmt for fmt, (tool, _) in ENCODERS.items() if shutil.which(tool)}


def generate(dest: Path) -> set[str]:
    """Encode the fixture WAVs into every available format.

    Returns the set of formats for which all encodes succeeded.
    """
    produced: set[str] = set()

    for fmt, (tool, build) in ENCODERS.items():
        if not shutil.which(tool):
            continue

        ok = True
        for stem in STEMS:
            src = dest / f"{stem}.wav"
            dst = dest / f"{stem}.{fmt}"
            if not src.is_file():
                continue

            if dst.exists():
                dst.unlink()

            try:
                result = subprocess.run(
                    build(src, dst),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=120,
                )
            except (OSError, subprocess.TimeoutExpired):
                ok = False
            else:
                if (
                    result.returncode != 0
                    or not dst.is_file()
                    or dst.stat().st_size == 0
                ):
                    ok = False

            if not ok and dst.exists():
                dst.unlink()

        if ok:
            produced.add(fmt)

    return produced
