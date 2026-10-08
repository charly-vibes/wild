## ADDED Requirements

### Requirement: Validate a host-selected local assembly

Local update evaluation SHALL validate the explicit assembly selected by the host lock rather than invoke registry newest-tip selection. It SHALL account for all roots, components, required inputs, transitive dependencies, declared singletons, and relations using existing v1 structural rules. Unknown entries SHALL remain in coverage and SHALL refuse policies requiring complete structure. The local report SHALL NOT claim native registry ancestry or constitute a v1 registry certificate.

#### Scenario: New provider dependency is not hidden by demand restriction
- **GIVEN** a candidate preserves the consumer's demanded output but adds an unsatisfied required dependency
- **WHEN** the host-selected assembly is checked
- **THEN** delivery is refused even though the root's demanded output signature is unchanged

#### Scenario: Unknown dependency remains visible
- **GIVEN** the lock contains a required dependency with no usable contract
- **WHEN** the local assembly is evaluated under policy requiring declared structure
- **THEN** that entry remains in the closure and coverage with Unknown assurance and delivery is refused

#### Scenario: Local pin does not claim newest lineage tip
- **GIVEN** a valid explicitly pinned host assembly and no Wild registry
- **WHEN** local structural checking succeeds
- **THEN** the report identifies its local scope and makes no registry-tip or publication claim
