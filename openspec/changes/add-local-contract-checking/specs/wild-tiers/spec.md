## ADDED Requirements

### Requirement: Protected local checking context

An enforced local check SHALL receive its base, obligations, scope, policy, checker, test/law harnesses, environment, fixtures, budgets, and evaluation time from a trusted invocation outside candidate control. Candidate-proposed changes SHALL be evaluated against the accepted context first. An authorized obligation transition SHALL bind old/new commitments and be labelled intentional change rather than backward compatibility.

#### Scenario: Candidate edits its own judge
- **GIVEN** a candidate deletes a law, narrows demand, or changes the policy or checker
- **WHEN** trusted enforcement evaluates the candidate
- **THEN** it retains the accepted context, reports the proposed change, and cannot accept by using the weaker candidate settings

#### Scenario: Authorized bug-fix changes an old obligation
- **GIVEN** an external authority record accepts a named old-to-new obligation transition for a bug fix
- **WHEN** the candidate passes the replacement requirements and unchanged obligations
- **THEN** its disposition is accepted intentional change with affected consumers recorded, not backward-compatible success

### Requirement: Evidence is bound and method labelled

Local evidence SHALL bind actual implementation and harness bytes, suite, fixtures, environment, scope, seed, and budgets. Current policy SHALL be evaluated afresh. Ordinary build/test success SHALL NOT become structural assurance or a v1 law result without the required harness guarantees. A sandbox that cannot enforce required restrictions SHALL yield inconclusive law evidence.

#### Scenario: Same contract but changed implementation
- **GIVEN** an implementation changes bytes without changing its extracted contract
- **WHEN** checking considers a previous executable law result
- **THEN** that evidence cannot satisfy the new artifact's law requirement

#### Scenario: Unsupported law isolation
- **GIVEN** the available runner cannot prevent an accepted law from reading ambient files or the network
- **WHEN** that law is required by policy
- **THEN** its result is inconclusive and the local outcome is unknown unless another definite failure already requires rejection
