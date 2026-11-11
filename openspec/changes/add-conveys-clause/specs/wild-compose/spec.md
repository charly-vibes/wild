## ADDED Requirements

### Requirement: Conveyance forwards uninterpreted input

The system SHALL satisfy `conveys_forwarding_scoped` as defined in the Constraints table and the v1 format reference.

#### Scenario: Conveyed slot is claimed, not rejected

- **GIVEN** a pass-through contract declaring a `conveys` clause over declared input paths
- **WHEN** extraction meets an unknown input slot at a declared path
- **THEN** the verdict records a conveyance claim scoped to the declared paths and no demand refusal for that slot

#### Scenario: Undeclared unknown slot is still refused

- **GIVEN** a contract without a `conveys` clause covering a given path
- **WHEN** extraction meets an unknown input slot at that path
- **THEN** the current refusal for unextracted demand is preserved

#### Scenario: Conveyance never hides newly introduced required inputs

- **GIVEN** a scoped substitution whose replacement introduces a new required input under a conveyed path
- **WHEN** the `scoped_substitution` check runs
- **THEN** the refusal lists the newly introduced required input exactly as without the clause
