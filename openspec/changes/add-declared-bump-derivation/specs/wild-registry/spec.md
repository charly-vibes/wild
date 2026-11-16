## ADDED Requirements

### Requirement: Declared bump class is derived from the corpus delta

The system SHALL satisfy `declared_bump_derived` as defined in the Constraints table and the v1 format reference.

#### Scenario: Accretion-only delta proposes minor

- **GIVEN** a computable base release corpus and a candidate tree whose corpus delta contains only ADDED requirements
- **WHEN** the declared-bump derivation runs
- **THEN** the proposed class is minor with reason `accretes` and no requirement was modified or removed

#### Scenario: Revocation proposes major

- **GIVEN** a corpus delta containing at least one MODIFIED or REMOVED requirement
- **WHEN** the declared-bump derivation runs
- **THEN** the proposed class is major with reason `revokes`

#### Scenario: Empty corpus delta proposes patch

- **GIVEN** a computable base and a candidate whose corpus delta changes no requirement
- **WHEN** the declared-bump derivation runs
- **THEN** the proposed class is patch and no accretion or revocation reason is claimed

#### Scenario: Missing base corpus is Unknown, never fabricated

- **GIVEN** no computable base corpus for the candidate tree
- **WHEN** the declared-bump derivation runs
- **THEN** the outcome is Unknown with a named diagnostic and no bump class is proposed

### Requirement: Bump override is upward-only

The system SHALL satisfy `bump_override_upward_only` as defined in the Constraints table and the v1 format reference.

#### Scenario: Raising the class records a reason

- **GIVEN** a proposed class lower than major
- **WHEN** the maintainer confirms an override to a higher class with a recorded reason
- **THEN** the confirmed class is the higher class and the reason is carried on the declared-claim record

#### Scenario: Lowering is refused and the proposal stands

- **GIVEN** a proposed major class
- **WHEN** the maintainer attempts to confirm a lower class
- **THEN** the confirmation is refused with the named diagnostic `bump_class_lowering_refused` and the proposed class stands as the confirmed claim
