## ADDED Requirements

### Requirement: Openness defaults open in IR v2

In IR schema version 2, a record or sum SHALL treat `open` as optional and SHALL resolve an omitted `open` to open (true); v1 contracts SHALL keep the v1 semantics (explicit `open`, closed-by-convention in authoring, checker fallback `false`) and SHALL NOT be reinterpreted, re-hashed, or re-verdicted. Effective openness SHALL be resolved per contract version before any polarity rule applies, and canonical form SHALL materialize the effective value so identity stays content-addressed.

#### Scenario: Omitted open resolves open in v2

- **GIVEN** a v2 contract record or sum that omits the `open` field
- **WHEN** an accretion or subtyping check resolves its openness
- **THEN** the effective openness is open and the canonical form materializes `open: true`

#### Scenario: V1 contracts are untouched by the default change

- **GIVEN** an existing v1 contract with explicitly declared `open` values
- **WHEN** the tool is upgraded to understand v2
- **THEN** the v1 contract's revision hash, canonical form, and all prior verdicts are unchanged

#### Scenario: Cross-version check resolves each side by its own version

- **GIVEN** a v2 candidate checked against a v1 ancestor in one lineage
- **WHEN** openness is resolved for the polarity rules
- **THEN** each contract's effective openness uses its own version's default and no ambiguity is silently assumed

### Requirement: Closure carries a justification

In IR schema version 2, a record or sum declared with `open: false` SHALL carry a non-empty `closed_reason` string; a closed declaration without one SHALL be rejected with a named diagnostic and SHALL never be silently accepted. The reason SHALL be part of the canonical form and SHALL be immutable within its lineage. v1 closed declarations SHALL NOT be required to carry a reason.

#### Scenario: Unjustified closure rejected

- **GIVEN** a v2 contract record or sum with `open: false` and no `closed_reason`
- **WHEN** the contract is checked or published
- **THEN** it is rejected with the named diagnostic for unjustified closure

#### Scenario: Justified closure keeps the break rules

- **GIVEN** a v2 record or sum with `open: false` and a non-empty `closed_reason`
- **WHEN** a closed output sum grows, opens, or becomes unrestricted
- **THEN** the existing polarity rules apply unchanged: the change is a break and must start a new lineage

#### Scenario: Editing a closure justification is a break

- **GIVEN** a published v2 revision with a record or sum declared `open: false` and a non-empty `closed_reason`
- **WHEN** a candidate changes only that `closed_reason` text (or flips `open`)
- **THEN** the candidate is not an accretion — the change is a break and must start a new lineage, because `closed_reason` is part of the canonical form and immutable within its lineage
