# Technical decision: producing contracts for software updates

Which combination of deterministic mining and authored obligations best supports consumer-specific, contract-checked software updates?

This is a supporting technical decision. The [software-updates product matrix](../../../software-updates/designs/matrix/problem.md) compares the entry products and defines success in completed updates, avoided false blocks, unsafe acceptance, and human effort. A fast patch checker alone does not satisfy that product objective.

Working premise: humans and agents can draft contracts cheaply. Cheap drafting does not establish that a draft captures intent or remains valid as code changes.

Cells describe mechanisms, not measured performance. Marker colors are design judgments. Latency, maintenance, adoption, and effectiveness require experiments. There is no weighted score or empirical winner.

The registry/deployment platform is deferred from this entry-point decision. Existing CI includes type checking, tests, specialized checks, and agent-generated tests where available. Task tracking remains in Beads.

See ../../research/2026-10-07-agentic-context.md for observations, hypotheses, and sources.

All approaches use the same trusted enforcement of their accepted tests, policy, and obligations. Only the availability of mining and authored-obligation feedback varies in the controlled comparison. Evidence reuse is judged by repeated work avoided and stale evidence accepted, not whether a result uses Wild's format; comparative reuse benefit is currently unmeasured.

? Does combined mining and authoring complete more independently valid updates than an equal budget spent on existing tests?
? How much demand coverage is possible without manual declarations?
? Do users keep the check enabled after the pilot?
