# Change: Add external-crate awareness — declared external signature bundles for demand resolution

## Why

The `rust-cargo-local-1` inventory sees only the workspace members supplied
in the bundle, so `std`/prelude and third-party references keep named
`incomplete-demand` gaps — the dominant residual abstention cause after the
wild-158 widening (bd wild-90d). The measurement is in
`results/adopt-audit-158-1.txt`: **12/12 consecutive-release testaruda pairs
abstained (unknown-abstention rate 100.0%)**, `incomplete-demand` +
`unsupported-construct` diagnostics on every version 0.1.0–0.5.5, and the
0.5.5 audit line records **41 distinct external/unmodeled demand targets**
recorded but unresolved — `std.io.Error.new`, `std.io.ErrorKind::*`,
`std.sync.Arc.clone`, `std.sync.mpsc.channel`, `std.thread.spawn`,
`std.time.Duration.from_millis`, `std.fs.read_to_string`,
`Command.new`, `Stdio.piped`, `HashMap.new`, `libc.kill`, `libc.SIGKILL`,
`shell_words.split`, `Box.new`, `String.from_utf8_lossy`, `Vec.new`,
`u32.MAX` — none of which can ever resolve against a workspace-only
inventory. Every one of these is an abstention the profile repeats by
construction on every crate that touches `std`.

The ticket sets the decision: "Options to design: bundling trusted external
signatures vs declaring a trusted-crate digest set. Scope decision needed;
**never silently trust**." This proposal puts all three live options in
front of the maintainer with an enforceable trust model for the recommended
one.

## What Changes

- **Typed incomplete-demand reasons (Option C, zero-trust, first)**: every
  unresolved demand gap carries a typed reason — `external-crate-unmodeled`,
  `std-item`, `unsupported-signature`, `unresolved-receiver`,
  `unknown-target` — so audits can measure *which* residual causes remain
  instead of one opaque `incomplete-demand` bucket. No resolution change,
  no trust change; abstention behavior identical, observability added.
- **Declared external signature bundles (Option A, the mechanism)**: an
  extraction bundle MAY supply signature inventories for external crates it
  declares (including `std`/prelude). Each bundle is digested and named in
  the extraction request; demand resolution may resolve against those
  external slots, marking resolved demands with `origin: external` and the
  supplying digest. Undeclared external demand keeps its typed gap.
- **Explicit trust, never silent (the trust model, in spec)**: there is no
  implicit `std` trust — std signatures are just another declared,
  digest-pinned bundle. A demand resolved against external signatures is
  structurally weaker than a bundle-supplied one (it is a claim about an
  artifact the bundle did not ship), so the contract records the external
  digest set used, and a check consuming such a contract reports that set;
  an unverifiable digest yields Unknown, never a silent pass.
- **Option B rejected** (a wild-shipped trusted-crate digest set): it makes
  wild itself a trusted third party to every extraction, conflicts with
  `extractor_isolated` ("extractors read only the source they are given")
  unless the set is supplied as an input anyway — at which point it is
  Option A with worse provenance. Rejected with reasoning recorded in
  design.md, not silently dropped.
- **What will NOT change**: verdict and refusal semantics (any gap still
  refuses scoped acceptance); cross-crate constructor *calls* gain no
  automatic trust — they resolve only when the corresponding external
  bundle is declared; nothing is downloaded or computed at extraction time
  (`extractor_isolated` untouched).

## Impact

- Specs: `openspec/specs/wild-extract/spec.md` — ADDED "Typed
  incomplete-demand disclosure reasons" and ADDED "Declared external
  signature bundles".
- Code: `src/extract/demand_resolution.rs` (typed reasons on unresolved
  entries; resolution against supplied external inventories with origin
  marking), the extraction request/bundle format for declaring external
  signature bundles and their digests (`docs/wild-formats-v1.md`,
  `schemas/wild-v1.schema.json` — format lane).
- Measured gate: re-run the adopt-audit harness
  (`results/adopt-audit-158-1.txt` harness); the typed reasons must show the
  41 external demand targets on testaruda 0.5.5 moving from
  `external-crate-unmodeled` gaps to resolved `origin: external` demands
  (Option A stage) or at minimum to countably-typed abstentions (Option C
  stage).
