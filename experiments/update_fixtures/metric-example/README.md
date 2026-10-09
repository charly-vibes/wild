# metric-example fixtures

Committed metric fixtures for the evaluation record slice (beads wild-aoq.1).
Every task record carries `origin: "synthetic"`; these cohorts exercise the
summary denominators from `openspec/changes/add-update-evaluation-harness/design.md`
("Aggregation acceptance example") — they are not real study results.

- `six-candidate/` — the six-candidate cohort: two compatible accepts, one
  incompatible accept, one incompatible compatibility-reject, one compatible
  unknown, one incompatible error. Expected: unsafe acceptance, recall and
  false-negative rate 1/3, false-block 0/3, unknown/error 1/6, coverage 6/6.
- `extended/` — the same six plus one policy-prohibited accepted candidate and
  one accepted oracle-unresolved candidate. Binary rates are unchanged; the
  added cases stay visible in assigned counts and their own categories and
  never count as independently validated completion.

Expectations are versioned: changing a fixture outcome appends a new fixture
version, it never rewrites committed history (same rule as the bootstrap
corpus).