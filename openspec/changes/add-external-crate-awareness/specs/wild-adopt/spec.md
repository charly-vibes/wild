## ADDED Requirements

### Requirement: External signature digests are gated at check time

The system SHALL satisfy `external_digest_set_gated` as defined in the Constraints table and the v1 format reference.

#### Scenario: Declared digest set admits the bundle

- **GIVEN** a check request declaring a trusted-digest set that contains the digest of the external signature bundle an extraction consumed
- **WHEN** the check runs
- **THEN** demands recorded with `trusted-external` provenance participate in resolution normally, with their provenance visible in the report

#### Scenario: Undeclared digest refuses trusted-external resolution

- **GIVEN** a check request whose declared trusted-digest set does not contain the digest an extraction's bundle recorded
- **WHEN** the check runs
- **THEN** trusted-external resolution is refused with the named diagnostic `external-signature-digest-untrusted`, the affected demands are treated as incomplete-demand gaps, and the verdict keeps Unknown assurance

#### Scenario: No declared digest set means no trust

- **GIVEN** a check request that declares no trusted-digest set while the extraction bundle consumed external signature summaries
- **WHEN** the check runs
- **THEN** the behavior matches the undeclared-digest refusal and no demand is silently trusted

#### Scenario: Digest set drift is never silently accepted

- **GIVEN** a previously accepted check re-run after the declared trusted-digest set changed without the bundle being re-extracted
- **WHEN** the recorded bundle digest no longer appears in the declared set
- **THEN** the check refuses trusted-external resolution with `external-signature-digest-untrusted` rather than silently accepting either the old or the new trust
