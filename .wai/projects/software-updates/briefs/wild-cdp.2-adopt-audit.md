# Brief: wild-cdp.2 — consecutive-release verdict audit for testaruda (wild.adopt observe)

## Why
Delegation rationale: this is a bounded research-lane slice — one stdlib-only Python
driver + one red-first test + one results file + one research-artifact paragraph.
Mechanically executable from the rulings below; the lead orchestrator stays free to
verify and ship. No Rust source changes, no openspec movement, no schema changes.

## Ticket
- **ID**: wild-cdp.2 (P2, claimed in this run; bd in_progress, epic wild-cdp)
- **Desired outcome**: an honest, reproducible audit of testaruda's crates.io release
  history: for every consecutive release pair, a contract-checked verdict computed by
  the real `wild` binary, compared against the release's declared semver bump, with
  every disagreement and every Unknown disclosed. Deliverables:
  1. `experiments/wild_adopt_audit.py` — the driver (stdlib only, no new deps)
  2. `tests/test_adopt_audit.py` — red-first smoke test (synthetic 3-release corpus)
  3. `results/adopt-audit-testaruda-2026-10-14.txt` — full real-corpus run output
  4. Research paragraph appended to
     `.wai/projects/software-updates/research/2026-10-14-dogfooding-wild-into-dulce-de-leche.md`
     (rung-1 section) citing headline numbers: pairs audited, verdict distribution,
     disagreement count, Unknown rate with named reasons.

## Design rulings (PRE-APPROVED by lead session — implement as stated)

- **D1 — target corpus: testaruda.** crates.io lists 12 versions (0.1.0 … 0.5.4) →
  11 consecutive pairs, satisfying the ticket's ≥8-pair Must gate with no shortfall.
  It is true semver (0.x minor/patch), unlike wai-cli's calver (8 versions, 7 pairs,
  would trip the disclosure clause). Fetch the version list from
  `https://crates.io/api/v1/crates/testaruda` (User-Agent header required by crates.io
  policy: `"wild-adopt-audit-research (charly-vibes)"`); fetch each version's source via
  `https://crates.io/api/v1/crates/testaruda/<ver>/download` → tar.gz → unpack to a
  temp dir. If network is unavailable, the driver must fail with a named diagnostic —
  no synthetic substitution of real history.
- **D2 — the consumer is a generated caller crate.** A scoped `wild check` verdicts a
  candidate bundle against a base bundle for a named consumer boundary. For the audit,
  the consumer's demand is testaruda's *public surface as used by an external caller*.
  Concretely, mirror the `write_bundle(consumer_lib=…, provider_lib=…)` pattern from
  `tests/runtime/test_extract.py` (helpers are importable: `BIN`, `run_extract`,
  `write_bundle`, `request_record`, `sha`; see `check_request_record` +
  `CHECKER`/`POLICY` constants in `tests/runtime/test_scoped_check.py` for the exact
  check-request shape). For each pair (prev = base, next = candidate):
  1. `wild extract` the prev tree → read its extraction report's complete inventory of
     public fns with supported signatures.
  2. Generate a consumer crate whose lib calls every inventoried public fn once with
     argument literals drawn from its signature (bools, ints, &str literals, String).
     This generated caller is *part of the base bundle*.
  3. The candidate bundle carries the same generated caller text + the next tree.
  4. `wild check --request <file> --format json --report <file>` with base = prev
     bundle, candidate = next bundle, consumer = the generated caller.
  A fn with an unsupported-signature gap is NOT called by the generator and is listed
  in the artifact as a coverage gap (it cannot contribute demand — disclosed, never
  silent).
- **D3 — verdict semantics (the audit table).** Exit codes are 0=accept, 1=refuse
  (envelope `decision` distinguishes reject vs unknown — read the envelope, not the
  exit code), 2=error. Per pair record: `bump_kind` (semver: 0.x minor/patch/major
  from the declared version strings — version strings are metadata for *comparison*
  only, never evidence), `computed_verdict` (accept / reject / unknown+diagnostics),
  and `audit_row`:
  - minor or patch bump + accept → `consistent`
  - minor or patch bump + reject → **DISAGREEMENT: semver claimed compatible, wild
    computed a break** (the headline finding class)
  - any bump + unknown → `abstained` with the named diagnostics (gaps)
  - major bump + accept → `consistent` (semver over-claimed breakage — record as a
    note, not a disagreement; over-conservatism is real but is not a lie about
    compatibility)
  - major bump + reject → `consistent`
  - error (exit 2) → `errored` with diagnostics; the pair is disclosed and skipped
  - repeated extraction of the same tree must be byte-identical; if not, flag
    determinism loss as a finding.
- **D4 — driver shape.** `experiments/wild_adopt_audit.py`, stdlib only, argparse:
  `--crate <name> --out <results-file> [--limit-pairs N] [--offline]`. Steps: fetch
  version list → fetch+unpack sources → build bundles per pair → run extract+check via
  the `wild` binary → render the audit table + summary → write results file. The wild
  binary is located like the tests do (`BIN` resolution: cargo build once if absent).
  Every subprocess result is echoed with its command line in the results file. The
  driver writes the JSON audit rows to stdout separately from the human table.
- **D5 — test (red-first).** `tests/test_adopt_audit.py`: a synthetic 3-release corpus
  (three tiny provider crates in-tree, declared versions 0.1.0 → 0.2.0 → 0.2.1, where
  0.2.0 removes a public fn the caller uses and 0.2.1 changes nothing public). Assert:
  (a) the minor bump pair with a removed demanded fn audits as DISAGREEMENT;
  (b) the patch pair audits as consistent/accept;
  (c) the run writes a results file and exits 0;
  (d) with network monkeypatched off, the driver fails with the named diagnostic.
  The test feeds the driver local unpacked sources (a `--sources <dir>` override
  mapping version → tree) so the red test never touches the network. Prove red before
  implementation (ImportError/path failure counts).
- **D6 — anti-goals.** Do NOT implement the `wild adopt` CLI (spec'd, unimplemented —
  explicitly out of scope). Do NOT modify any Rust source, schemas, openspec changes,
  or existing tests (the new test file is additive). Do NOT let the driver fabricate
  verdicts: every verdict line in the results file must correspond to a real `wild
  check` invocation echoed with its exit code. Do NOT retry a crashed subprocess into
  a different verdict.
- **D7 — follow-up threshold.** If the extractor's gap rate makes >50% of pairs
  abstain (Unknown), stop extending: record the rate, write the artifact paragraph,
  and surface it as the finding — gap-rate measurement IS the deliverable, not a
  failure. If crates.io source for any version fails to unpack or extract, record
  that version as `source-unavailable` and continue.

## Exact commands
- Red/green: `python3 -m pytest tests/test_adopt_audit.py -q`
- Real run: `python3 experiments/wild_adopt_audit.py --crate testaruda --out results/adopt-audit-testaruda-2026-10-14.txt`
- Regression (must stay green, unchanged): `python3 -m pytest tests/test_prototype_smoke.py tests/runtime -q`
- Repo gates for landing: `JUST_TEMPDIR=/tmp just ci`, `openspec validate --all --strict`

## Out of scope
Any semantic change to wild; obligations authoring; registry/deploy; ddl-side work
(that is wild-cdp.1/.3); publishing anything.
