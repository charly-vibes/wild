## ADDED Requirements

### Requirement: Absence is declared policy, not violation

The system SHALL satisfy `absence_as_policy` as defined in the Constraints table and the v1 format reference.

#### Scenario: Fallible absence is a handled value outcome

- **GIVEN** a required input slot declaring `on_absent: fallible`
- **WHEN** the input is absent at that slot
- **WHEN** the demand check runs
- **THEN** the outcome records fallible absence for the consumer to handle and no caller-violation refusal is raised

#### Scenario: Clause direction is accretion then break

- **GIVEN** a retained input slot gaining `on_absent: fallible`
- **WHEN** the accretion check runs
- **THEN** gaining the clause accretes and revoking it is a break

#### Scenario: Fallible slots stay in closure validation

- **GIVEN** a substitution whose replacement introduces a new required input near a fallible slot
- **WHEN** the closure validation runs
- **THEN** the new required input is still listed exactly as without the clause
