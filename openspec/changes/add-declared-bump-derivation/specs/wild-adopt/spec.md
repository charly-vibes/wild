## ADDED Requirements

### Requirement: Declared bump is recorded for verdict audit

The system SHALL satisfy `declared_bump_recorded` as defined in the Constraints table and the v1 format reference.

#### Scenario: Derived class feeds the audit comparison

- **GIVEN** a release whose declared bump class was derived and confirmed
- **WHEN** the past-claims audit runs
- **THEN** the audit compares the declared class against the computed verdict for that release and lists the agreement or disagreement

#### Scenario: Disagreement is listed, never silently reconciled

- **GIVEN** a declared minor class and a computed revocation verdict for the same release
- **WHEN** the past-claims audit runs
- **THEN** the disagreement is listed in the audit report and neither the declared record nor the computed verdict is rewritten

#### Scenario: Absent declaration stays an Unknown claim

- **GIVEN** a release with no recorded declared bump class
- **WHEN** the past-claims audit runs
- **THEN** the declared claim reports Unknown and is excluded from agreement counts
