# Semantic composition investigation

Research question: can reusable assemblies preserve public obligations through internal and cross-language replacements?

Start with the [investigation and evidence ledger](research/2026-10-09-investigation.md), then compare the [three hierarchy approaches](designs/matrix/problem.md) and [16 evaluation cases](designs/2026-10-09-case-matrix.md). The [Rule-of-5 review](reviews/2026-10-09-rule-of-5.md) records five passes and their remedies. [Decision status](designs/matrix/decision.md) remains open.

Established result: a reproducible six-schedule reservation model accepts identical interface shapes while detecting four behavioral failures in the stale implementation. This establishes a bounded need for behavioral checking; it does not select wrappers over flat assemblies or prove a real runtime correct.

TypeSafe verified two HIGH review findings above its confidence threshold. Two others require human judgment on the initial pilot's scope: composite evidence commitments and shared singleton identity. Those cases are included provisionally. Lower-severity findings use self-reported validation.

Beads owns task status:

| ID | Scope |
| --- | --- |
| wild-9co | Research epic |
| wild-9co.1 | This investigation, matrix and editorial review |
| wild-9co.2 | Protected public-law pilot, positive replacements and negative controls |
| wild-9co.3 | Boundary mapping, identity, flattening and evidence experiment |
| wild-9co.4 | Bounded semantic profile and cross-language observation mapping; depends on wild-9co.2 |

The project remains in WAI's research phase. Product work wild-mh5/wild-nic/wild-aoq continues independently; no normative spec or runtime behavior is changed here.
