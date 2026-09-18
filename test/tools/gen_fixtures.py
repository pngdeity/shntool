#!/usr/bin/env python3
"""Generate deterministic audio and CUE fixtures for the shntool test suite.

The fixtures are produced from the Python standard library only, so they are
independent of the program under test and byte-for-byte reproducible.
"""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

CD_RATE = 44100
SECTOR_SAMPLES = 588


def _write_pcm(
    path: Path, channels: int, sampwidth: int, rate: int, frames: list[bytes]
) -> None:
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(sampwidth)
        handle.setframerate(rate)
        handle.writeframes(b"".join(frames))


def _silence(channels: int, sampwidth: int, count: int) -> list[bytes]:
    frame = b"\x00" * (channels * sampwidth)
    return [frame] * count


def _tone(
    channels: int,
    sampwidth: int,
    rate: int,
    count: int,
    freq: float = 440.0,
    amplitude: float = 0.5,
) -> list[bytes]:
    peak = int((2 ** (8 * sampwidth - 1) - 1) * amplitude)
    frames: list[bytes] = []
    for index in range(count):
        value = int(peak * math.sin(2 * math.pi * freq * index / rate))
        if sampwidth == 1:
            sample = struct.pack("<B", value + 128)
        elif sampwidth == 2:
            sample = struct.pack("<h", value)
        elif sampwidth == 3:
            sample = value.to_bytes(3, "little", signed=True)
        else:
            raise ValueError(f"unsupported sample width: {sampwidth}")
        frames.append(sample * channels)
    return frames


def _riff_chunk(chunk_id: bytes, payload: bytes) -> bytes:
    chunk = chunk_id + struct.pack("<I", len(payload)) + payload
    if len(payload) % 2:
        chunk += b"\x00"
    return chunk


def _wav_bytes(channels: int, sampwidth: int, rate: int, frames: list[bytes]) -> bytes:
    data = b"".join(frames)
    block_align = channels * sampwidth
    fmt = struct.pack(
        "<HHIIHH", 1, channels, rate, rate * block_align, block_align, 8 * sampwidth
    )
    body = _riff_chunk(b"fmt ", fmt) + _riff_chunk(b"data", data)
    return b"RIFF" + struct.pack("<I", 4 + len(body)) + b"WAVE" + body


def _id3v2_tag(payload: bytes) -> bytes:
    size = len(payload)
    synchsafe = bytes(
        [(size >> 21) & 0x7F, (size >> 14) & 0x7F, (size >> 7) & 0x7F, size & 0x7F]
    )
    return b"ID3\x04\x00\x00" + synchsafe + payload


_CUE_TRACKS = (
    (1, "First", "00:00:00"),
    (2, "Second", "00:01:00"),
    (3, "Third", "00:02:00"),
)


def _cue_sheet() -> str:
    lines = ['FILE "album.wav" WAVE']
    for number, title, index in _CUE_TRACKS:
        lines.append(f"  TRACK {number:02d} AUDIO")
        lines.append(f'    TITLE "{title}"')
        lines.append('    PERFORMER "Artist"')
        lines.append(f"    INDEX 01 {index}")
    return "\n".join(lines) + "\n"


def generate(dest: Path) -> None:
    """Populate ``dest`` with all fixtures (idempotent)."""
    dest.mkdir(parents=True, exist_ok=True)

    _write_pcm(dest / "mono_16_44100_1s.wav", 1, 2, CD_RATE, _silence(1, 2, CD_RATE))
    _write_pcm(dest / "stereo_16_44100_1s.wav", 2, 2, CD_RATE, _silence(2, 2, CD_RATE))
    _write_pcm(
        dest / "stereo_16_44100_1s_tone.wav",
        2,
        2,
        CD_RATE,
        _tone(2, 2, CD_RATE, CD_RATE),
    )
    _write_pcm(
        dest / "stereo_16_44100_misaligned.wav",
        2,
        2,
        CD_RATE,
        _silence(2, 2, CD_RATE + 100),
    )
    _write_pcm(dest / "stereo_24_44100_1s.wav", 2, 3, CD_RATE, _silence(2, 3, CD_RATE))
    _write_pcm(dest / "mono_16_8000_1s.wav", 1, 2, 8000, _silence(1, 2, 8000))
    _write_pcm(
        dest / "tiny_stereo_16_44100.wav",
        2,
        2,
        CD_RATE,
        _silence(2, 2, SECTOR_SAMPLES),
    )
    _write_pcm(dest / "album.wav", 2, 2, CD_RATE, _silence(2, 2, CD_RATE * 3))

    cue = _cue_sheet()
    (dest / "album.cue").write_text(cue, encoding="utf-8")
    (dest / "album_bom.cue").write_bytes(b"\xef\xbb\xbf" + cue.encode("utf-8"))
    (dest / "album_crlf.cue").write_bytes(cue.replace("\n", "\r\n").encode("utf-8"))
    (dest / "names.txt").write_text(
        "stereo_16_44100_1s.wav\nmono_16_44100_1s.wav\n", encoding="utf-8"
    )

    # ID3v2-prefixed WAV (tests the tag-skipping path).
    canonical = _wav_bytes(2, 2, CD_RATE, _silence(2, 2, CD_RATE))
    (dest / "id3v2.wav").write_bytes(_id3v2_tag(b"\x00" * 128) + canonical)

    block_align = 2 * 2
    fmt = struct.pack("<HHIIHH", 1, 2, CD_RATE, CD_RATE * block_align, block_align, 16)

    # An even-sized extra chunk between fmt and data.
    extra_body = (
        _riff_chunk(b"fmt ", fmt)
        + _riff_chunk(b"JUNK", b"\x00" * 8)
        + _riff_chunk(b"data", b"".join(_silence(2, 2, CD_RATE)))
    )
    (dest / "extra_chunk.wav").write_bytes(
        b"RIFF" + struct.pack("<I", 4 + len(extra_body)) + b"WAVE" + extra_body
    )

    # An odd-sized chunk, which requires a RIFF pad byte.
    odd_body = (
        _riff_chunk(b"fmt ", fmt)
        + _riff_chunk(b"junk", b"abc")
        + _riff_chunk(b"data", b"".join(_silence(2, 2, CD_RATE)))
    )
    (dest / "odd_chunk.wav").write_bytes(
        b"RIFF" + struct.pack("<I", 4 + len(odd_body)) + b"WAVE" + odd_body
    )

    # An odd-sized data chunk (8-bit mono, odd sample count).
    (dest / "odd_data.wav").write_bytes(_wav_bytes(1, 1, 8000, _silence(1, 1, 1001)))

    # A chunk after the data chunk (a real "extra RIFF chunk").
    trailing_body = (
        _riff_chunk(b"fmt ", fmt)
        + _riff_chunk(b"data", b"".join(_silence(2, 2, CD_RATE)))
        + _riff_chunk(b"JUNK", b"\x00" * 12)
    )
    (dest / "trailing_chunk.wav").write_bytes(
        b"RIFF" + struct.pack("<I", 4 + len(trailing_body)) + b"WAVE" + trailing_body
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dest", type=Path, help="directory to populate")
    generate(parser.parse_args().dest)
