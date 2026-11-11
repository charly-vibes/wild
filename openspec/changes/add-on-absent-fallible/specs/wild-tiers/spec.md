## ADDED Requirements

### Requirement: Absence surfaces as runtime observation

The system SHALL satisfy `absence_observed_at_runtime` as defined in the Constraints table and the v1 format reference.

#### Scenario: Absence is tier-3 evidence, not a static verdict

- **GIVEN** a slot declared `on_absent: fallible`
- **WHEN** absence of the input is observed by canary or replayed traffic
- **THEN** the absence is recorded as tier-3 scoped evidence while the static verdict kinds and structural results remain unchanged
