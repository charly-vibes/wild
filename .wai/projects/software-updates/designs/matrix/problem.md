# Product decision: easier contract-checked software updates

Which first product helps consumers complete more useful software updates with less manual compatibility reasoning, using checked contracts rather than trusting version labels?

The original value proposition remains central: identify candidate revisions by their exact artifacts, evaluate them against actual consumer requirements, and help complete a direct update or explicit migration. Agentic coding can reduce the cost of contracts and repairs; it is a delivery mechanism rather than a replacement product goal.

Compare existing update automation plus CI, a local consumer-specific update assistant, a general agent-change checker, and the native contract platform. The [contract-production matrix](../../../agentic-adoption/designs/matrix/problem.md) is a supporting technical decision shared by the Wild alternatives.

Facts describe proposed mechanisms and existing spec constraints. Colors are design judgments about fit for a first brownfield product, not measured superiority. Neutral means no comparative advantage has been established; the baseline is not required to have a red cell. No proposal wins merely by using its own artifact format. Register experimental targets before measuring results.

The same candidate catalog, target priorities, allowed manifest/migration actions, protected obligations, existing tests, and independent oracle apply to controlled comparisons. All approaches may attempt an authorized out-of-range update. Runtime/platform, provenance, licensing, and organization-policy constraints are evaluated separately from compatibility.

See the [decision context](../../research/2026-10-07-update-context.md) and [shared protocol](../../../agentic-adoption/designs/2026-10-07-mined-and-authored.md). Metrics count actual pinned and independently validated updates, not reports produced. Tasks are tracked only in Beads (wild-6ig, wild-1xk).

? Does the update assistant complete more valid direct updates or migrations than existing automation and an agent given the same budget?
? Does consumer demand overcome unnecessary range restrictions without increasing unsafe acceptance?
? Do teams retain it because updates become easier, rather than because reports are produced?
