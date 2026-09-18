#!/usr/bin/env python3
"""Differential test harness for shntool.

Runs a candidate ``shntool`` binary and a reference binary over a fixed corpus
of deterministic fixtures and compares, for every case:

  * exit code
  * stdout bytes (normalized for the per-case working directory)
  * stderr bytes (same)
  * the set of resulting files and their SHA-256 digests

Because both binaries run in identical private working directories seeded with
the same fixtures, any difference is a behavioral change.

Usage:
    python3 test/differential.py --candidate build/shntool \
                                 --reference /path/to/reference/shntool
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "tools"))
import gen_fixtures  # noqa: E402

TIMEOUT_SECONDS = 60

# (name, argv). Commands that create files use distinct output prefixes so the
# fixtures themselves are never overwritten.
CASES: list[tuple[str, list[str]]] = [
    ("version", ["-v"]),
    ("help", ["-h"]),
    ("modes", ["-m"]),
    ("formats", ["-f"]),
    ("no_arguments", []),
    ("len_mono", ["len", "-P", "none", "mono_16_44100_1s.wav"]),
    ("len_stereo", ["len", "-P", "none", "stereo_16_44100_1s.wav"]),
    ("len_misaligned", ["len", "-P", "none", "stereo_16_44100_misaligned.wav"]),
    ("len_24bit", ["len", "-P", "none", "stereo_24_44100_1s.wav"]),
    ("len_8000hz", ["len", "-P", "none", "mono_16_8000_1s.wav"]),
    (
        "len_multiple",
        [
            "len",
            "-P",
            "none",
            "album.wav",
            "stereo_16_44100_1s.wav",
            "mono_16_44100_1s.wav",
        ],
    ),
    ("len_from_file", ["len", "-P", "none", "-F", "names.txt"]),
    ("len_missing_file", ["len", "-P", "none", "does_not_exist.wav"]),
    ("info_stereo", ["info", "-P", "none", "stereo_16_44100_1s.wav"]),
    ("hash_md5", ["hash", "-P", "none", "stereo_16_44100_1s.wav"]),
    ("hash_sha1", ["hash", "-P", "none", "-s", "stereo_16_44100_1s.wav"]),
    (
        "hash_composite",
        [
            "hash",
            "-P",
            "none",
            "-c",
            "stereo_16_44100_1s.wav",
            "stereo_16_44100_1s_tone.wav",
        ],
    ),
    (
        "cmp_identical",
        [
            "cmp",
            "-P",
            "none",
            "stereo_16_44100_1s.wav",
            "stereo_16_44100_1s.wav",
        ],
    ),
    (
        "cmp_different",
        [
            "cmp",
            "-P",
            "none",
            "stereo_16_44100_1s.wav",
            "stereo_16_44100_1s_tone.wav",
        ],
    ),
    ("gen_silence", ["gen", "-P", "none", "-l", "0:01", "-o", "wav", "-d", ".", "out"]),
    (
        "conv_wav",
        ["conv", "-P", "none", "-a", "conv_", "-o", "wav", "stereo_16_44100_1s.wav"],
    ),
    (
        "pad_end",
        ["pad", "-P", "none", "-a", "pad_", "stereo_16_44100_misaligned.wav"],
    ),
    (
        "strip",
        ["strip", "-P", "none", "-a", "strip_", "stereo_16_44100_1s.wav"],
    ),
    ("trim_tone", ["trim", "-P", "none", "-a", "trim_", "stereo_16_44100_1s_tone.wav"]),
    ("fix_check", ["fix", "-P", "none", "-c", "stereo_16_44100_misaligned.wav"]),
    ("cue_default", ["cue", "-P", "none", "album.wav"]),
    ("cue_split_points", ["cue", "-P", "none", "-s", "album.wav"]),
    ("split_cue", ["split", "-P", "none", "-f", "album.cue", "album.wav"]),
    ("split_cue_bom", ["split", "-P", "none", "-f", "album_bom.cue", "album.wav"]),
    ("split_cue_crlf", ["split", "-P", "none", "-f", "album_crlf.cue", "album.wav"]),
    (
        "split_by_length",
        ["split", "-P", "none", "-l", "0:01", "-o", "wav", "album.wav"],
    ),
    (
        "join",
        [
            "join",
            "-P",
            "none",
            "-a",
            "joined_",
            "-o",
            "wav",
            "stereo_16_44100_1s.wav",
            "tiny_stereo_16_44100.wav",
        ],
    ),
    ("cat_wav", ["cat", "-P", "none", "stereo_16_44100_1s.wav"]),
]


def snapshot(root: Path) -> dict[str, str]:
    """Return {relative path: sha256} for every regular file under root."""
    result: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        result[str(path.relative_to(root))] = digest
    return result


def normalize(data: bytes, workdir: Path, binary: Path) -> bytes:
    for token in (str(workdir).encode(), str(binary).encode()):
        data = data.replace(token, b"<PATH>")
    return data


def run_case(
    binary: Path, argv: list[str], fixtures: Path
) -> tuple[int, bytes, bytes, dict[str, str], Path]:
    workdir = Path(tempfile.mkdtemp(prefix="shntool-diff-"))
    shutil.copytree(fixtures, workdir / "work")
    work = workdir / "work"
    env = dict(os.environ, LC_ALL="C", LANG="C", TZ="UTC", TERM="dumb")
    try:
        proc = subprocess.run(
            [str(binary), *argv],
            cwd=work,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=TIMEOUT_SECONDS,
        )
        return proc.returncode, proc.stdout, proc.stderr, snapshot(work), workdir
    except subprocess.TimeoutExpired as exc:
        return (
            -999,
            exc.stdout or b"",
            exc.stderr or b"",
            snapshot(work),
            workdir,
        )


def describe_files(ref: dict[str, str], cand: dict[str, str]) -> list[str]:
    problems = []
    for name in sorted(set(ref) | set(cand)):
        if name not in cand:
            problems.append(f"    only in reference: {name}")
        elif name not in ref:
            problems.append(f"    only in candidate: {name}")
        elif ref[name] != cand[name]:
            problems.append(f"    differs: {name}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--filter", default="", help="only run cases matching")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    for label, binary in (("candidate", args.candidate), ("reference", args.reference)):
        if not binary.is_file():
            parser.error(f"{label} binary not found: {binary}")

    args.candidate = args.candidate.resolve()
    args.reference = args.reference.resolve()

    fixtures_root = Path(tempfile.mkdtemp(prefix="shntool-fixtures-"))
    fixtures = fixtures_root / "fixtures"
    gen_fixtures.generate(fixtures)

    passed = 0
    failed: list[str] = []

    for name, argv in CASES:
        if args.filter and args.filter not in name:
            continue

        ref_rc, ref_out, ref_err, ref_files, ref_dir = run_case(
            args.reference, argv, fixtures
        )
        cand_rc, cand_out, cand_err, cand_files, cand_dir = run_case(
            args.candidate, argv, fixtures
        )

        problems: list[str] = []
        if ref_rc != cand_rc:
            problems.append(f"    exit code: reference={ref_rc} candidate={cand_rc}")

        ref_out_n = normalize(ref_out, ref_dir / "work", args.reference)
        cand_out_n = normalize(cand_out, cand_dir / "work", args.candidate)
        if ref_out_n != cand_out_n:
            problems.append("    stdout differs")

        ref_err_n = normalize(ref_err, ref_dir / "work", args.reference)
        cand_err_n = normalize(cand_err, cand_dir / "work", args.candidate)
        if ref_err_n != cand_err_n:
            problems.append("    stderr differs")

        problems.extend(describe_files(ref_files, cand_files))

        if problems:
            failed.append(name)
            print(f"FAIL {name}: {' '.join(argv)}")
            for line in problems:
                print(line)
            if args.verbose:
                print(f"    reference stdout: {ref_out_n!r}")
                print(f"    candidate stdout: {cand_out_n!r}")
                print(f"    reference stderr: {ref_err_n!r}")
                print(f"    candidate stderr: {cand_err_n!r}")
        else:
            passed += 1
            print(f"PASS {name}")

        shutil.rmtree(ref_dir, ignore_errors=True)
        shutil.rmtree(cand_dir, ignore_errors=True)

    shutil.rmtree(fixtures_root, ignore_errors=True)

    print()
    print(f"{passed} passed, {len(failed)} failed")
    if failed:
        print("failed cases: " + ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
