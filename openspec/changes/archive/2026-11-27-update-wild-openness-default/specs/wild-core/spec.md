## ADDED Requirements

### Requirement: Openness defaults open

In the v1 wire format, a record or sum SHALL treat `open` as optional and SHALL resolve an omitted `open` to open (true); the reader SHALL resolve the effective value before any polarity rule applies, and the checker's openness fallback SHALL be open. An omitted `open` and an explicit `open: true` SHALL serialize differently and land as distinct revision ids, and SHALL accrete each other as semantically equal.

#### Scenario: Omitted open resolves open

- **GIVEN** a contract record or sum that omits the `open` field
- **WHEN** an accretion or subtyping check resolves its openness
- **THEN** the effective openness is open

#### Scenario: Omitted open and explicit true are distinct ids that accrete

- **GIVEN** two contracts differing only in that one omits `open` and the other writes `open: true`
- **WHEN** both are canonicalized and hashed, and then checked against each other
- **THEN** their revision ids differ and the accretion check between them succeeds

#### Scenario: Explicit declarations keep their semantics

- **GIVEN** a contract with explicitly declared `open` values
- **WHEN** the checker resolves its openness
- **THEN** the declared values are used exactly as before the default change

### Requirement: Closure carries a justification

A record or sum declared with `open: false` SHALL carry a non-empty `closed_reason` string; a closed declaration without one SHALL be rejected with a named diagnostic and SHALL never be silently accepted. The reason SHALL be part of the canonical form and SHALL be immutable within its lineage; any change to a record or sum's `open` value or `closed_reason` text SHALL be a break.

#### Scenario: Unjustified closure rejected

- **GIVEN** a contract record or sum with `open: false` and no `closed_reason`
- **WHEN** the contract is checked or published
- **THEN** it is rejected with the named diagnostic for unjustified closure

#### Scenario: Justified closure keeps the break rules

- **GIVEN** a record or sum with `open: false` and a non-empty `closed_reason`
- **WHEN** a closed output sum grows, opens, or becomes unrestricted
- **THEN** the existing polarity rules apply unchanged: the change is a break and must start a new lineage

#### Scenario: Editing a closure justification is a break

- **GIVEN** a published revision with a record or sum declared `open: false` and a non-empty `closed_reason`
- **WHEN** a candidate changes only that `closed_reason` text (or flips `open`)
- **THEN** the candidate is not an accretion — the change is a break and must start a new lineage, because `closed_reason` is part of the canonical form and immutable within its lineage
