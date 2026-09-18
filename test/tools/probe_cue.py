#!/usr/bin/env python3
"""Probe shntool's CUE-sheet handling and report observed behavior.

This is a research tool, not a pass/fail test. It feeds a fixed set of CUE
sheets to ``split`` and records, for each construct, how the parser responded:
whether split points were produced, how many output files appeared, and any
diagnostic. The output backs ``doc/cue-conformance.md``.

Fixtures come from ``gen_fixtures.py`` so the probe is self-contained.

Examples:
    test/tools/probe_cue.py
    test/tools/probe_cue.py --shntool build-fuzz/shntool --json
    test/tools/probe_cue.py --work /tmp/cueprobe --keep
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# name -> (cue sheet text, input fixture)
CASES: dict[str, tuple[str, str]] = {
    "baseline_3track": (
        'FILE "album.wav" WAVE\n'
        '  TRACK 01 AUDIO\n    TITLE "First"\n    PERFORMER "Artist"\n'
        "    INDEX 01 00:00:00\n"
        '  TRACK 02 AUDIO\n    TITLE "Second"\n    PERFORMER "Artist"\n'
        "    INDEX 01 00:01:00\n"
        '  TRACK 03 AUDIO\n    TITLE "Third"\n    PERFORMER "Artist"\n'
        "    INDEX 01 00:02:00\n",
        "album.wav",
    ),
    "index00_present": (
        'FILE "album.wav" WAVE\n'
        '  TRACK 01 AUDIO\n    TITLE "First"\n    INDEX 01 00:00:00\n'
        '  TRACK 02 AUDIO\n    TITLE "Second"\n    INDEX 00 00:00:30\n'
        "    INDEX 01 00:01:00\n"
        '  TRACK 03 AUDIO\n    TITLE "Third"\n    INDEX 01 00:02:00\n',
        "album.wav",
    ),
    "hidden_track1_nonzero": (
        'FILE "album.wav" WAVE\n'
        '  TRACK 01 AUDIO\n    TITLE "Hidden"\n    INDEX 01 00:00:30\n'
        '  TRACK 02 AUDIO\n    TITLE "Second"\n    INDEX 01 00:01:00\n'
        '  TRACK 03 AUDIO\n    TITLE "Third"\n    INDEX 01 00:02:00\n',
        "album.wav",
    ),
    "multifile": (
        'FILE "disc1.wav" WAVE\n'
        '  TRACK 01 AUDIO\n    TITLE "A"\n    INDEX 01 00:00:00\n'
        '  TRACK 02 AUDIO\n    TITLE "B"\n    INDEX 01 00:01:00\n'
        'FILE "disc2.wav" WAVE\n'
        '  TRACK 03 AUDIO\n    TITLE "C"\n    INDEX 01 00:02:00\n',
        "album.wav",
    ),
    "mismatched_file_name": (
        'FILE "completely-different-name.flac" WAVE\n'
        '  TRACK 01 AUDIO\n    TITLE "First"\n    INDEX 01 00:00:00\n'
        '  TRACK 02 AUDIO\n    TITLE "Second"\n    INDEX 01 00:01:00\n'
        '  TRACK 03 AUDIO\n    TITLE "Third"\n    INDEX 01 00:02:00\n',
        "album.wav",
    ),
    "no_file_line_starts_track": (
        '  TRACK 01 AUDIO\n    TITLE "First"\n    INDEX 01 00:00:00\n'
        '  TRACK 02 AUDIO\n    TITLE "Second"\n    INDEX 01 00:01:00\n',
        "album.wav",
    ),
    "blank_first_line": (
        "\n"
        'FILE "album.wav" WAVE\n'
        '  TRACK 01 AUDIO\n    TITLE "First"\n    INDEX 01 00:00:00\n'
        '  TRACK 02 AUDIO\n    TITLE "Second"\n    INDEX 01 00:01:00\n'
        '  TRACK 03 AUDIO\n    TITLE "Third"\n    INDEX 01 00:02:00\n',
        "album.wav",
    ),
    "cdtext_and_rem": (
        'REM COMMENT "made by a ripper"\n'
        'FILE "album.wav" WAVE\n'
        '  TRACK 01 AUDIO\n    SONGWRITER "X"\n    ISRC ABCDE1234567\n'
        '    TITLE "First"\n    INDEX 01 00:00:00\n'
        '  TRACK 02 AUDIO\n    GENRE Rock\n    TITLE "Second"\n'
        "    INDEX 01 00:01:00\n"
        '  TRACK 03 AUDIO\n    TITLE "Third"\n    INDEX 01 00:02:00\n',
        "album.wav",
    ),
    "noncd_input": (
        'FILE "mono_16_8000_1s.wav" WAVE\n'
        '  TRACK 01 AUDIO\n    TITLE "First"\n    INDEX 01 00:00:00\n'
        '  TRACK 02 AUDIO\n    TITLE "Second"\n    INDEX 01 00:00:30\n',
        "mono_16_8000_1s.wav",
    ),
    "duplicate_split_point": (
        'FILE "album.wav" WAVE\n'
        '  TRACK 01 AUDIO\n    TITLE "First"\n    INDEX 01 00:00:00\n'
        '  TRACK 02 AUDIO\n    TITLE "Second"\n    INDEX 01 00:01:00\n'
        '  TRACK 03 AUDIO\n    TITLE "Third"\n    INDEX 01 00:01:00\n',
        "album.wav",
    ),
    "split_point_beyond_eof": (
        'FILE "album.wav" WAVE\n'
        '  TRACK 01 AUDIO\n    TITLE "First"\n    INDEX 01 00:05:00\n'
        '  TRACK 02 AUDIO\n    TITLE "Second"\n    INDEX 01 00:06:00\n',
        "album.wav",
    ),
}


def find_shntool(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    for candidate in ("build/shntool", "build-final/shntool", "build-fuzz/shntool"):
        path = REPO_ROOT / candidate
        if path.exists():
            return path
    raise SystemExit("no shntool binary found; pass --shntool PATH")


def run_case(
    shntool: Path, root: Path, fixtures: Path, name: str, cue: str, input_name: str
) -> dict:
    outdir = root / "out" / name
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True)
    (outdir / "in.cue").write_text(cue, encoding="utf-8")

    proc = subprocess.run(
        [
            str(shntool),
            "split",
            "-P",
            "none",
            "-a",
            "tk_",
            "-f",
            "in.cue",
            str(fixtures / input_name),
        ],
        cwd=outdir,
        capture_output=True,
        text=True,
    )
    products = sorted(p.name for p in outdir.iterdir() if p.name != "in.cue")
    return {
        "case": name,
        "returncode": proc.returncode,
        "outputs": products,
        "stderr": [line.strip() for line in proc.stderr.splitlines() if line.strip()],
        "stdout": [line.strip() for line in proc.stdout.splitlines() if line.strip()],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shntool", help="path to the shntool binary under test")
    parser.add_argument("--work", help="working directory (default: a temp dir)")
    parser.add_argument("--keep", action="store_true", help="keep the work dir")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()

    shntool = find_shntool(args.shntool)
    root = (
        Path(args.work) if args.work else Path(tempfile.mkdtemp(prefix="shntool-cue-"))
    )
    fixtures = root / "fixtures"
    fixtures.mkdir(parents=True, exist_ok=True)

    import gen_fixtures  # same directory

    gen_fixtures.generate(fixtures)

    results = [
        run_case(shntool, root, fixtures, name, cue, input_name)
        for name, (cue, input_name) in CASES.items()
    ]

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for result in results:
            print(f"CASE {result['case']}")
            print(
                f"  rc={result['returncode']} "
                f"nfiles={len(result['outputs'])} files={result['outputs']}"
            )
            for line in result["stderr"]:
                print(f"  stderr: {line[:200]}")
            for line in result["stdout"]:
                print(f"  stdout: {line[:200]}")
            print()

    if not args.keep:
        shutil.rmtree(root, ignore_errors=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
