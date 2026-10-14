---
tags: [unikernel-cd, research]
---

# Unikernel CD: mapping wild-deploy onto a compose-replace world

## Source

Geoffrey Huntley, "unikernels were hard. key word: were." (ghuntley.com/unikernels, 11 Oct 2026) — conversation with Justin Cormack (MirageOS). Key claims extracted below.

Claim status in this document follows the sim's discipline: MEASURED = output of a run of `prototype/wild_cd_sim.py` (this session, 2026-10-14), CITED = from the article, ASSUMED = reviewer assumption stated as a parameter, ARGUED = inference requiring its stated premises.

## Article claims relevant to wild

1. **Unikernels = app is the OS.** No userland, no shell; everything (TCP, DNS, storage) is a library composed into one image. MirageOS functors are the composition mechanism.
2. **The blocker was missing libraries, not the idea.** Agents + a golden oracle (mkfs.xfs in Rust, byte-identical output) make porting a loop, not a project.
3. **The OS is design debt / attack surface.** No shell means "nothing in the model weights knows what to do next" — drive-by RCE stops yielding a foothold.
4. **Breaking changes are no longer taboo.** Ship the breaking change with a skill pack; agents auto-migrate. (Python 2→3 rule retired.)
5. **Patch the world via overlays/first-party source.** Agents treat dependencies as source, not bundled binaries.
6. **Storage is S3-shaped.** turbopuffer model: S3 as primary, local NVMe cache. Huntley's "Spaceleans" (Orleans ported to OCaml as unikernels) rehydrates actor state from pluggable storage.
7. **Back pressure is compile time.** Rust contention across parallel agents is the tax; fast iteration wins.

## The structural shift: checking moves from deploy-time to compose-time

Every unikernel deploy rebuilds and replaces a whole world (Nix-style fresh composition). There is no in-place patching and no shared staging. This relocates wild's center of gravity:

| | Classic CD (wild-deploy today) | Unikernel CD |
| --- | --- | --- |
| Unit of deploy | one service revision | whole image = full component closure |
| When `wild check` runs | CI on a diff, per service | at image composition, over the entire graph, per deploy |
| Registry role | published revisions, append-only | content-addressed store of contract-certified components (Nix store + certificate) |
| Ordering | derived topological gate across services | mostly collapses (hypothesis — requires lease-based coordination; see the checked-lockstep reconciliation below and open question 1) |
| Rollback | floor-respecting, barrier-aware | free for compute; lives only in the data plane |

Checker-cost evidence (prototype/wild_cd_sim.py bench D, MEASURED, toy Python): 100k slots = 100.7 ms full check, 0.123 ms two-level Merkle diff, 0.0012 ms cache hit. A full-fleet composition check per deploy is effectively free at these costs. What is prohibitive at deploy-time per-service granularity amortizes into an image build.

## What collapses in wild-deploy's state machine

- **rolling_overlap_safe** becomes nearly free: Firecracker-class microVMs boot in ~100 ms (ASSUMED; Firecracker's own docs advertise ~125 ms startup), so the roll window shrinks from minutes to seconds. Scenario A's 198k failed requests (break, uncoordinated) become a transport-level rounding error. The failures that matter move to the data plane.
- **gate_order_derived** mostly collapses (ARGUED — the reconciliation below is a hypothesis, not a result) — a unikernel fleet can swap the entire fleet built against one checked composition. That is lockstep release, which the spec refuses for unsatisfied prerequisite cycles, made safe by machine-checked composition. Key framing: wild's contract checking is what makes the deployment model that eliminates wild's deploy *ordering* viable — but not its *coordination*. Nodes restart at staggered times; during the swap window a mixed old/new fleet serves traffic, which is exactly the rolling-overlap condition. Checked lockstep therefore still runs on the spec's coordination lease (provider_live_before_consumer, gate_decision_pure); what collapses is the derived ordering edge set, not the lease machinery. Sim B: random order safe 2.5% baseline vs 8.5% wild; lockstep 5.1% baseline vs 0% wild — the unikernel move is a third strategy: checked lockstep.
- **floor_declared + provider_live_before_consumer** survive in exactly one place: the data plane. Compute images have durable state externalized (they are not stateless — local NVMe caches and in-flight actor memory are state); durable actor state outlives every deploy. Floors, accretion, tombstones, and irreversible_edges_declared migrate from provider services to the storage contract (schema evolution on the S3-backed store; the first-write barrier belongs there). Net simplification: compute rollbacks always safe; only storage evolution carries irreversibility.

## What gets stronger

- **live_state_fresh (fail-closed)** goes from prudent to mandatory: no shell means no ad-hoc verification path. Live reports must be first-class protocol emissions signed by the image revision hash into the append-only registry. gate_decision_pure fits: the control plane can itself be a unikernel.
- **retire_on_zero_demand + lineages_served_concurrently** become cheap: two unikernel images cost ~nothing extra; "break → new lineage + adapter" (Scenario A: zero failures, no calendar penalty) is the unikernel-native pattern made affordable by smallness.
- **Supply chain closes**: each image ships a contract-closure certificate (every component revision + composition verdict) — attack-surface inversion agrees with the article's security thesis from the provenance side.

## Gaps in wild-deploy for this world

1. **Composition-level gate.** Spec gates service revisions against floors; needs a `compose` gate over the full graph emitting one image-level certificate. Pieces exist (per-edge check, Merkle cache) but no composition artifact as deploy unit.
2. **Boot-time attestation as report source.** live_state_fresh assumes a trusted reporter; needs image-hash-signed reports, registry rejects mismatches.
3. **Storage-plane contract extraction.** irreversible_edges_declared is a deploy-time declaration; should derive from the storage provider's contract — `wild extract` needs data-shape contracts, not just call-shape ones, including cache-invalidation contracts (a rolled-back image with a warm NVMe cache can serve stale reads). Extension to wild-core's contract model.

## Observation: MirageOS implements a slice of wild's thesis in the language

OCaml functor signatures are contracts-as-modules, machine-checkable at link time; `wild check` ≈ functor application type-checking. What wild adds beyond the OCaml compiler is the behavioral layer: laws, tiers, accretion relations, tombstones. For a unikernel target, `wild extract` on OCaml gets signatures for free and should spend effort on laws and tombstones. Huntley calling Spaceleans "Erlang-esque" is the same idea — actor protocols are contracts nobody machine-checks across versions.

## Proposed experiments — all three RUN (wild-wsz children, 2026-10-14)

1. **Unikernel-parameterized CD sim — RUN (wild-5gb).** Executed per brief (sections E–H added to wild_cd_sim.py, byte-stable A–D preserved). Results (results/unikernel-cd-sim-2026-10-14.txt): lead-time gap canary-vs-unikernel narrows (p95 15.3h → 2.0h, gap 13.3h); removing data-plane floor logic erases wild's impact-minutes advantage (334 → −264 min/100, floors_residual 598 min/100) — **hypothesis SUPPORTED**, the residual difference isolates the value of floors exactly as predicted. Hybrid fleets (0.0/0.5/1.0 axis) modeled: floor ordering does not collapse in the hybrid case.
2. **Composition-certificate prototype — RUN (wild-m8c).** `prototype/wild_compose.py` emits a whole-graph composition certificate (per-edge verdicts + Merkle root) with an independent proof-carrying verifier (re-derives everything; tamper arms labeled `tampered:<field>`). Measured compose+verify cost over a 4-layer synthetic fleet DAG: 200 svc / 540 edges = 15.4 ms compose, 9.78 ms verify; incremental bump re-checks 7/162 edges in 2.84 ms (changed_leaves 1/222). Compose-time checking over a full fleet DAG is effectively free, closing gap 1's cost question (results/composition-cert-2026-10-14.txt).
3. **Functor-signature extraction pilot — RUN (wild-3yy).** Extracted from mirage-skeleton @ 52abe5a (59 .ml/.mli files): 20 machine-checked signature boundaries (3 module types + 17 functor boundaries over 32 parameters), 9 signature items enforced at every application site, 0 behavioral predicates expressible, 9 unsupported constructs disclosed per-kind (5 `with type`, 4 first-class modules). wild adds 4 mechanism classes per boundary (law slots, accretion relation, tombstone eligibility, artifact-bound evidence) = 68 additions over 17 boundaries — the signature layer is a floor, not the contract (results/functor-pilot-2026-10-14.txt).

## Open questions

- Does checked-lockstep fleet swap actually dominate derived-order rolling for mixed fleets (some services third-party/not unikernelized)? Realistic deployments are hybrids for years.
- How do actor-grain schema contracts relate to wild-core's existing contract shapes — same category, or a new kind?
- Who signs the image↔certificate binding, and does the append-only registry need a new artifact class for compositions (vs revisions)? (Overlaps gap 2 — same binding problem from the report side.)

Measured (functor pilot, mirage-skeleton @ 52abe5a, mirage >= "4.9.0" declared by the repo's own opam file): over 59 .ml/.mli files under tutorial/, applications/, and device-usage/ (lead correction: `example/` does not exist at the pin), the pilot counted 3 module-type definitions (9 signature items), 17 functor boundaries carrying 32 parameter constraints, and 1 module application — 20 machine-checked signature boundaries OCaml enforces for free at link time. 9 constructs the extractor does not interpret are disclosed per-kind (5 `with type` constraints, 4 first-class module package expressions), never dropped. 0 behavioral predicates are expressible anywhere in those signatures; per boundary wild adds 4 mechanism classes the type system cannot express (law slots, accretion relation, tombstone eligibility, artifact-bound evidence) = 68 additions over 17 boundaries. Pilot verdict: the signature layer is a floor, not the contract — OCaml gives the shape checking for free and stops exactly where wild's behavioral layer begins. Evidence: results/functor-pilot-2026-10-14.txt; extractor experiments/functor_pilot.py (gap-disclosing, sorted-walk deterministic, byte-identical repeat runs).

## Status

Research only; no normative spec or runtime behavior changed. Follow-up work tracked under the beads epic.

