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
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "tools"))
import gen_fixtures  # noqa: E402
import make_format_fixtures  # noqa: E402

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

# Cases that depend on an external helper. The value is the format that
# make_format_fixtures must have produced; if it is absent the case is skipped
# rather than failed.
CASE_REQUIRES: dict[str, str] = {}


def _add(name: str, argv: list[str], fmt: str = "") -> None:
    CASES.append((name, argv))
    if fmt:
        CASE_REQUIRES[name] = fmt


for _fmt in ("flac", "ape", "aiff"):
    _add(f"len_{_fmt}", ["len", "-P", "none", f"stereo_16_44100_1s.{_fmt}"], _fmt)
    _add(f"info_{_fmt}", ["info", "-P", "none", f"stereo_16_44100_1s.{_fmt}"], _fmt)
    _add(f"hash_{_fmt}", ["hash", "-P", "none", f"stereo_16_44100_1s.{_fmt}"], _fmt)
    _add(f"cat_{_fmt}", ["cat", "-P", "none", f"stereo_16_44100_1s.{_fmt}"], _fmt)
    _add(
        f"conv_{_fmt}_to_wav",
        [
            "conv",
            "-P",
            "none",
            "-a",
            f"conv_{_fmt}_",
            "-o",
            "wav",
            f"stereo_16_44100_1s.{_fmt}",
        ],
        _fmt,
    )
    _add(
        f"conv_wav_to_{_fmt}",
        [
            "conv",
            "-P",
            "none",
            "-a",
            f"to_{_fmt}_",
            "-o",
            _fmt,
            "stereo_16_44100_1s.wav",
        ],
        _fmt,
    )
    _add(
        f"split_{_fmt}",
        [
            "split",
            "-P",
            "none",
            "-a",
            f"split_{_fmt}_",
            "-f",
            "album.cue",
            f"album.{_fmt}",
        ],
        _fmt,
    )
    _add(
        f"join_{_fmt}",
        [
            "join",
            "-P",
            "none",
            "-a",
            f"join_{_fmt}_",
            "-o",
            "wav",
            f"stereo_16_44100_1s.{_fmt}",
            f"tiny_stereo_16_44100.{_fmt}",
        ],
        _fmt,
    )

# Negative, error-path, and RIFF-edge coverage. None of these need helpers.
for _name, _argv in (
    ("err_unknown_mode", ["frobnicate"]),
    ("err_unknown_option", ["-Z"]),
    (
        "err_unknown_input_format",
        ["conv", "-P", "none", "-i", "bogus", "-o", "wav", "stereo_16_44100_1s.wav"],
    ),
    (
        "err_missing_split_file",
        ["split", "-P", "none", "-f", "no_such.cue", "album.wav"],
    ),
    (
        "err_extract_track_zero",
        ["split", "-P", "none", "-x", "0", "-f", "album.cue", "album.wav"],
    ),
    (
        "err_extract_track_range",
        ["split", "-P", "none", "-x", "99", "-f", "album.cue", "album.wav"],
    ),
    ("err_bad_length", ["split", "-P", "none", "-l", "notalen", "album.wav"]),
    ("err_join_no_files", ["join", "-P", "none", "-o", "wav"]),
    ("err_missing_sha1_file", ["hash", "-P", "none", "-s", "does_not_exist.wav"]),
    (
        "err_output_dir_missing",
        [
            "conv",
            "-P",
            "none",
            "-d",
            "no_such_dir",
            "-a",
            "x_",
            "-o",
            "wav",
            "stereo_16_44100_1s.wav",
        ],
    ),
    ("id3v2_len", ["len", "-P", "none", "id3v2.wav"]),
    ("id3v2_info", ["info", "-P", "none", "id3v2.wav"]),
    ("id3v2_hash", ["hash", "-P", "none", "id3v2.wav"]),
    ("id3v2_conv", ["conv", "-P", "none", "-a", "id3_", "-o", "wav", "id3v2.wav"]),
    ("extra_chunk_len", ["len", "-P", "none", "extra_chunk.wav"]),
    ("extra_chunk_info", ["info", "-P", "none", "extra_chunk.wav"]),
    ("extra_chunk_hash", ["hash", "-P", "none", "extra_chunk.wav"]),
    ("extra_chunk_strip", ["strip", "-P", "none", "-a", "strip_", "extra_chunk.wav"]),
    ("extra_chunk_cat", ["cat", "-P", "none", "extra_chunk.wav"]),
    ("extra_chunk_cat_suppressed", ["cat", "-P", "none", "-c", "extra_chunk.wav"]),
    ("odd_chunk_len", ["len", "-P", "none", "odd_chunk.wav"]),
    ("odd_chunk_info", ["info", "-P", "none", "odd_chunk.wav"]),
    ("odd_chunk_strip", ["strip", "-P", "none", "-a", "strip_", "odd_chunk.wav"]),
    ("odd_data_len", ["len", "-P", "none", "odd_data.wav"]),
    ("odd_data_info", ["info", "-P", "none", "odd_data.wav"]),
    ("trailing_chunk_len", ["len", "-P", "none", "trailing_chunk.wav"]),
    ("trailing_chunk_info", ["info", "-P", "none", "trailing_chunk.wav"]),
    ("trailing_chunk_hash", ["hash", "-P", "none", "trailing_chunk.wav"]),
    (
        "trailing_chunk_strip",
        ["strip", "-P", "none", "-a", "strip_", "trailing_chunk.wav"],
    ),
    (
        "trailing_chunk_conv",
        ["conv", "-P", "none", "-a", "conv_", "-o", "wav", "trailing_chunk.wav"],
    ),
    ("trailing_chunk_cat", ["cat", "-P", "none", "trailing_chunk.wav"]),
    (
        "trailing_chunk_cat_suppressed",
        ["cat", "-P", "none", "-c", "trailing_chunk.wav"],
    ),
    ("hash_from_file", ["hash", "-P", "none", "-F", "names.txt"]),
):
    _add(_name, _argv)


def snapshot(root: Path) -> dict[str, str]:
    """Return {relative path: sha256} for every regular file under root."""
    result: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        result[str(path.relative_to(root))] = digest
    return result


def stable_snapshot(root: Path, timeout: float = 10.0) -> dict[str, str]:
    """Snapshot root repeatedly until two consecutive reads agree.

    shntool does not wait for its output encoder subprocess (see the unused
    close_and_wait() in upstream), so an encoded file may still be written when
    the process exits. Waiting for the tree to settle avoids reporting a race
    as a behavioral difference.
    """
    deadline = time.monotonic() + timeout
    previous = snapshot(root)

    while time.monotonic() < deadline:
        time.sleep(0.1)
        current = snapshot(root)
        if current == previous:
            return current
        previous = current

    return previous


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
        return (
            proc.returncode,
            proc.stdout,
            proc.stderr,
            stable_snapshot(work),
            workdir,
        )
    except subprocess.TimeoutExpired as exc:
        return (
            -999,
            exc.stdout or b"",
            exc.stderr or b"",
            stable_snapshot(work),
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
    available_formats = make_format_fixtures.generate(fixtures)

    passed = 0
    skipped: list[str] = []
    failed: list[str] = []

    for name, argv in CASES:
        if args.filter and args.filter not in name:
            continue

        required = CASE_REQUIRES.get(name)
        if required and required not in available_formats:
            skipped.append(name)
            print(f"SKIP {name} (missing helper for {required})")
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
    if skipped:
        print(f"{len(skipped)} skipped (missing helpers): " + ", ".join(skipped))
    print(f"{passed} passed, {len(failed)} failed")
    if failed:
        print("failed cases: " + ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
