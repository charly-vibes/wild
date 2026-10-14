# Unikernel CD investigation

Research question: how does wild-deploy's gate/lineage/rollback model map onto unikernel continuous deployment, where every deploy is a fresh whole-world composition?

Start with the [mapping research artifact](research/2026-10-14-unikernel-cd-mapping-wild-deploy-onto-a-compose.md), grounded in Geoffrey Huntley's unikernels piece (ghuntley.com/unikernels, conversation with Justin Cormack) and `prototype/wild_cd_sim.py` measurements.

Headline findings so far:

1. **Checking moves from deploy-time to compose-time.** Every deploy rebuilds the full component closure, so `wild check` runs over the entire graph per deploy. At bench-D costs (100k slots: 100 ms full, 0.12 ms Merkle diff) that is effectively free.
2. **Checked lockstep is a third deploy strategy** the spec doesn't name: atomically swapping a fleet built against one checked composition removes the ordering problem that `gate_order_derived` solves by derivation. wild's contract checking is what makes the deployment model that eliminates wild's deploy ordering viable.
3. **The irreducible compatibility surface is the data plane.** Compute images become stateless; floors, accretion, tombstones, and irreversible-write barriers migrate to the storage contract (S3-backed actor-state evolution). Compute rollback becomes always-safe.
4. **Fail-closed gets stronger.** No shell means no ad-hoc verification; live reports must be image-hash-signed protocol emissions into the append-only registry.

Three gaps are identified: a composition-level gate (image-level certificate), boot-time attestation as the report source, and storage-plane contract extraction in `wild extract`.

Beads owns task status:

| ID | Scope |
| --- | --- |
| wild-wsz | Research epic |
| wild-5gb | Unikernel-parameterized CD sim variant (hypothesis: lead-time gap narrows, data-plane impact gap widens) |
| wild-m8c | Composition-certificate prototype (whole-graph check + Merkle) |
| wild-3yy | Functor-signature extraction pilot on a MirageOS unikernel |

The project is in WAI's research phase. No normative spec or runtime behavior is changed here; any spec movement (e.g. a `compose` gate in wild-deploy) would go through openspec separately.
