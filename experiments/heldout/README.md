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
1c. **Post-wild-1gm re-run (2026-10-13): expected no-op confirmed — all
   wild-arm verdicts byte-identical to the wild-f4i run.** The
   `add-format-args-demand-support` extension (`format_args!` admitted to
   the argument-confined whitelist + family-wide format-capture disclosure
   for provider value items) moved none of the held-out verdicts:
   accept/accept/unknown/accept on
   intent-change/migration-supplied/platform-ineligibility/
   transitive-addition, exactly as before. The re-freeze REWROTE the
   committed `freeze.json` — only the wild binary digest changed
   (`d8788765…` → `3a37cad8…`); harness, corpus, adapters, oracle, seal,
   and split are byte-identical. This is the disclosed verification the
   change promised: the e5 cohort has no `format_args!` use and no
   provider-item captures, and the run confirms it — had any verdict
   moved, that would have been a corpus/adapter finding to investigate.
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

## wild-zfw corpus scaling (2026-11-11): 60 cases, 2 ecosystems

4. **Pre-registration order is auditable in git.** The corpus (60 cases:
   56 held_out, 4 development; 8 cargo + 52 python), the oracle
   (60 outcomes), the split, the freeze (11 tools) and the seal were
   committed together (9d63311) BEFORE `compare` ran the first wild verdict
   on any new cell. No post-hoc swaps; the 4 e5 unresolved cases and 10
   python drift-excluded cells keep recorded reasons in `excluded.json`.
5. **Python arm provenance is split-disclosed per cell**
   (`python_matrix.json` is the committed source): 28 section-2 cells carry
   their RECORDED outcomes as oracle (24 ok / 4 break; the 4 break cells are
   named in RESULTS.md §2), imported verbatim — not re-measured; 24 fresh
   cells carry outcomes measured this run by real pip installs of the exact
   versions plus the committed smoke scripts (23 ok / 1 break:
   flask-3.1.1 × werkzeug-3.0.0, the partitioned kwarg). Fresh cells were
   never seen by any tuning pass; the §2 cells ARE tuning-exposed for the
   py_wild engine (v1→v2 refinement saw them) — the corpus keeps them
   held_out with this ruling as the disclosure, per the brief.
6. **Fresh reproduction disagrees with the §2 record on 5/28 cells — all
   interpreter drift, not provider incompatibility.** Python 3.15 removed
   `pkgutil.get_loader` (breaks flask 2.2.5's own import — all 4 of its
   fresh §2 cells) and `ast.Str` (breaks werkzeug ≤2.3.0 imports —
   2.3.3/3.0.3 × 2.2.3 plus one agreement-on-outcome cell). The 5
   outcome-mismatches are recorded per cell in python_matrix.json
   (reproduction blocks); the oracle stays the §2 record. The 10 fresh
   matrix cells poisoned by the same drift are excluded with reasons —
   they have no provider-compatibility outcome in this environment. The
   requests arm reproduced 12/12.
7. **Checkers are ecosystem-scoped.** checkers.json entries carry
   `ecosystems`; compare skips non-applicable checker×case pairs (216
   skipped, recorded in compare.json, excluded from every denominator).
   The report's per-checker break/ok denominators are now computed over
   the cases that checker actually ran on (identical to pool-wide for a
   single-ecosystem corpus).
8. **Aggregate accuracy is now recorded — alongside, never instead of,
   the separate metrics.** The report gains per-checker aggregate-accuracy
   sections and a corpus-aggregate section, each with explicit denominators
   (decided runs; unknown excluded from numerator and denominator and
   counted separately).
9. **compare exit policy changed (disclosed).** Definite failures are
   findings of the comparison, not run failures: compare exits 0 when
   grading completes and 2 on integrity refusals (freeze drift, missing
   seal, post-seal oracle drift, missing outcomes). wild-1xk's exit-1-on-
   failures behavior drew attention to exactly the findings the report
   already carries; wild-zfw's completion gate requires the run itself to
   exit 0.
10. **Environment requirements for the python arm** (disclosed, not
    hidden): update_eval.py's replay needs `jsonschema` (PEP 668 blocks a
    user install on this host — installed via `pip install --target
    /tmp/wild-zfw-scratch/pylibs jsonschema` and PYTHONPATH); python
    trees are ephemeral scratch (/tmp/wild-zfw-scratch/pytrees),
    reinstallable from python_matrix.json's protocol block (pinned
    support deps: jinja2 3.1.6, click 8.1.8, itsdangerous 2.2.0,
    blinker 1.9.0, markupsafe 2.1.5, certifi 2026.10.23,
    charset_normalizer 3.5.2, idna 3.10). A fresh clone re-freezes before
    comparing (freeze digests include the wild binary).

Held-out results over 56 cases (6 oracle-break, 50 oracle-ok; separate
denominators first, aggregate second):

| checker | eco | missed-breakage | false-block | coverage | unknown | aggregate-accuracy |
|---|---|---|---|---|---|---|
| host_ranges | cargo | 0/1 | 2/3 | 4/4 | 0 | 2/4 |
| ci | cargo | 0/1 | 1/3 (intent-change) | 4/4 | 0 | 3/4 |
| ecosystem | cargo | 1/1 (platform 1.8.0) | 1/3 (2.1.0) | 4/4 | 0 | 2/4 |
| wild | cargo | 0/1 | 0/3 | 3/4 | 1/4 | 3/4 |
| py_declared | python | 1/5 (flask-2.2.5 × wk-3.1.3, the §2 `__version__` catch) | 10/47 | 52/52 | 0 | 41/52 |
| py_wild | python | 4/5 (the `partitioned=` cells — demand-invisible, §2's documented blind spot) | 0/47 | 52/52 | 0 | 48/52 |

py_wild's one correct-reject is its true §2 catch; the corpus aggregate
(99 correct / 119 decided runs, 1 unknown) is recorded in report.md — the
separate columns remain the safety analysis. The §2 tradeoff reproduces on
the scaled corpus: declared ranges (both ecosystems) false-block compatible
updates; caret/ecosystem rules miss real breakages; CI false-blocks a
behavior change; the contract tools miss demand-invisible breaks.

## Reproduction

```sh
python3 experiments/heldout_corpus.py build \
  --cohort experiments/update_fixtures/e5/cases.json --out experiments/heldout
# ^ merges python_matrix.json by default (wild-zfw); pass `--python-matrix ''`
#   for the legacy cargo-only corpus. compare additionally needs the python
#   trees (python_matrix.json protocol) and jsonschema on PYTHONPATH (see
#   ruling 10).
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