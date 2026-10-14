---
tags: [research]
project: software-updates
date: 2026-10-14
question: What is needed to use wild instead of semantic versioning across the dulce-de-leche fleet, for rolling releases and auto-updates?
---

# Dogfooding wild into dulce-de-leche

## Ground truth today (verified in both repos)

**ddl side — where semver gating lives:**
- `src/compat.rs` — hand-maintained semver-range matrix (`wai = ">=2026.3.0"`, …),
  embedded fallback + runtime fetch from
  `https://charly-vibes.github.io/ddl/compatibility.json`. Verified against
  code: consulted only in `ddl status` (src/main.rs:819) and the version-check
  path (src/main.rs:908) — advisory rendering, maintained by humans reading
  changelogs.
- `src/installer.rs::upgrade_decision` (DDL-5bs) — the automated upgrade gate
  is release-age cooldown (`min_release_age_days`) + "same artifact" dedup.
  **No compatibility semantics exist in the automated path at all.** This
  sharpens the thesis: wild does not replace an automated semver gate — it
  adds the first automated gate where today there is none, and replaces the
  human-maintained matrix as the compatibility oracle.
- `versions.ddl.toml` — CI pins, updated deliberately ("a broken release of any
  tool must not break CI of the whole fleet"). Stale pins are the symptom of
  unmeasured compatibility; pinning itself is a supply-chain/determinism
  control (standardization §4) and survives wild — rung 4 keeps exact artifact
  hashes and CI determinism unchanged. Orthogonal to compatibility, like
  DDL-5bs below.
- 12 managed tools; install methods: cargo (wai-cli, testaruda, dont-cli,
  pretender, vampiro, specodelic, turu), npm (openspec), pinned GitHub release
  binary (bd), plus homebrew/scoop distributions. **wild itself is not yet in
  the managed set.**

**wild side — what exists vs what is spec'd:**
- Implemented CLI: `extract` (rust-cargo-local-1; scalar + string signatures,
  std macro whitelist after wild-m7f, non-scalar-return gap after wild-73j),
  `check` (scoped structural + protected-context obligations + authored law
  execution), `update plan` (base-digest-verified planning with honest
  refusals), `v1` (canonical reader).
- Spec'd but not implemented: `wild.registry` (append-only verdict log),
  `wild.deploy` (gates/leases/rollout), `wild.compose` (whole-graph
  certificates — prototyped separately in unikernel-cd wild-m8c), `wild.adopt`
  (the adoption ladder).
- Key invariant that makes the goal coherent (`wild-core`:
  `compatibility_computed`): *no compatibility verdict is derived from a
  version string; version strings are metadata and attestation input only*.

**The fleet's real dependency edges:** process-level, not link-level. ddl
invokes every tool; wai detects plugins by running binaries; tools read each
other's managed blocks (`.ddl/`, AGENTS.md markers); testaruda drives just/cargo.
No fleet tool links another fleet tool's crates. The current extractor captures
crate-internal Rust API surface — necessary but not sufficient for fleet
interop.

## The two mismatches to solve

1. **Contract surface ≠ extractor surface.** rust-cargo-local-1 sees Rust
   items; fleet interop is CLI verbs, exit codes, config/env surface. Two
   honest fits: (a) authored **law suites** — digest-bound executables that run
   the candidate binary and assert behavior (already supported by
   `wild check`); (b) a future CLI-surface extraction profile (e.g. clap-derive
   scanning — feasibility unknown, clap is third-party proc-macro, not the std
   macro whitelist). Start with laws; keep extraction for Rust-linked checks
   where they exist.
2. **No publish/consume plumbing.** Contracts must be produced at release time
   by each tool's CI and fetched by ddl at upgrade time. Today nothing publishes
   a contract bundle, and ddl has no fetch-and-verify path for one.

## The ladder, mapped onto ddl (wild.adopt: observe → shadow → gate → native)

**Rung 0 — adopt wild into the fleet.** ddl manages wild. Small, mechanical,
and required for everything else (ddl is the bootstrap consumer).

**Rung 1 — observe: history audit (highest-information first move).**
wild.adopt's `past_claims_audited` invariant: extract each historical release of
a fleet tool (crates.io/npm release archives carry source; bd's GitHub
releases carry source via tags), compute
verdicts between consecutive releases, and list where the declared semver bump
disagrees with the computed verdict. Zero enforcement, zero release-process
change, and it validates the extractor against real fleet code. It also directly
measures the headline claim: *where semver lied*. Needs a driver (the `adopt`
command is spec'd but not implemented — an experiments/-style replay script
like update_eval is enough).

**Rung 1 result — testaruda audit (2026-10-14, beads wild-cdp.2).**
Replayed testaruda's full crates.io history (12 versions, 0.1.0 → 0.5.4, 11
consecutive pairs) through the real `wild` binary via the stdlib-only driver
`experiments/wild_adopt_audit.py` (synthetic red-first test at
`tests/test_adopt_audit.py`; full run log at
`results/adopt-audit-testaruda-2026-10-14.txt`). Every verdict line in the log
corresponds to a real `wild extract`/`wild check` invocation echoed with its
command line and exit code; repeated extraction was byte-identical for every
version (determinism pass). Headline numbers: **11 pairs audited — 0
consistent, 0 disagreement, 11 abstained (100% unknown rate), 0 errored, 0
source-unavailable.** The zero-disagreement count is *not* "semver never lied
for testaruda" — it is "wild abstained on every pair, and abstention is not a
compatibility claim." The named reason is uniform across all 11 pairs: every
testaruda release declares its public API in non-inline modules (`pub mod
adapter;` + `pub use` re-exports), the rust-cargo-local-1 profile walks only
each member's `src/lib.rs`, so each release surfaces `unsupported-construct`
gaps ("non-inline module requires file resolution"), both sides' inventories
are incomplete, and scoped check correctly refuses to ground a compatibility
claim — zero fabricated accepts, which is the honest-abstention property
working as designed. Per the ticket's follow-up threshold (>50% abstention:
gap-rate measurement IS the deliverable), the finding for rung 2: **module/
file resolution is the top extractor gap gating adopt verdicts on real fleet
code** — until `wild extract` resolves `mod` files (or demand is authored for
re-exported items), 100% of testaruda's release pairs abstain. The synthetic
corpus proves the audit machinery itself computes real accept/reject verdicts
when inventory is complete (minor bump removing a demanded fn audits
DISAGREEMENT; patch bump with unchanged surface audits consistent).

**Rung 1 addendum — after mod-path resolution (2026-10-14, beads wild-cdp.4).**
`rust-cargo-local-1` now resolves public non-inline modules against the
committed bundle (`src/name.rs`, `src/name/mod.rs`, recursive, with
rustc's entry-file rule: `lib.rs`/`main.rs` resolve modules in their own
directory). Red-first tests in `tests/runtime/test_extract.py`: resolved
module fns become genuine inventory slots and dep-qualified calls into
them resolve as demand; an absent module file keeps the honest gap; a
private non-inline module carries no public surface. Re-running the audit
(`results/adopt-audit-cdp4-1841.txt`, 12 consecutive pairs over 13
versions): **abstention is still 100%, but the gap composition changed** —
the previous run's blocker is gone. Every release now surfaces
`testaruda::adapter::*` slots that the prior run never saw (grep for
`adapter::` in the old log: 0 hits), and "non-inline module requires file
resolution" no longer appears. The residual abstention causes, in order
of measured frequency, are: `impl` blocks / method implementations
("outside the supported profile"), returned-object method calls
(`.to_string()`, `.is_empty()` — "outside the supported demand profile"),
enum-variant demand paths (`AdapterError::Io`), and public fns outside the
scalar signature subset. Finding for rung 2: mod-path resolution was
necessary but not sufficient — verdicts on real fleet code additionally
require the method/variant demand profile to widen, which is a deliberate
scope decision for the next ticket, not a silent relaxation of the
signature subset.

**Rung 1 addendum 2 — after demand-profile widening (2026-10-14, beads
wild-158, change `add-method-variant-demand`).** The two candidate
categories widened per pre-approved rulings D1–D3: (1) method-call demand
resolves in bounded shapes (receiver is a path resolving through the
bounded demand rules, or a call whose head resolves to an inventoried
same-crate constructor with a recorded syntactic return type — no type
inference beyond that, D7); (2) public enums inventory their variants as
named slots (`AdapterError::Io`-style demand paths now resolve); (3) the
blanket impl-block `unsupported-construct` gap is replaced by per-construct
accounting (type-qualified pub method slots, named gaps for trait impls and
`pub(crate)` items, impl bodies now walked instead of silently skipped).
Re-audit `results/adopt-audit-158-1.txt` vs
`results/adopt-audit-cdp4-1841.txt`, honestly:

- **Verdicts unchanged: still 12/12 abstained** (refuse/Unknown, exit 1);
  determinism pass. Abstention persists because testaruda's inventory stays
  incomplete — expected per the brief ("abstention count MAY still be >0").
- **Categories cleared:** enum-variant demand gaps (`AdapterError::Io`,
  `AdapterIO::spawn_in`) now resolve as supported demand against named
  variant slots; impl-method slots are type-qualified (the prior run's
  duplicate `adapter::new`-style colliding slots are gone); bounded-receiver
  method calls resolve. The blanket "method implementations are outside the
  supported profile" gap is gone (0/12 pairs carry it).
- **Diagnostic volume grew** (0.5.5: 81→414 incomplete-demand,
  26→24 unsupported-construct; 0.1.0: ~219/17) — this is disclosure
  expansion, not regression: per-construct accounting walks impl bodies that
  were previously silently skipped, and same-crate optimistic recording
  names previously-invisible std/prelude references (`std::io::Error::new`,
  `Vec::new`, `json!`, `miette!`). The residual blockers, in order:
  (1) method calls on non-bounded receivers (locals, literals, std objects —
  needs real type inference, D7 follow-up threshold), (2) std/third-party
  references outside the supplied bundle, (3) trait impls (named gaps),
  (4) non-scalar signature fns (signature subset unchanged, D4).
- Finding for rung 2: the demand profile is now honest per construct; the
  abstention rate is carried by std-awareness (a profile for bundling std
  signatures or declaring trusted external crates) and variable-receiver
  type inference — both deliberate follow-up tickets, not silent relaxations.

**Rung 2 — shadow: publish contracts, report verdicts, gate nothing.**
Each tool's release workflow runs `wild extract` on the release tree and
publishes a contract bundle (v1 extraction artifacts) next to the binary
(GitHub release asset or a compatibility.json-style pages path). Two binding
requirements the convention must carry:
- **Artifact-digest stamping (required):** release CI extracts from the exact
  tree it builds and stamps the published artifact sha256 into the bundle;
  ddl refuses a bundle whose stamped digest ≠ the candidate's sha256. Without
  this, a source-extracted contract could ride along with a binary built from
  different bytes — the trust model must stay digest-bound end to end.
- **Base-contract caching:** the *installed* tool's contract is supplied by
  caching the bundle at install time and recording the contract digest in the
  lock entry; a missing base contract (pre-rung-2 installs, older releases) is
  Unknown with a named diagnostic, never a fabricated base.

Rollout: pilot one tool end-to-end (publish → fetch → verdict) before the
fleet-wide release.yml edits — the publish step is a per-repo PR needing an
owner in ~12 repos.

`ddl upgrade` fetches the candidate bundle, runs `wild check`
candidate-vs-installed-base, and renders the verdict beside the existing
semver/age decision — advisory. This rung measures real gap rates (how often
verdicts are Unknown because the extractor can't see something) *before*
anything gates on them.

**Rung 3 — gate: verdict-driven upgrades, auto-update becomes possible.**
`upgrade_decision` consults the wild verdict: accept → proceed (release-age
cooldown stays — supply-chain cooldown is orthogonal to interface
compatibility), unknown → defer with diagnostics (current behavior, honestly
labeled), reject → block. Nothing is replaced — there is no automated semver
gate to rip out; wild is the first one. `versions.ddl.toml` / compatibility.json become
attestation metadata only. Once the accept path is trusted, `ddl upgrade --auto`
(scheduled) becomes defensible: the thing that made pins conservative —
unmeasured compatibility — is now measured. Cross-tool obligations (e.g. wai's
managed-block markers, testaruda config schema) go into obligations docs;
accepted-state obligations gate transitions per wild-tiers.

**Rung 4 — native: rolling releases.** Tools release freely without
coordinate-semver discipline; the fleet lock advances through contract-checked
automation; version strings remain as names/attestation inputs only. Requires
the wild-registry append-only verdict log for the auto-update audit trail, and
attestation for unattended updates (live reports must be attributable — the
unikernel-cd finding generalizes).

## Coverage honesty (per tool)

| Tool | Structural extraction | Path |
| --- | --- | --- |
| wai (wai-cli), testaruda, dont (dont-cli), pretender, vampiro, specodelic, turu (whisper-vibes), ah (espectacular), incitaciones, funkalization, ddl, wild | rust-cargo-local-1 (bounded) | extract + laws |
| openspec (npm/TS) | none | authored laws only; gate last |
| bd (GitHub binary, no crate) | none (no vendored source path yet) | authored laws only; gate last |

All 12 managed tools covered; the first row's crates are confirmed in
ddl's `src/platform.rs` MANAGED_TOOLS registry (crate_name per row).

Every refusal stays a refusal: a tool with no evidence path keeps its semver
gate and is disclosed as uncovered — never a silent pass.

## Risks / open questions

- **Unknown-heavy verdicts** are likely at rung 2 (async/tokio surface, clap
  derive, trait objects). That is the point of shadow — but gate timing must be
  decided from measured rates, not optimism.
- **Rollback/downgrade interplay is an open question.** Auto-update can still
  regress runtime behavior no contract captures, and ddl's lock has no
  documented rollback semantics with respect to verdicts. Candidate answer:
  rollbacks reuse the same check (a downgrade is just another candidate) plus
  the registry log for the audit trail. Must be resolved before `--auto`.
- **Who maintains obligations and laws?** The consumer-update-assistant design
  (`.wai/projects/software-updates/designs/2026-10-07-consumer-update-assistant.md`)
  already answered: agents mine/draft, humans accept; accepted-state obligations
  are the protected surface.
- **bootstrap paradox:** ddl checks wild, wild ships contracts extracted by
  itself. Self-check first is the cheapest rung-1 corpus anyway (dogfooding all
  the way down).
- Release-age policy (DDL-5bs) is a supply-chain control, not a compatibility
  control — do not collapse them.

## Suggested first slices

1. **Rung 1 audit ticket** (research): replay one well-changelog'd tool's
   release history (wai-cli or testaruda) through extract + consecutive-release
   verdicts; audit declared bump vs computed verdict; write up disagreements.
2. **Rung 0 ticket**: add wild to ddl's MANAGED_TOOLS + registry drift test.
3. **Rung 2 design**: contract-bundle artifact convention + publish step +
   ddl shadow-report path (openspec change; design lane before code).

Each rung's evidence gates the next; nothing here changes the release process
before rung 3, per wild.adopt's own constraint. Exit criteria per rung:

- **Rung 1 exit:** audit artifact published; disagreements (declared bump vs
  computed verdict) enumerated for the pilot tool; extractor gap list extracted
  from the corpus.
- **Rung 2 exit:** N consecutive releases shadowed for ≥1 tool with verdict
  distribution (accept/unknown/reject) recorded; zero false-block complaints;
  stamping/base-caching verified in ddl's tests.
- **Rung 3 exit:** M auto-accepted upgrades with no runtime breakage
  attributed; rollback path exercised at least once.
- **Rung 4 entry:** registry log live and attestation for unattended updates
  resolved (see risks).
