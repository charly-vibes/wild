---
tags: [review, resolution]
tracks:
- .wai/projects/software-updates/designs/matrix
- .wai/projects/agentic-adoption/designs/matrix
- .wai/projects/agentic-adoption/designs/2026-10-07-mined-and-authored.md
---

# Rule-of-5 corrections

All five requested design corrections are applied. This record distinguishes content changes, mechanical checks, and the confidence-limited TypeSafe assessment. No experiments or runtime behavior are claimed to be implemented.

## Current entry points

- [Product matrix](../../software-updates/designs/matrix/problem.md): easier contract-checked updates; compares existing tooling, an update assistant, a general checker, and the native platform over seven outcome criteria.
- [Product design](../../software-updates/designs/2026-10-07-consumer-update-assistant.md): candidate discovery through an independently validated pinned direct update or migration.
- [Technical matrix](../designs/matrix/problem.md): contract production as a supporting decision, with common protected enforcement and no presumed evidence-reuse winner.
- [Technical design and experiments](../designs/2026-10-07-mined-and-authored.md): corrected treatment definitions, outcome table and denominators, update-specific cohorts, and end-to-end range-change protocol.
- [Current technical decision](../designs/2026-10-07-mined-and-authored-2.md): refreshed snapshot and trade-offs. The earlier snapshot is explicitly historical.

## Disposition by finding

| Finding | Applied correction | Verification status |
| --- | --- | --- |
| DRAFT-001 | Added a product matrix centered on completed updates, range friction, unsafe acceptance, effort, lag, first use, and migration. Reframed the original matrix as technical support and changed E3/E7 to update outcomes. | Mechanically present; TypeSafe selected verified at confidence 0.75, below 0.8. REVIEW_REQUIRED. |
| CORR-001 | Defined identical trusted enforcement, authority, catalog, target priorities, and protected in-loop checks for A-D. Only mining and authored-obligation feedback vary. Updated the matrix cells as well as the protocol. | TypeSafe verified, confidence 0.96. |
| CORR-002 | Replaced the format-based baseline criticism with measurable native-log/test/cache reuse. All four reuse markers are neutral and relative benefit is explicitly unmeasured. E6 charges retrieval and regeneration and measures stale acceptance. | Mechanically inspected. UNVERIFIED by TypeSafe under the skill's MEDIUM severity limit. |
| CLAR-001 | Added accept/reject/unknown/error crossed with independently compatible/incompatible outcomes; policy eligibility and oracle uncertainty remain separate. Defined all denominators, zero-denominator handling, direct/migration classes, and failed-attempt costs. | Mechanically inspected. UNVERIFIED by TypeSafe under the skill's MEDIUM severity limit. |
| EDGE-001 | Added allowed/excluded range strata crossed with compatibility, equal opt-in authority for all arms, real manifest changes and host resolution, actual artifact/closure checks, independent consumer validation, pinned delivery, and separate migration outcomes. | TypeSafe verified, confidence 0.97. |

## Validation method and remaining review flag

The three HIGH correction claims were mechanically located and submitted in one request using the previously invoked rule-of-5-universal procedure. The model alias was jev-latest and the returned model was jev-1.13.0. These checks assess whether the revised text supports the correction claims; they do not establish product effectiveness. They do not change the validation of the historical findings.

For DRAFT-001 the response selected verified but returned confidence 0.75. The skill's `references/typesafe-verification.md` states: "Any verdict with confidence < CONFIDENCE_GATE" is kept as "REVIEW_REQUIRED" and routed to "ESCALATE_TO_HUMAN". The prescribed gate is 0.8. Accordingly, the product alignment decision is flagged for human review in Beads wild-6ig, rather than silently rounded up or repeatedly queried for a passing result. The applied correction remains in place; this is a review flag, not a request to authorize the edits again. Comparative execution wild-1xk remains dependent on the review issue.

The two MEDIUM findings were not submitted, as prescribed by the severity cap. Their structural edits and consistency were checked locally. WAI validates both matrices without structural errors or stale decisions. It emits a methodology warning that the baseline has no red cell; this is intentional and documented in both current designs. Existing tools are not assigned an invented deficiency to satisfy a color heuristic. Markdown links, decision pointers, and whitespace are checked separately.

## Scope preserved

The original easier-update proposition remains central. Agents are a contract-authoring and migration mechanism; generic patch feedback is a supporting capability. Current normative specs and runtime code are unchanged. The isolated range-change workflow is a design correction that requires the OpenSpec change workflow before runtime implementation.
