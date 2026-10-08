## ADDED Requirements

### Requirement: Standalone local compatibility check

Wild SHALL check supplied base/candidate bundles for a named consumer scope without requiring registry publication, upstream contract adoption, historical reconstruction, or activation of adoption gate/native modes. It SHALL use v1 envelopes and the local-1 report contract, write only explicitly requested report artifacts, and preserve host manifests, lockfiles, source, and CI configuration.

#### Scenario: First result in an existing repository
- **GIVEN** supported local bundles and an explicit check request with no Wild registry or adoption history
- **WHEN** wild check evaluates the requested boundary
- **THEN** it reports structural assurance, law methods, scope, coverage, and stable diagnostics
- **AND** project files and adoption level remain unchanged

#### Scenario: A result separates policy from execution
- **GIVEN** a required analysis gap, a known structural break, and a malformed request in three separate runs
- **WHEN** checks finish
- **THEN** the local outcomes are respectively unknown, reject, and error with exits 1, 1, and 2
- **AND** all refuse policy acceptance without calling missing evidence a structural counterexample

### Requirement: Separate authored obligations from extracted facts

Wild SHALL accept human- or agent-authored obligation drafts using the same local-1 format and authority rules, store them separately from mined facts, and preserve accepted obligations when re-extracting candidate code. Authorship SHALL NOT raise assurance. Prose without an executable or structural predicate SHALL remain unverified, and contradictions with extracted facts SHALL remain visible.

#### Scenario: Regeneration cannot erase intent
- **GIVEN** an accepted law and a candidate that regenerates its contracts without that law
- **WHEN** the candidate is checked
- **THEN** the original law is still evaluated and the proposed deletion is reported separately

#### Scenario: Human and agent predicates receive equal checking
- **GIVEN** otherwise identical executable obligations with human and agent origin labels
- **WHEN** the same checker evaluates them on identical committed inputs
- **THEN** their assurance and law results match while provenance retains the different origins
