# Held-out corpus artifacts (wild-1xk)

Purpose: the committed inputs, outputs, and rulings of the wild-1xk held-out
comparison run. Responsibilities: document what each artifact is, the design
rulings a reader needs to audit the results, and how to reproduce the run.
Rationale: the comparison's discipline (freeze, sealed split, sealed oracle)
is only auditable if the committed artifacts carry their own story.

## Artifact map

| artifact | producer | role |
|---|---|---|
| `cases.json` | `heldout_corpus.py build` | comparison corpus: 8 adjudicable cases (4 `held_out`, 4 `development`), family = case id, human_minutes null/unavailable |
| `oracle.json` | `heldout_corpus.py build` | independent outcomes (compatible→ok, incompatible→break) from the e5 cohort's verdicts, established by real Cargo replay **before** any miner tuning |
| `excluded.json` | `heldout_corpus.py build` | the 4 e5 evaluation cases whose `independent_verdict` is `unresolved` (resolution-level refusals — singleton conflict, platform/toolchain gaps, wrong target, baseline failure). They cannot get a break/ok oracle outcome, so they are excluded with recorded reasons, never graded |
| `case_context.json` | `heldout_corpus.py build` | per-case real context: consumer tree, base version (from the consumer's committed Cargo.lock), target |
| `checkers.json` | `heldout_corpus.py build` | the four real adapters as harness command templates |
| `freeze/freeze.json` | `heldout_eval.py freeze` | sha256 digests of the 8 evaluation tools (harness, corpus builder, adapters, update_eval, wild binary) at run time |
| `split/split.json` | `heldout_eval.py split` | committed development/held-out split with family-integrity leakage guard |
| `seal/oracle.seal.json` | `heldout_eval.py seal` | the oracle's digest, sealed before any held-out comparison; `compare` refuses on post-seal oracle drift |
| `compare.json` | `heldout_eval.py compare` | the run record: per checker × case verdicts, outcome classes, elapsed seconds, freeze/oracle provenance digests |
| `report.md` | `heldout_eval.py report` | separate-metrics report — missed breakages, false blocks, Unknown rate, coverage, execution cost, human contract-maintenance time, each with its own denominator; aggregate accuracy deliberately absent |

## Design rulings a reader needs

1. **The wild arm reports Unknown on all 4 held-out cases (coverage 0/4).**
   The landed `rust-cargo-local-1` profile refuses consumers whose code
   contains constructs outside its supported set: the e5 consumers invoke
   `println!`, and expression macros carry `unsupported-construct` +
   `incomplete-demand` gaps, so the scoped claim is refused as Unknown — the
   honest refusal per the disclose-every-unsupported-mechanism law. The
   adapter deliberately does **not** rewrite fixture code to dodge the
   refusal; that would manufacture agreement. Extending the extractor's
   supported set is a runtime-semantics change (OpenSpec territory), out of
   scope for wild-1xk. The 0/4 coverage is itself a comparison finding.

1a. **Post-wild-m7f.3 re-run (2026-10-13): coverage unchanged at 0/4 —
   the macro extension was necessary but not sufficient.** The
   add-std-macro-demand-support change (whitelist of 15 argument-confined
   std macros + statement-position coverage) landed and is exercised by
   the re-run; the re-freeze REWROTE the committed `freeze.json` — only the
   wild binary digest changed (`d5f4c2ec…` → `77ccd5b4…`), the harness,
   corpus, adapters, oracle, seal, and split are byte-identical. The wild
   arm still refuses all four cases Unknown, and the diagnostics moved off
   macros entirely: the e5 provider API is string-shaped
   (`dept::greet(name: &str) -> String`, `farewell`, `farewell_spanish`),
   and the profile's signature subset supports only unit/bool/i8-u32 — so
   the provider's public functions are `unsupported-construct` gaps, the
   consumer demand `dept::greet` resolves to no supplied slot, and the
   scoped claim stays refused (`incomplete-demand`). The remaining blocker
   is a provider-side signature-subset extension (string types), a further
   runtime-semantics change tracked separately in beads; the adapter and
   corpus remain untouched.
1b. **Post-wild-7e9 re-run (2026-10-13): coverage 3/4 — the wild arm now
   produces real held-out verdicts.** The string-signature extension
   (wild-7e9: `String` → text-owned, `&str`/`&String` → text-borrowed in
   the `rust-cargo-local-1` signature subset) resolved the blocker ruling
   1a disclosed. The re-freeze REWROTE the committed `freeze.json` — only
   the wild binary digest changed (`77ccd5b4…` → `d8788765…`); the
   harness, corpus, adapters, oracle, seal, and split are byte-identical.
   Verdicts: accept on `intent-change`, `migration-supplied`,
   `transitive-addition` (all three oracle-ok — zero false blocks, better
   than every other arm on this pool); honest Unknown on
   `platform-ineligibility` (the one oracle-break case; envelope
   diagnostics `unsupported-construct, incomplete-demand` — the refusal
   stands, no fixture rewrite). Metrics: missed-breakage 0/1,
   false-block 0/3, coverage 3/4, unknown-rate 1/4. Per the epic
   wild-m7f goal gate, real coverage > 0 makes the epic a close
   candidate.
2. **The wild adapter mirrors `src/main.rs` into `src/lib.rs`.** The profile
   extracts from `src/lib.rs` per member; the e5 consumers are binaries.
   The mirroring is applied identically to base and candidate (same demand
   surface), never mutates a committed fixture tree, and is disclosed here.
3. **The base workspace is used exactly as committed — no `cargo update`.**
   The committed base lock intentionally carries a stale checksum for
   `dept 1.2.3` (that is the graded `baseline-failure` discipline from
   wild-aoq.2); a base-side `cargo update` would trip checksum verification.
   Only the candidate is resolved through a real authorized update (pin to
   the exact target + `cargo update --offline` against the frozen registry),
   matching the replay machinery.
4. **Host declared ranges use the pre-update committed requirement.** The
   consumer-base declares `dept = "~1.2"` — cargo tilde semantics
   (`>=1.2.0, <1.3.0`) — so 1.8.0 and 1.9.0 are range-rejected even though
   the authorized update phase rewrites the manifest. The checker measures
   what the host's own declaration permits, not what the harness edited.
5. **Human contract-maintenance time is null/unavailable** for these
   synthetic cases; the report prints null with named basis, never
   fabricated zeros.

## Results summary (held-out pool: 1 definite-break, 3 definite-ok)

| checker | missed-breakage | false-block | coverage | unknown |
|---|---|---|---|---|
| host_ranges | 0/1 | 2/3 (1.8.0, 1.9.0 range-rejected) | 4/4 | 0 |
| ci | 0/1 | 1/3 (intent-change 1.2.4: the behavior change fails the suite though the update is compatible) | 4/4 | 0 |
| ecosystem | 1/1 (platform-ineligibility 1.8.0: caret-compatible yet breaks) | 1/3 (migration-supplied 2.1.0) | 4/4 | 0 |
| wild | 0/1 | 0/3 | 3/4 | 1/4 |

(wild row from the post-wild-7e9 re-run — see ruling 1b. The m7f.3 macro
extension alone had left the row at 0/4 with provider signature gaps;
the string-signature extension resolved it.)

The separate columns are the point: aggregate accuracy would hide that the
ecosystem caret rule misses the one real breakage while CI false-blocks an
intent change and the declared range blocks two compatible updates.

## Reproduction

```sh
python3 experiments/heldout_corpus.py build \
  --cohort experiments/update_fixtures/e5/cases.json --out experiments/heldout
python3 experiments/heldout_eval.py split --cases experiments/heldout/cases.json \
  --out experiments/heldout/split
python3 experiments/heldout_eval.py seal --oracle experiments/heldout/oracle.json \
  --out experiments/heldout/seal
python3 experiments/heldout_eval.py freeze --tool experiments/heldout_eval.py \
  --tool experiments/heldout_corpus.py \
  --tool experiments/heldout_adapters/host_ranges.py \
  --tool experiments/heldout_adapters/ci.py \
  --tool experiments/heldout_adapters/ecosystem.py \
  --tool experiments/heldout_adapters/wild.py \
  --tool experiments/update_eval.py --tool target/debug/wild \
  --out experiments/heldout/freeze
python3 experiments/heldout_eval.py compare \
  --freeze experiments/heldout/freeze --split experiments/heldout/split \
  --cases experiments/heldout/cases.json --oracle experiments/heldout/oracle.json \
  --seal experiments/heldout/seal --checkers experiments/heldout/checkers.json \
  --pool held_out --out experiments/heldout/compare.json
python3 experiments/heldout_eval.py report \
  --compare experiments/heldout/compare.json --cases experiments/heldout/cases.json \
  --oracle experiments/heldout/oracle.json --out experiments/heldout/report.md
```

`compare` exits 1 when definite failures exist (this run: 5) and refuses
(exit 2) on freeze drift, missing seal, post-seal oracle drift, or pool
cases missing oracle outcomes. The committed `freeze.json` records the
wild binary digest at run time; a fresh clone re-freezes before comparing.

Disclaimer (verbatim from the report): this is validation of the value
proposition, not evidence that the future v1 runtime has the prototype
failure rates.