# Real-project experiments (prototype extractors, toy checker)

Run order: `run_rust.py`, `run_spk.py` (needs genesis-vibes crates + specodelic tags under /tmp/proj),
`setup.sh`, `oracle.py`, `eval_py.py` (Python pairs). Paths are hard-coded to the sandbox.

## 1. genesis-vibes (provider) and specodelic (consumer), Rust
- 16 crate versions on crates.io (0.2.0 to 0.12.0), 6 specodelic tags (v0.1.0 to v0.5.0).
- Extractor: tree-sitter over `pub` items (about 345 slots at 0.2.0, 773 at 0.12.0).
- 15 consecutive releases: Cargo's 0.x caret rule calls 5 compatible (the patch bumps); the contract calls 9 accretions and 6 breaks.
  They disagree on 6 transitions: 5 where Cargo is conservative (0.3->0.4, 0.4->0.5, 0.8.3->0.9, 0.10.1->0.11, 0.11.1->0.12) and 1 where a patch release broke callers (0.8.0->0.8.1 added a public struct field).
- Over all 120 version pairs: 14 Cargo-incompatible but accretion; 3 Cargo-compatible but break.
- 0.8.1 is confirmed by genesis' own CHANGELOG (struct-literal callers must add `title: None`) and by specodelic v0.2.0, which added `title:` when it moved from genesis 0.7.0 to 0.8.1.
- 0.11.1->0.12.0 shows no public-surface change; the CHANGELOG declares a behavior break in `lefthook::ensure_wired`, which specodelic v0.5.0 does not use (it uses `ensure_command_wired`).
- Demand per specodelic release: 37, 48, 80, 80, 80 slots. Versions the demand allows beyond Cargo's range: v0.1.0 +1 (0.8.0), v0.2.0 +6, v0.3.0 +3, v0.4.0 and v0.5.0 +1 (0.12.0).
- Not done: a compile oracle. Sandbox cargo is 1.75; these crates use edition 2024 (needs 1.85+) and rustup is unreachable.

## 2. Flask/Werkzeug and requests/urllib3, Python (execution oracle)
28 consumer-by-provider cells installed side by side and exercised with a smoke test (small, so it understates real breakage).
- Oracle: 24 pass, 4 fail.
- Tool v1 (symbol demand): 23 true pass, 3 false pass, 1 false break, 1 true break (accuracy 0.86).
- Tool v2 (adds call-site arguments): 24 true pass, 3 false pass, 0 false break, 1 true break (accuracy 0.89).
- Declared ranges: 18 true pass, 1 false pass, 6 false break, 3 true break (accuracy 0.75).
- Real catch: Flask 2.2.5 with Werkzeug 3.1.3 fails because `werkzeug.__version__` was removed; the declared range (>=2.2.2, no upper bound) allows it.
- Misses: Flask 3.1.1 with Werkzeug below 3.1 fails because Flask passes `partitioned=` to `Response.set_cookie`. That is a keyword on a method of a returned object; without type inference the demand is invisible. The declared floor (>=3.1.0) catches it.

Caveats: two extractor refinements (`__version__` and module `__getattr__`; call-site arguments) were made after seeing oracle failures, so v1/v2 numbers are optimistic. Small sample (28 cells, 2 pairs).

## 3. specodelic's own CLI and JSON output across releases (real binaries)
Binaries exist for v0.2.0, v0.3.0, v0.4.0 only (checksums verified). v0.1.0, v0.3.1 and v0.5.0 (published 2026-10-03, now "latest") have no binary assets, and the sandbox cannot build them (rustc 1.75 vs 1.88 required).
- CLI contract (`cli_extract.py`, crawls `--help`): 197 slots at v0.2.0, 218 at v0.3.0 and v0.4.0.
  v0.2.0 -> v0.3.0 adds two commands (`archive-companion`, `parse`); v0.3.0 -> v0.4.0 is identical. Both transitions are accretions.
- A first run flagged v0.3.0 as breaking because a new command has a required argument. That was a modelling flaw (a new command's arguments bind nobody), fixed by modelling each command's arguments as a callable signature.
- JSON output shape (lint, graph, doctor over 3 corpora): 438 key-path slots, identical in all three releases.
- Behavior (same commands, same inputs), 3 of 7 command/corpus pairs differ despite identical shapes:
  - `linter.law_cases` became an error in v0.3.0 (+3 issues on the v0.1.0-era corpus).
  - `linter.single_root_reachable` got stricter in v0.4.0 (+8 warnings on the v0.1.0-era corpus, +3 on the v0.4.0 corpus).
  - `doctor` reports a different format revision.
- Exit status: the real corpora did not flip (the old corpus already fails on other rules; the new rule is advisory).
  A constructed spec (a law property without `**identity:**` / `**associativity:**` labels) exits 0 under v0.2.0 and 1 under v0.3.0 and v0.4.0, so a CI gate can flip. That fixture is derived from the rule delta, not found in the wild.
- Release notes for v0.3.0 and v0.4.0 contain only a full-changelog link; no breaking change was declared on the page.
- Reading: tier 1 (shape) passes both transitions; a corpus replay (tier 3) detects both and names the rules.

## 4. Semantic-composition replacement experiment (wild-9co.2)
- `composition_replacement.py`: frozen finite reservation domain (6 two-op schedules, commit step budget 8), independently specified public-event oracle (safety L1 + bounded progress L2), five implementations with recorded digests, three projections, four evidence claims.
- C01: same-shape stale-read replacement accepted by the structural check (red), public oracle flags 4/6 schedules. C02: independently written token-CAS implementation allowed on 6/6. C08: dishonest projections rejected by the event-completeness fixture. C14: deadlock fails bounded progress (safety-only would pass); beyond-bound is unknown. C16: subdomain/foreign-oracle/edited-law claims refused.
- Scope: finite frozen domain only; schedules outside the six are unknown; no v1 runtime, unbounded liveness, or cross-language conformance. Assertions pinned in `tests/test_composition_replacement.py`.
