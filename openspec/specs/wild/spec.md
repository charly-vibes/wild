---
id: spec
kind: intent
statement: THE wild SHALL let software components, first-party or third-party, be composed on machine-checked contracts, so that compatibility is determined autonomously and verifiably instead of asserted by version numbers.
---

# Wild

Umbrella spec. Contracts form a category: objects are contract revisions, morphisms are accretions (provides grow, requires shrink), and breaks cross lineages through adapters. Assemblies of components compose on top of that category and yield a certificate any independent verifier can re-check. The other specs refine one concern each: `wild.core` (contracts and accretion), `wild.tiers` (verdict pipeline), `wild.compose` (assemblies, resolution, certificates), `wild.registry` (log, ownership, lock), `wild.bridge` (adapters, overlays, third parties), `wild.adopt` (brownfield adoption), `wild.deploy` (rollout), `wild.extract` (extractors and law harness).

## Constraints

| id | kind | expr | traces_to |
| -- | ---- | ---- | --------- |
| compatibility_computed | invariant | `no compatibility verdict is derived from a version string; version strings are metadata and attestation input only` | [[spec]] |
| decision_autonomous | invariant | `given contracts and demand, the composition verdict is computed without human input; human judgment enters only as attestation` | [[spec]] |
| decision_verifiable | invariant | `every composition verdict ships a certificate that an independent verifier can re-check` | [[spec]] |
| offline_verifiable | invariant | `verification needs only the certificate and content-addressed contracts: no network and no registry write access` | [[spec]] |
| language_blind | invariant | `the core operates on the Contract IR only; ecosystem knowledge lives in extractors` | [[spec]] |
| category_structure | invariant | `contracts with accretions, and assemblies with composition, obey the category laws; verdict logic relies on those laws only` | [[spec]] |
| honest_scope | invariant | `a verdict states its tier and its coverage and never claims more than was checked` | [[spec]] |
| no_silent_downgrade | invariant | `when coverage drops (an uncontracted dependency appears, an attestation expires), the verdict drops with it` | [[spec]] |
| checker_versioned | invariant | `every recorded verdict names the checker version; changing the checker never rewrites an existing verdict` | [[spec]] |
| output_envelope | invariant | `every command emits a JSON envelope with tier, verdict, and slot ids; the human rendering is derived from it` | [[spec]] |
| honest_verdict_labels | invariant | `a verdict names the highest tier passed; the bare word compatible is never emitted` | [[spec]] |
| open_world_disclosed | advisory | `every report lists known consumers and states that undeclared consumers are not covered` | [[spec]] |

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
| resolve | requested | resolved | [[spec.decision_autonomous]] ∧ [[spec.compatibility_computed]] |
| certify | resolved | certified | [[spec.decision_verifiable]] |
| verify | certified | verified | [[spec.offline_verifiable]] ∧ [[spec.checker_versioned]] |
| refuse_unresolved | requested | refused | [[spec.honest_scope]] |
| refuse_stale | resolved | refused | [[spec.no_silent_downgrade]] |
| refuse_invalid | certified | refused | [[spec.honest_scope]] |

## Properties

| id | kind | derives_from | generator | predicate |
| -- | ---- | ------------ | --------- | --------- |
| version_string_never_decides | unit | [[spec.compatibility_computed]] | `release_labelled_patch_that_removes_a_slot()` | `verdict == Reject regardless of label` |
| verdict_needs_no_human | unit | [[spec.decision_autonomous]] | `contracts_and_demand()` | `compute(c, d) completes with no interactive input` |
| verdict_has_certificate | unit | [[spec.decision_verifiable]] | `arbitrary_composition_verdict()` | `certificate present ∧ verify(certificate) == verdict` |
| verification_is_offline | unit | [[spec.offline_verifiable]] | `verify_with_network_and_registry_disabled()` | `verify(certificate) completes` |
| core_has_no_ecosystem_imports | unit | [[spec.language_blind]] | `core_module_dependency_graph()` | `no dependency edge to any extractor` |
| category_laws_hold | law | [[spec.category_structure]] | `arbitrary_contract_chain(length: 3)` | **identity:** `compose(id, f) == f` **associativity:** `compose(compose(f, g), h) == compose(f, compose(g, h))` |
| verdict_states_its_scope | unit | [[spec.honest_scope]] | `arbitrary_verdict()` | `verdict has tier ∧ coverage` |
| lost_coverage_lowers_verdict | unit | [[spec.no_silent_downgrade]] | `assembly_gaining_an_uncontracted_dependency()` | `verdict(after) < verdict(before)` |
| verdict_names_checker | unit | [[spec.checker_versioned]] | `verdict_recorded_then_checker_upgraded()` | `recorded.checker == old ∧ recorded unchanged` |
| envelope_matches_human | unit | [[spec.output_envelope]] | `arbitrary_check_result()` | `parse(render_human(r)) agrees with envelope(r)` |
| bare_compatible_never_emitted | unit | [[spec.honest_verdict_labels]] | `arbitrary_passing_result()` | `output names the highest tier passed ∧ not equals "compatible"` |
| unknown_consumers_disclosed | unit | [[spec.open_world_disclosed]] | `report_with_known_consumers([a, b])` | `report states undeclared consumers are not covered` |

## Notes

Value proposition: determine composition across modules, components, and packages, first or third party, autonomously and verifiably. Autonomy comes from computing verdicts over contracts; verifiability from certificates re-checked offline by a separate verifier; the category structure is what lets verdicts compose (transitivity of accretion, associativity of assembly composition).

What the evidence says (toy simulations with assumed parameters, not data about real registries): the accretion relation needed four rule fixes before it passed exhaustive reflexivity and transitivity checks; with truthful labels, lineage resolution and semver-with-duplicates coincide, so the gain is machine-checked labels; undeclared behavior stays the weak spot and is only reached through laws and evidence. These limits are why `honest_scope` and `open_world_disclosed` exist.

## Requirements

The spec corpus SHALL stay lint-clean and reference-closed, so every constraint, property, and model row in the corpus remains checkable by the specodelic toolchain.

#### Scenario: Spec corpus stays lint-clean and reference-closed
- **GIVEN** the dual-format corpus under `openspec/specs`
- **WHEN** `spk lint openspec` and `specodelic graph openspec` run
- **THEN** lint reports no issues and no warnings across all nine files
- **AND** the reference graph reports no dangling references
- **AND** the gate executes this behavior as a declared contract test

The three ecosystem gates (ah, pretender, testaruda) SHALL be wired as hard gates, so quality checks are machine-enforced rather than advisory.

#### Scenario: Gates wired and standard true
- **GIVEN** the wired gate configs (`.espectacular/config.toml`, `justfile`, `lefthook.yml`, `pretender.toml`, `testaruda.toml`)
- **WHEN** the wiring gate runs `ah check`, `pretender check`, `spk lint openspec`, and `testaruda select --safe`
- **THEN** the three gate configs exist on disk and parse clean
- **AND** they carry the standard sections and follow the hardcoded-gate pattern
- **AND** the openspec spec corpus is lint-clean and reference-closed
- **AND** the gated tests run clean
- **AND** the gate executes this behavior as a declared contract test
