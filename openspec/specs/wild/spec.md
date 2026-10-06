---
id: spec
kind: intent
statement: THE wild SHALL let software components, first-party or third-party, be composed on machine-checked contracts, so that compatibility is determined autonomously and verifiably instead of asserted by version numbers.
---

# Wild

## Purpose

This is a normative design specification; only the prototype and corpus gate scenarios explicitly identified below are implemented. Shared wire formats and decision rules are defined in [wild v1 formats](../../../docs/wild-formats-v1.md) and [the v1 schema](../../../schemas/wild-v1.schema.json).

Umbrella spec. Contracts form a category: objects are contract revisions, morphisms are accretions (provides grow, requires shrink), and breaks cross lineages through adapters. Assemblies of components compose on top of that category and yield a certificate any independent verifier can re-check. The other specs refine one concern each: `wild.core` (contracts and accretion), `wild.tiers` (verdict pipeline), `wild.compose` (assemblies, resolution, certificates), `wild.registry` (log, ownership, lock), `wild.bridge` (adapters, overlays, third parties), `wild.adopt` (brownfield adoption), `wild.deploy` (rollout), `wild.extract` (extractors and law harness).

## Constraints

| id | kind | expr | traces_to |
| -- | ---- | ---- | --------- |
| compatibility_computed | invariant | `no compatibility verdict is derived from a version string; version strings are metadata and attestation input only` | [[spec]] |
| decision_autonomous | invariant | `given contracts and demand, the composition verdict is computed without human input; human judgment enters only as attestation` | [[spec]] |
| decision_verifiable | invariant | `every composition verdict ships a certificate that an independent verifier can re-check` | [[spec]] |
| offline_verifiable | invariant | `verification uses the v1 certificate bundle and caller-supplied assembly commitment, policy, trust roots, and evaluation time defined in docs/wild-formats-v1.md; no network or registry write access` | [[spec]] |
| language_blind | invariant | `the core operates on the Contract IR only; ecosystem knowledge lives in extractors` | [[spec]] |
| category_structure | invariant | `contract accretion is reflexive and transitive; assembly composition is a partial operation on compatible, explicitly identified interfaces and obeys identity and associativity wherever defined` | [[spec]] |
| honest_scope | invariant | `a verdict states its tier and its coverage and never claims more than was checked` | [[spec]] |
| no_silent_downgrade | invariant | `lost coverage cannot increase assurance; expired attestations cease satisfying attestation policy without erasing independently valid structural or law results` | [[spec]] |
| checker_versioned | invariant | `every recorded verdict names the checker version; changing the checker never rewrites an existing verdict` | [[spec]] |
| output_envelope | invariant | `every command emits the v1 JSON envelope with assurance, decision, tier_reports, slots, coverage, checker, and disclosed consumers; the human rendering is derived from it` | [[spec]] |
| honest_verdict_labels | invariant | `a verdict names structural assurance, law method, evidence scope, and attestation policy result; the bare word compatible is never emitted` | [[spec]] |
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
| verdict_states_its_scope | unit | [[spec.honest_scope]] | `arbitrary_verdict()` | `verdict has structural assurance, law methods, evidence scope, attestation status, and coverage` |
| lost_coverage_lowers_verdict | unit | [[spec.no_silent_downgrade]] | `assembly_gaining_an_uncontracted_dependency()` | `coverage(after) < coverage(before) ∧ assurance(after) ≤ assurance(before)` |
| verdict_names_checker | unit | [[spec.checker_versioned]] | `verdict_recorded_then_checker_upgraded()` | `recorded.checker == old ∧ recorded unchanged` |
| envelope_matches_human | unit | [[spec.output_envelope]] | `arbitrary_check_result()` | `parse(render_human(r)) agrees with envelope(r)` |
| bare_compatible_never_emitted | unit | [[spec.honest_verdict_labels]] | `arbitrary_passing_result()` | `output names structural assurance, law method, and evidence scope ∧ not equals "compatible"` |
| unknown_consumers_disclosed | unit | [[spec.open_world_disclosed]] | `report_with_known_consumers([a, b])` | `report states undeclared consumers are not covered` |

## Notes

Value proposition: determine composition across modules, components, and packages, first or third party, autonomously and verifiably. Autonomy comes from computing verdicts over contracts; verifiability from certificates re-checked offline by a separate verifier; the category structure is what lets verdicts compose (transitivity of accretion, associativity of assembly composition).

What the evidence says (toy simulations with assumed parameters, not data about real registries): the accretion relation needed four rule fixes before it passed exhaustive reflexivity and transitivity checks; with truthful labels, lineage resolution and semver-with-duplicates coincide, so the gain is machine-checked labels; undeclared behavior stays the weak spot and is only reached through laws and evidence. These limits are why `honest_scope` and `open_world_disclosed` exist.

## Design acceptance cases

These cases define future runtime behavior. They are not claims that the current prototypes implement the v1 protocol. Executable document and prototype gates are under Requirements.

### Rule: Compatibility computed

The system SHALL satisfy `compatibility_computed` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Version string never decides
- **GIVEN** the fixture domain `release_labelled_patch_that_removes_a_slot()`
- **WHEN** the `compatibility_computed` check runs
- **THEN** `verdict == Reject regardless of label`

### Rule: Decision autonomous

The system SHALL satisfy `decision_autonomous` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Verdict needs no human
- **GIVEN** the fixture domain `contracts_and_demand()`
- **WHEN** the `decision_autonomous` check runs
- **THEN** `compute(c, d) completes with no interactive input`

### Rule: Decision verifiable

The system SHALL satisfy `decision_verifiable` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Verdict has certificate
- **GIVEN** the fixture domain `arbitrary_composition_verdict()`
- **WHEN** the `decision_verifiable` check runs
- **THEN** `certificate present ∧ verify(certificate) == verdict`

### Rule: Offline verifiable

The system SHALL satisfy `offline_verifiable` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Verification is offline
- **GIVEN** the fixture domain `verify_with_network_and_registry_disabled()`
- **WHEN** the `offline_verifiable` check runs
- **THEN** `verify(certificate) completes`

### Rule: Language blind

The system SHALL satisfy `language_blind` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Core has no ecosystem imports
- **GIVEN** the fixture domain `core_module_dependency_graph()`
- **WHEN** the `language_blind` check runs
- **THEN** `no dependency edge to any extractor`

### Rule: Category structure

The system SHALL satisfy `category_structure` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Category laws hold
- **GIVEN** the fixture domain `arbitrary_contract_chain(length: 3)`
- **WHEN** the `category_structure` check runs
- **THEN** **identity:** `compose(id, f) == f` **associativity:** `compose(compose(f, g), h) == compose(f, compose(g, h))`

### Rule: Honest scope

The system SHALL satisfy `honest_scope` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Verdict states its scope
- **GIVEN** the fixture domain `arbitrary_verdict()`
- **WHEN** the `honest_scope` check runs
- **THEN** `verdict has structural assurance, law methods, evidence scope, attestation status, and coverage`

### Rule: No silent downgrade

The system SHALL satisfy `no_silent_downgrade` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Lost coverage lowers verdict
- **GIVEN** the fixture domain `assembly_gaining_an_uncontracted_dependency()`
- **WHEN** the `no_silent_downgrade` check runs
- **THEN** `coverage(after) < coverage(before) ∧ assurance(after) ≤ assurance(before)`

### Rule: Checker versioned

The system SHALL satisfy `checker_versioned` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Verdict names checker
- **GIVEN** the fixture domain `verdict_recorded_then_checker_upgraded()`
- **WHEN** the `checker_versioned` check runs
- **THEN** `recorded.checker == old ∧ recorded unchanged`

### Rule: Output envelope

The system SHALL satisfy `output_envelope` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Envelope matches human
- **GIVEN** the fixture domain `arbitrary_check_result()`
- **WHEN** the `output_envelope` check runs
- **THEN** `parse(render_human(r)) agrees with envelope(r)`

### Rule: Honest verdict labels

The system SHALL satisfy `honest_verdict_labels` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Bare compatible never emitted
- **GIVEN** the fixture domain `arbitrary_passing_result()`
- **WHEN** the `honest_verdict_labels` check runs
- **THEN** `output names structural assurance, law method, and evidence scope ∧ not equals "compatible"`

### Rule: Open world disclosed

The system SHALL satisfy `open_world_disclosed` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Unknown consumers disclosed
- **GIVEN** the fixture domain `report_with_known_consumers([a, b])`
- **WHEN** the `open_world_disclosed` check runs
- **THEN** `report states undeclared consumers are not covered`

#### Acceptance case: Historical certificate does not authorize current use
- **GIVEN** an attestation was valid at certificate creation but is now expired
- **WHEN** the caller requests current verification with the later evaluation time
- **THEN** historic checks remain immutable and current attestation policy refuses

## Requirements

### Requirement: Spec corpus integrity

The spec corpus SHALL stay lint-clean and reference-closed, so every constraint, property, and model row in the corpus remains checkable by the specodelic toolchain.

#### Scenario: Spec corpus stays lint-clean and reference-closed
- **GIVEN** the dual-format corpus under `openspec/specs`
- **WHEN** `spk lint openspec` and `specodelic graph openspec` run
- **THEN** lint reports no issues and no warnings across all nine files
- **AND** the reference graph reports no dangling references
- **AND** the gate executes this behavior as a declared contract test

### Requirement: Ecosystem gate wiring

The three ecosystem gates (ah, pretender, testaruda) SHALL be wired as hard gates, so quality checks are machine-enforced rather than advisory.

#### Scenario: Gates wired and standard true
- **GIVEN** the wired gate configs (`.espectacular/config.toml`, `justfile`, `lefthook.yml`, `pretender.toml`, `testaruda.toml`)
- **WHEN** the wiring gate runs `ah check`, `pretender check`, `spk lint openspec`, and `testaruda select --safe`
- **THEN** the three gate configs exist on disk and parse clean
- **AND** they carry the standard sections and follow the hardcoded-gate pattern
- **AND** the openspec spec corpus is lint-clean and reference-closed
- **AND** the gated tests run clean
- **AND** the gate executes this behavior as a declared contract test

### Requirement: Wild design contract

The design corpus SHALL expose this capability's constraints as normative, self-contained rules with acceptance cases, and SHALL link to a structurally valid shared v1 schema without claiming future runtime behavior is implemented.

#### Scenario: Wild design is self-contained
- **GIVEN** this spec, `docs/wild-formats-v1.md`, and `schemas/wild-v1.schema.json`
- **WHEN** the design contract gate checks normative rule coverage, local references, and the shared schema
- **THEN** every constraint has a corresponding rule and acceptance case
- **AND** both referenced files exist and the schema is valid JSON Schema draft 2020-12
- **AND** this capability is discoverable by strict OpenSpec validation
