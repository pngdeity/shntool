# 0001: Preserve the upstream module architecture and observable behavior

- Status: Accepted
- Date: 2026-09-18
- Related: [CUE sheet conformance](../cue-conformance.md)

## Context

This repository modernizes shntool 3.0.10 in place. The working agreement is
that the command-line interface and observable behavior are the specification:
the pristine sources are preserved under the `upstream-3.0.10` tag, and a
differential oracle (`test/differential.py`) compares exit status, output, and
digests against a reference build.

Hardening work (bounds checks, `printf` format attributes, sanitizers, fuzzing)
surfaced CUE-sheet parsing as the one area where user expectations and the
implementation diverge. Separately, the question arose whether the original
design is coherent or merely an accumulation of fixes, and whether the
modernization should reshape it.

Investigation of `ChangeLog`, `doc/CREDITS`, `man/shntool.1`, the module
headers, and targeted behavioral probes (`test/tools/probe_cue.py`, summarized
in `doc/cue-conformance.md`) supports two conclusions:

1. **The architecture is deliberate and cohesive.** The program is explicitly a
   core plus `mode_module` and `format_module` contracts, documented in
   `doc/modules.howto`. Cross-cutting behavior (output naming, clobber policy,
   partial-output cleanup, progress, canonical headers, sector arithmetic,
   ID3v2 skipping, decoder/encoder argument templating) is centralized in the
   `core_*` files and reused by every module. Extension is a first-class feature
   (`--with-extra-modes` / `--with-extra-formats`).
2. **The feature surface is an accumulated, issue-driven tail.** `ChangeLog` and
   `CREDITS` attribute most capabilities to named bug reporters; split mode's
   options proliferated; and the CUE reader is a recursive line tokenizer
   (`get_length_token`) riding the split-point reader with flat shared state
   (`cue_info`), not a CUE parser. Constructs that would require more structure
   were left out — sometimes deliberately, since the man page promises only a
   "simple CUE sheet".

The two are not in conflict. The core abstraction is narrow and stable ("read
WAVE data, transform it, write WAVE data"), so most requests could be satisfied
at the leaves without touching the trunk, and requests that did not fit were
declined rather than architected around.

## Decision

1. **Preserve the module architecture.** Do not rewrite the core/mode/format
   structure. Modernize around it (build system, language baseline, safety), not
   through it.
2. **Treat observable upstream behavior as the specification.** Changes fix
   memory safety, undefined behavior, and clear bugs; they do not redefine
   semantics. Anything that alters observable behavior must be justified and
   covered by the differential oracle.
3. **Treat the CUE subset as an intentional, documented boundary.** The
   supported, ignored, substituted, and rejected constructs are enumerated in
   `doc/cue-conformance.md`. Ignored constructs are scope, not defects.
4. **Harden the leaves rather than generalize the trunk.** Prefer bounds checks,
   format attributes, sanitizers, unit tests, and fuzzing at module boundaries
   over restructuring shared code.
5. **Require a separate decision to expand CUE semantics.** `INDEX 00`/pregap
   modeling, multi-`FILE` sheets, and CD-TEXT are product changes, not fixes. If
   pursued, they get their own ADR and their own test coverage; they must not be
   smuggled in as bug fixes.

## Rationale

- Rewriting risks the one asset that cannot be recovered: verified behavioral
  equivalence with the reference build.
- The module contracts are what made decades of format additions cheap;
  replacing them would discard that leverage.
- The CUE limits are the rare case where the narrow stream model was not
  stretched to fit. Documenting them converts an apparent defect into an
  explicit decision, preventing both accidental "fixes" and silent user
  surprise.
- Where this tree did correct the leaves (unbounded `strcpy` removal, the
  `-Wsign-compare` fixes, the empty-field pointer guard, the track-count
  clamp), those changes were safety- and behavior-preserving, consistent with
  this decision.

## Consequences

Positive:

- Behavior compatibility remains testable and auditable.
- Effort concentrates on measurable safety (sanitizers, fuzzing) rather than
  speculative redesign.
- CUE expectations are documented, reducing support ambiguity.

Negative:

- The tool remains a "simple CUE" splitter; users wanting full CUE semantics
  must look elsewhere or fund a separate design.
- Some duplication and weak encapsulation in the core (global context, per-mode
  input plumbing, `st_error`/`exit` control flow) remains by choice.
- `doc/cue-conformance.md` must be maintained if behavior ever changes.

Neutral:

- The conformance matrix is a snapshot of upstream 3.0.10 behavior as preserved
  by this fork. It is descriptive, not a claim against an external standard.

## Alternatives considered

- **Greenfield rewrite.** Rejected: discards behavioral equivalence, the
  differential oracle, and the module contracts for no demonstrated functional
  gain.
- **Implement the full CUE specification now.** Rejected as unforced scope: it
  changes the data model (a track may have several indices), breaks the
  documented "N split points -> N+1 files" invariant, has no consumer for
  CD-TEXT, and could not be verified against the reference build.
- **Refactor `split` into a real CUE parser without changing behavior.**
  Deferred: a defensible cleanup with some test value, but no user-visible
  benefit and non-trivial risk. It belongs in its own change with its own
  oracle.

## References

- `man/shntool.1`, "Specifying split points" — "a simple CUE sheet".
- `ChangeLog` 2.0.0 (`cue` mode; "simple CUE sheets for splitting") through
  3.0.8 (BOM handling).
- `doc/CREDITS` — feature origins (Boogie Shafer, Krzysztof Wojszko, John,
  Pierre-Yves, David Bonde, Wim Speekenbrink, Samson).
- `doc/modules.howto`, `include/module-types.h` — module contracts.
- `doc/cue-conformance.md` — construct-by-construct matrix.
- `test/tools/probe_cue.py` — reproducible probe.
- `test/differential.py`, `test/fuzz/fuzz_cue.c` — oracle and fuzz target.
