# Change: Add on_absent: fallible — absence as policy for required inputs

## Why

A required input slot makes absence a caller violation: the input is missing,
so the composition refuses. But two honest contexts share one expression of
requirements — "my program is broken" (throw) vs "the outside world lacked the
fact" (collect and handle). Research lesson 9 (.wai/projects/semantic-
composition/research/2026-10-21-lessons-from-hickey-in-context-clojure-conj.md
— "missing is a policy, not a truth") proposes the distinction as a
contract-level clause. Ticket: wild-adc.

## What Changes

- Required input slots MAY declare `on_absent: fallible`: absence at the slot
  is a normal value outcome the consumer handles, not a caller violation.
- The slot STAYS required — it remains in demand and in closure validation;
  only the absence handling changes. A NEW fallible-required slot is still a
  new required input (non-accretion, unchanged).
- Direction is pinned: adding the clause to a retained input is an accretion
  (demand widens); revoking it narrows demand and is a break.
- Tier placement: the clause is recorded tier-1 as a scoped claim; the absence
  itself is observed at tier 3 (canary, replayed traffic) — never a new
  static verdict kind, never an override of structural results.
- Normative rows in wild-core (slot semantics + accretion direction) and
  wild-tiers (observation placement); contract tests pin claim-not-refuse,
  direction, closure integrity, and the tier-3 placement.

## Impact

- Specs: `openspec/specs/wild-core/spec.md` (constraint `absence_as_policy`,
  three unit properties, mirrored Requirement),
  `openspec/specs/wild-tiers/spec.md` (constraint `absence_observed_at_runtime`,
  one unit property, mirrored Requirement).
- Code: v1 slot format + demand/check semantics.
- Tests: red-first contract tests under `tests/runtime/`.
