## ADDED Requirements

### Requirement: Typed incomplete-demand disclosure reasons

Every unresolved demand emitted as an incomplete-demand gap SHALL carry a typed reason distinguishing its residual cause — `external-crate-unmodeled`, `std-item`, `unsupported-signature`, `unresolved-receiver`, or `unknown-target` — with the class of each reason defined in this capability's design. The typed reason SHALL NOT change acceptance behavior: every gap keeps refusing scoped acceptance with Unknown structural assurance, and the gap message keeps naming the demand target.

#### Scenario: External demand carries a typed reason
- **GIVEN** a consumer recording a demand into `std::io::Error::new` (or any non-workspace crate name) that cannot resolve against the workspace-only inventory
- **WHEN** extraction runs
- **THEN** the incomplete-demand gap carries the typed reason `std-item` (or `external-crate-unmodeled` for a non-std head) and names the demand target

#### Scenario: Typed reasons do not soften refusal
- **GIVEN** any consumer whose demands include typed-reason gaps of any class
- **WHEN** the extraction is submitted for scoped acceptance
- **THEN** every gap still refuses scoped acceptance with Unknown structural assurance, exactly as the untyped gap did

### Requirement: Declared external signature bundles

An extraction bundle MAY declare external signature inventories — per external crate name, a content-digested slot inventory with recorded provenance — and demand resolution MAY resolve against declared external slots only, marking each resolved demand with `origin: external` and the supplying digest. Demand into an undeclared external crate SHALL keep its typed incomplete-demand gap. There SHALL be no implicit trust: `std`/prelude is declared exactly like any other external crate.

#### Scenario: Declared external demand resolves with origin marking
- **GIVEN** a bundle declaring an external signature inventory for a crate, digest-matched, and a consumer demand into that crate whose target is in the inventory
- **WHEN** extraction runs
- **THEN** the demand resolves with `origin: external` and the supplying digest recorded, and no incomplete-demand gap is emitted

#### Scenario: Undeclared external demand keeps its typed gap
- **GIVEN** a consumer demand into an external crate that the bundle does not declare
- **WHEN** extraction runs
- **THEN** the report retains the incomplete-demand gap with the typed reason `external-crate-unmodeled` naming the demand target

#### Scenario: Digest mismatch requires fresh extraction
- **GIVEN** a declared external signature inventory whose content digest no longer matches the supplied artifact
- **WHEN** extraction runs
- **THEN** input binding fails and a fresh extraction is required

#### Scenario: External digest set is visible at check time
- **GIVEN** a contract whose resolved demands include `origin: external` entries
- **WHEN** a check consumes that contract
- **THEN** the check report lists the external digest set used, and a digest it cannot verify yields Unknown structural assurance for the affected demands rather than a silent pass
