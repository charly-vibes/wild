---
sut_path: /var/home/sasha/para/areas/dev/gh/charly/wild
commit: 4e26885ac3549052cc38394ff3695fa280a403df
updated: 2026-11-27
external_references:
  - path: /var/home/sasha/para/areas/dev/gh/charly/reports/hegel-eval-2026-11-16/README.md
    why: Suite-level Hegel evaluation this run extends.
  - path: /var/home/sasha/para/areas/dev/gh/charly/antithesis/scratchbook/property-catalog.md
    why: Suite-level catalog section "wild (c22c150)" — the baselines this catalog refines.
  - path: /var/home/sasha/para/areas/dev/gh/charly/antithesis/scratchbook/properties/wild.md
    why: Prior screening-depth evidence; line citations re-verified at 4e26885.
  - path: https://github.com/antithesishq/antithesis-skills
    why: antithesis-research skill (version 2026-11-12 6ba10e2).
  - path: https://hegel.dev/
    why: Engine under evaluation; crate `hegeltest` 0.52.7.
---

# Property catalog — wild (v1 relations + check/extract pipeline)

Four properties, matching the bd wild-wz9 baseline candidates. Each entry
states the invariant, the check mode, the seam, the generator sketch, and a
predicted red/green status; full evidence and investigation logs live in
`properties/{slug}.md`. These are Hegel (in-process PBT) properties, not
Antithesis-platform properties: the engine runs them as harness assertions in
`tests/`, so every invariant below is an `Always`-style safety check — a
failing generated case fails the test — and no SUT-side SDK instrumentation
exists or is proposed. Fault injection and concurrency exploration are
explicitly out of scope for Hegel (see `deployment-topology.md`).

Predicted status is derived by reading the code at the pinned commit, not by
running a failing property (screening depth, per the suite-level caveat).

## Relations on contracts and types

### accretes-is-transitive — compatibility chains compose

| | |
|---|---|
| **Type** | Safety (category law) |
| **Property** | For contracts valid under `validate_contract`, `accretes(a,b) == Holds ∧ accretes(b,c) == Holds` implies `accretes(a,c) == Holds`. |
| **Invariant** | Always: no generated triple of valid contracts composes to a `Breaks` after two `Holds` steps. |
| **Check mode** | Pure in-process: `wild::v1::accretes` (`src/v1.rs:804`) on three generated valid contracts. |
| **Seam** | None needed — `accretes` and `validate_contract` are public. |
| **Generator sketch** | Generate a valid seed contract, then derive b and c by accreting/neutral edits (slot add/drop with tombstone, required→optional, interval widen, tombstone reactivate); keep edits inside the v1 semantic rules (sorted slots/tombstones/laws/relations by key, ids matching the v1 grammar `id_syntax` `src/v1.rs:219`, defaults `{present:false}` or `{present:true,value}` inhabiting the type, tombstone polarity `in` + non-required `src/v1.rs:242-249`). |
| **Predicted** | **RED.** Narrowed-tombstone removal (`subtype(tombstone, old)`, `src/v1.rs:898`) + containment reactivation (`:966`) breaks the chain; witness in the evidence file. |
| **Why it matters** | Transitivity is the product's composition claim (`docs/wild-formats-v1.md`: "the category laws apply to jointly composable interfaces"); a red here is a real spec/code divergence, not a synthetic failure. |

**Open Questions:**

- Is the narrowed-tombstone removal acceptance intentional? `(needs human input)` — recommendation recorded in `evaluation/synthesis.md` (match the format document's type-retention wording; the prototype's widened-tombstone direction also restores the law).

### subtype-is-preorder — subtype is reflexive and transitive on valid types

| | |
|---|---|
| **Type** | Safety |
| **Property** | For types passing `validate_type`: (a) `subtype(t,t) != Breaks` (reflexivity, never self-breaks), (b) `Holds(a,b) ∧ Holds(b,c) ⟹ Holds(a,c)` (transitivity of the proven-inclusion verdict), (c) `Breaks` is symmetric: `Breaks(a,b) ⟹ Breaks(b,a)`. |
| **Invariant** | Always: no generated valid type violates (a), (b), or (c). |
| **Check mode** | Pure in-process: `wild::v1::subtype` (`src/v1.rs:546`) over generated recursive types; validity filtered via `validate_contract` on a wrapping one-slot contract. |
| **Seam** | `validate_type` is private (`src/v1.rs:287`). Interim: wrap the type in a minimal one-slot contract and call public `validate_contract`. Preferred (wild-dr2): a `pub` seam for `validate_type` (suite-level implementability finding I2). |
| **Generator sketch** | Depth-bounded recursive type generator (scalar with/without intervals, record fields optional/required, open/closed with `closed_reason`, sums, sequence/map with length-cardinality intervals, function arities, opaque fingerprints); integers at interval boundaries (`min > max` rejected upstream); strings restricted per the v1 id/facet grammars. |
| **Predicted** | **GREEN** for (a) and (b) (the conservative table is a conjunction of interval/field containments, which are transitive; Unknown short-circuits to non-Holds, never to Breaks). (c) is a hypothesis with lower confidence — keep it a separate test so a (c) failure does not mask (a)/(b). |
| **Why it matters** | `accretes` composes `subtype` verdicts per slot; every accretion guarantee inherits the subtype table's soundness. |

**Open Questions:**

- Reflexivity is deliberately partial (integer without interval → `Unknown`, `src/v1.rs:616-640`); the property conditions on `validate_type`-valid types, but should an interval-less integer type be a *valid* type at all? `(partial: code treats it as valid-but-Unknown, doc does not forbid it)`.

### canonical-is-normal-form — canonicalization is a normal form

| | |
|---|---|
| **Type** | Safety (digest identity) |
| **Property** | For every parsed value `v`: `canonical(v)` reparses, `canonical(parse(canonical(v))) == canonical(v)` (idempotence), any object-key permutation / whitespace / escape-spelling variant of the input yields identical canonical bytes and digest (key-order independence, digest stability), and validation (`validate_contract`) is order-insensitive over the set-typed arrays. |
| **Invariant** | Always: no generated value round-trips to different canonical bytes or a different digest. |
| **Check mode** | Pure in-process: `formats::parse` (:104) / `formats::canonical` (:313) / digest, plus `validate_contract` on permuted contract documents. |
| **Seam** | None needed — all three are public. |
| **Generator sketch** | Strings with `"`, `\`, U+0000..U+001F, U+2028, non-BMP, lone-surrogate-adjacent forms; integers at the safe-integer boundary ±9007199254740991 (`src/formats.rs` parser bounds) and their base-ten spellings; objects built by permuting keys of generated contracts (contract-level: slots/tombstones sorted by name, laws by id, relations by id — permutation must not change validity or bytes). |
| **Predicted** | **GREEN.** The writer sorts keys and fixes escaping in one place; the strict parser refuses floats, duplicate keys, out-of-range integers, BOM, leading zeros. |
| **Why it matters** | Digest identity is how lineage, tombstones, and certificates identify contracts; any instability silently forks identity. |

**Open Questions:** None.

## CLI contract (check/extract pipeline)

### cli-exit-envelope-contract — every command maps outcomes to exits and a canonical envelope

| | |
|---|---|
| **Type** | Safety |
| **Property** | For any invocation of `extract --request <file> --output <dir>`, `check --request <file> --format json --report <file>`, `update plan --request <file> --output <file>`, or `v1 accretes --old <f> --new <f> --output <f>`: stdout is exactly one canonical-JSON document carrying the v1 `kind:"envelope"` with its fixed member set (`command`, `assurance`, `decision`, `tier_reports`, `slots`, `coverage{numerator,denominator,ratio_ppm}`, `checker`, `known_consumers`, `undeclared_consumers_covered`, `deployment`, `diagnostics`, `src/main.rs:37-69`) — bare at pinned commit 4e26885, or carried verbatim as `data` of the genesis shell (`ok`, `envelope_version`, `cli_version`, `envelope_kind` = ok/check/error, `warnings`, `meta`) now in flight (bd wild-lof, `src/genesis.rs:26-39`); exit is 0 iff decision `accept`, 1 for computed refusal (`Reject`/`Unknown`), 2 for malformed input or failed orchestration (`input-mismatch`/`invalid-contract` codes); nothing outside the requested output paths is written; `--version`/`-V` prints a plain version line with exit 0 and no envelope (`src/main.rs:833-840`). |
| **Invariant** | Always: no generated invocation produces a non-canonical envelope, a missing member, a wrong (exit, decision) pair, or a write outside the requested locations. |
| **Check mode** | Subprocess: Hegel `#[hegel::state_machine]` spawning the built `wild` binary per step, asserting on stdout bytes, exit code, and the output-tree diff. |
| **Seam** | None in the library — the binary is the seam; tests build it via `cargo`/`CARGO_BIN_EXE_wild`. Must run outside the Landlock law sandbox (`src/harness.rs` is for candidate artifacts only). |
| **Generator sketch** | Requests and contract documents composed from the same valid-contract generator plus a corruption layer (truncate, duplicate key, float, unknown kind, bad UTF-8 path, unreadable path, wrong flag order, extra args) to drive all three exit branches. |
| **Predicted** | **GREEN** for the envelope shape and (exit, decision) pairs (single `envelope` constructor, mapping reviewed at all five command paths); the write-outside guarantee is the riskiest clause (fact records under `<report dir>/facts/` are part of the declared contract, `src/main.rs:9-15`). |
| **Why it matters** | The envelope and exit mapping are the declared interop contract (`docs/wild-formats-v1.md` §Adoption/commands; `docs/wild-local-v1.md`); consumers script against them. |

**Open Questions:**

- Which stdout shape does the CLI contract pin — bare v1 envelope, or the genesis shell from in-flight bd wild-lof? `(partial: v1 members and exit mapping identical under both; only the outermost stdout shape differs)`
- Coverage `ratio_ppm` rounding uses integer division (`src/main.rs:46-49`); should the property pin exact floor semantics at boundary numerators, or only `null`-iff-zero-denominator? `(partial: doc says floor(1e6·n/d), code matches; boundary tests unpinned)`.
