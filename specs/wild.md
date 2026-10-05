---
id: wild
kind: intent
statement: THE wild SHALL let software components, first-party or third-party, be composed on machine-checked contracts, so that compatibility is determined autonomously and verifiably instead of asserted by version numbers.
---

# Wild

Umbrella spec. Contracts form a category: objects are contract revisions, morphisms are accretions (provides grow, requires shrink), and breaks cross lineages through adapters. Assemblies of components compose on top of that category and yield a certificate any independent verifier can re-check. The other specs refine one concern each: `wild.core` (contracts and accretion), `wild.tiers` (verdict pipeline), `wild.compose` (assemblies, resolution, certificates), `wild.registry` (log, ownership, lock), `wild.bridge` (adapters, overlays, third parties), `wild.adopt` (brownfield adoption), `wild.deploy` (rollout), `wild.extract` (extractors and law harness).

## Constraints

| id | kind | expr | traces_to |
| -- | ---- | ---- | --------- |
| compatibility_computed | invariant | `no compatibility verdict is derived from a version string; version strings are metadata and attestation input only` | [[wild]] |
| decision_autonomous | invariant | `given contracts and demand, the composition verdict is computed without human input; human judgment enters only as attestation` | [[wild]] |
| decision_verifiable | invariant | `every composition verdict ships a certificate that an independent verifier can re-check` | [[wild]] |
| offline_verifiable | invariant | `verification needs only the certificate and content-addressed contracts: no network and no registry write access` | [[wild]] |
| language_blind | invariant | `the core operates on the Contract IR only; ecosystem knowledge lives in extractors` | [[wild]] |
| category_structure | invariant | `contracts with accretions, and assemblies with composition, obey the category laws; verdict logic relies on those laws only` | [[wild]] |
| honest_scope | invariant | `a verdict states its tier and its coverage and never claims more than was checked` | [[wild]] |
| no_silent_downgrade | invariant | `when coverage drops (an uncontracted dependency appears, an attestation expires), the verdict drops with it` | [[wild]] |
| checker_versioned | invariant | `every recorded verdict names the checker version; changing the checker never rewrites an existing verdict` | [[wild]] |
| output_envelope | invariant | `every command emits a JSON envelope with tier, verdict, and slot ids; the human rendering is derived from it` | [[wild]] |
| honest_verdict_labels | invariant | `a verdict names the highest tier passed; the bare word compatible is never emitted` | [[wild]] |
| open_world_disclosed | advisory | `every report lists known consumers and states that undeclared consumers are not covered` | [[wild]] |

## Model

### States

- `requested`
- `resolved`
- `certified`
- `verified`
- `refused`

### Transitions

| id | from | to | guard |
| -- | ---- | -- | ----- |
| resolve | requested | resolved | [[wild.decision_autonomous]] ∧ [[wild.compatibility_computed]] |
| certify | resolved | certified | [[wild.decision_verifiable]] |
| verify | certified | verified | [[wild.offline_verifiable]] ∧ [[wild.checker_versioned]] |
| refuse_unresolved | requested | refused | [[wild.honest_scope]] |
| refuse_stale | resolved | refused | [[wild.no_silent_downgrade]] |
| refuse_invalid | certified | refused | [[wild.honest_scope]] |

## Properties

| id | kind | derives_from | generator | predicate |
| -- | ---- | ------------ | --------- | --------- |
| version_string_never_decides | unit | [[wild.compatibility_computed]] | `release_labelled_patch_that_removes_a_slot()` | `verdict == Reject regardless of label` |
| verdict_needs_no_human | unit | [[wild.decision_autonomous]] | `contracts_and_demand()` | `compute(c, d) completes with no interactive input` |
| verdict_has_certificate | unit | [[wild.decision_verifiable]] | `arbitrary_composition_verdict()` | `certificate present ∧ verify(certificate) == verdict` |
| verification_is_offline | unit | [[wild.offline_verifiable]] | `verify_with_network_and_registry_disabled()` | `verify(certificate) completes` |
| core_has_no_ecosystem_imports | unit | [[wild.language_blind]] | `core_module_dependency_graph()` | `no dependency edge to any extractor` |
| category_laws_hold | law | [[wild.category_structure]] | `arbitrary_contract_chain(length: 3)` | **identity:** `compose(id, f) == f` **associativity:** `compose(compose(f, g), h) == compose(f, compose(g, h))` |
| verdict_states_its_scope | unit | [[wild.honest_scope]] | `arbitrary_verdict()` | `verdict has tier ∧ coverage` |
| lost_coverage_lowers_verdict | unit | [[wild.no_silent_downgrade]] | `assembly_gaining_an_uncontracted_dependency()` | `verdict(after) < verdict(before)` |
| verdict_names_checker | unit | [[wild.checker_versioned]] | `verdict_recorded_then_checker_upgraded()` | `recorded.checker == old ∧ recorded unchanged` |
| envelope_matches_human | unit | [[wild.output_envelope]] | `arbitrary_check_result()` | `parse(render_human(r)) agrees with envelope(r)` |
| bare_compatible_never_emitted | unit | [[wild.honest_verdict_labels]] | `arbitrary_passing_result()` | `output names the highest tier passed ∧ not equals "compatible"` |
| unknown_consumers_disclosed | unit | [[wild.open_world_disclosed]] | `report_with_known_consumers([a, b])` | `report states undeclared consumers are not covered` |

## Notes

Value proposition: determine composition across modules, components, and packages, first or third party, autonomously and verifiably. Autonomy comes from computing verdicts over contracts; verifiability from certificates re-checked offline by a separate verifier; the category structure is what lets verdicts compose (transitivity of accretion, associativity of assembly composition).

What the evidence says (toy simulations with assumed parameters, not data about real registries): the accretion relation needed four rule fixes before it passed exhaustive reflexivity and transitivity checks; with truthful labels, lineage resolution and semver-with-duplicates coincide, so the gain is machine-checked labels; undeclared behavior stays the weak spot and is only reached through laws and evidence. These limits are why `honest_scope` and `open_world_disclosed` exist.
