# CUE sheet conformance

This document records how `shntool split` (alias `shnsplit`) handles CUE-sheet
constructs. It describes the behavior of upstream shntool 3.0.10 as preserved by
this repository. It is a behavioral inventory, not a conformance claim against
an external specification, and it is the reference for the boundary described
in [ADR 0001](adr/0001-preserve-upstream-architecture.md).

## How this was determined

- Source: `src/mode_split.c` (`get_length_token`, `handle_cue_keyword`,
  `get_cue_field`, `extract`, `smrt_parse`, `read_split_points_file`,
  `cue_sprintf`, and the `cue_info` state).
- Documentation: `man/shntool.1` ("Specifying split points"), `ChangeLog`,
  `doc/CREDITS`.
- Observation: `test/tools/probe_cue.py` runs a fixed set of CUE sheets against
  a built binary and reports exit status, output files, and diagnostics.
- Cross-check: differential cases `split_cue`, `split_cue_bom`,
  `split_cue_crlf`, and `split_by_length` in `test/differential.py`.

Reproduce the observations with:

```sh
meson setup build
meson compile -C build
python3 test/tools/probe_cue.py --shntool build/shntool
```

## Classification legend

| Class | Meaning |
|---|---|
| **Supported** | Handled as the construct implies. |
| **Substituted** | The underlying need is served by a different mechanism; the construct itself is not modeled. |
| **Recognized, not acted on** | Identified (often only to select the CUE parser) but deliberately has no effect. |
| **Rejected** | Terminated with a diagnostic rather than handled. |
| **Mis-detected** | The sheet is classified as raw byte offsets instead of a CUE sheet. |

## Matrix

| CUE construct / scenario | Class | Observed behavior | Evidence |
|---|---|---|---|
| `INDEX 01` (ordered, single `FILE`) | Supported | One split point per line; N points produce N+1 files; a leading `00:00:00` point is dropped with a warning. | `probe_cue.py` `baseline_3track` (rc 0, 3 files); test `split_cue` |
| Global `TITLE` | Supported | Album name; consumed by `-t %a`. | `cue_sprintf` (`%a`); test `split_cue` |
| Global `PERFORMER` | Supported | Default artist; overrides track artists that are empty. | `globals` pass before `cue_sprintf` (`artists[i]` <- `artist`) |
| Track `TITLE` | Supported | Per-track title; consumed by `-t %t`. | `get_cue_field` -> `titles[trackno-1]`; test `split_cue` |
| Track `PERFORMER` | Supported | Per-track artist; consumed by `-t %p`. | `get_cue_field` -> `artists[trackno-1]`; naming probe (`Artist - ...`) |
| `TRACK nn` | Recognized, not acted on | Advances the parser's track counter; the number itself is neither parsed nor validated. `%n` comes from output position, not this field. | `handle_cue_keyword` `TRACK` branch; `cue_sprintf` (`tracknum + offset`) |
| `FILE` | Recognized, not acted on | Used only as a CUE-detection token; the filename is never opened or compared. A mismatched name changes nothing. | `probe_cue.py` `mismatched_file_name` (identical to baseline) |
| `REM` | Recognized, not acted on | Never parsed for content. | `handle_cue_keyword` returns immediately for `REM`; `probe_cue.py` `cdtext_and_rem` |
| `INDEX 00` (pregap) | Recognized, not acted on | Never a split point; the track begins at `INDEX 01`. Output is identical with or without the line. | `probe_cue.py` `index00_present` (identical to baseline) |
| CD-TEXT: `CATALOG`, `CDTEXTFILE`, `SONGWRITER`, `COMPOSER`, `ARRANGER`, `MESSAGE`, `DISC_ID`, `GENRE`, `TOC_INFO`, `TOC_INFO2`, `UPC_EAN`, `ISRC`, `SIZE_INFO` | Recognized, not acted on | Detection tokens only; not stored, not exposed to `-t`. | `get_length_token` keyword list; `probe_cue.py` `cdtext_and_rem` |
| Audio before track 1 (`INDEX 01` later than `00:00:00`) | Substituted | Emits an extra leading piece for the region before track 1, titled literally `pregap`, preserving HTOA audio. CUE pregap semantics are not modeled. | `probe_cue.py` `hidden_track1_nonzero` (rc 0, 4 files incl. `tk_00`); `-t %n_%t` yields `00_pregap.wav` |
| Pregap audio as a distinct track (`INDEX 00`) | Substituted | The need is met manually by `-e` / `-u` lead-in/lead-out overlap instead. | `mode_split.c` `adjust_for_leadinout`; `man/shntool.1` `-e`/`-u` |
| Multi-`FILE` sheet | Rejected (flattened) | Every `INDEX 01` from every `FILE` section becomes one ordered split sequence against the single input file. It succeeds, but the per-file semantics are wrong. | `probe_cue.py` `multifile` (rc 0, flattened); `FILE` ignored |
| Sheet whose first line is not a detection keyword (blank line, or first line `TRACK`) | Mis-detected | Falls back to raw byte-offset mode; the first non-numeric line raises a format error. | `probe_cue.py` `blank_first_line`, `no_file_line_starts_track` (rc 1) |
| Non-CD input with `m:ss:ff` | Rejected | `error: m:ss.ff format can only be used with CD-quality files`. CUE frames are CD-only; byte offsets are the escape hatch. | `probe_cue.py` `noncd_input`; `smrt_parse` |
| Non-increasing or duplicate split points | Rejected | `error: split point N is not greater than previous split point M`. | `probe_cue.py` `duplicate_split_point` |
| Split point equal to the data size | Supported | Dropped as redundant. | `man/shntool.1` "Specifying split points"; `process_file` |
| Split point beyond the data size | Rejected | `error: split points go beyond input file's data size`. | `probe_cue.py` `split_point_beyond_eof` |
| UTF-8 BOM | Supported | Skipped. | test `split_cue_bom`; `get_cue_keyword` |
| CRLF line endings | Supported | Handled. | test `split_cue_crlf` |
| Final line without a trailing newline | Supported | Handled (historical fix). | `ChangeLog` 3.0.1; `doc/CREDITS` (Wim Speekenbrink) |
| CUE-derived output naming `-t %p %a %t %n` | Supported (four fields only) | `-t` expands performer, album, track title, and output sequence number; requires at least one `TRACK` per output piece; duplicate names are rejected. | `cue_sprintf`; `probe` naming run |
| More `TRACK` lines than `SPLIT_MAX_PIECES` | Rejected (hardening) | Track counter is clamped; previously this indexed past the per-track arrays. A safety fix, not a semantic change. | `handle_cue_keyword` `TRACK` branch (this fork) |

## Detection heuristic

The parser starts in an "unknown" state. It switches to CUE mode only when a
line's first token is one of the recognized global keywords (`FILE`, `CATALOG`,
`CDTEXTFILE`, `REM`, `TITLE`, `PERFORMER`, `SONGWRITER`, `COMPOSER`,
`ARRANGER`, `MESSAGE`, `DISC_ID`, `GENRE`, `TOC_INFO`, `TOC_INFO2`, `UPC_EAN`,
`ISRC`, `SIZE_INFO`); otherwise it treats the input as raw byte-offset split
points. `TRACK` and `INDEX` are acted on but are not detection keywords, so a
sheet must lead with a recognized global line. This is why a leading blank line
or a first line of `TRACK 01 AUDIO` is mis-detected (see the matrix).

## Split-point model

- Split points must be strictly increasing, one per line.
- N split points create N+1 output files.
- A leading zero-valued point is discarded with a warning; a final point equal
  to the data size is dropped.
- `m:ss` rounds to the nearest sector boundary on CD-quality input; `m:ss.ff` is
  CD-only; exact byte offsets bypass alignment.
- The number of output pieces is bounded by `SPLIT_MAX_PIECES` (256).

## CUE-derived naming

`-t` supports exactly four fields: `%p` (performer), `%a` (album), `%t` (track
title), `%n` (output sequence number). Track artists fall back to the global
`PERFORMER` when empty. `%n` is derived from output position
(`tracknum + offset`), not from the CUE `TRACK` number. Naming fails if there
are fewer `TRACK` lines than output pieces, or if two pieces would produce the
same filename. `-m` applies character translation, and path separators in
generated names are converted to `-`.

## References

- `man/shntool.1`, "Specifying split points".
- `src/mode_split.c` — parser and naming implementation.
- `test/tools/probe_cue.py` — reproducible probe used for the matrix.
- `test/differential.py` — `split_cue`, `split_cue_bom`, `split_cue_crlf`,
  `split_by_length`.
- `test/fuzz/fuzz_cue.c` — coverage-guided fuzzing of the tokenizer.
- [ADR 0001](adr/0001-preserve-upstream-architecture.md) — the decision this
  document supports.
