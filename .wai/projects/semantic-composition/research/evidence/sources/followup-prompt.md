# Wild — focused follow-up prompt

Evaluate **one** design question in https://github.com/charly-vibes/wild: **Can a certified assembly be treated as a reusable composite component, with an external contract and preserved behavioral guarantees?**

Use primary sources only: README, docs/wild-manual.md, docs/wild-formats-v1.md, schemas/, specs/, prototype/, tests/, and experiments/RESULTS.md. Identify the exact inspected commit. Clone and execute tests/prototypes if possible; report blockers and mark unexecuted claims UNKNOWN.

1. Distinguish the existing v1 assembly semantics, the Python prototype implementation, and aspirational commands.
2. Trace roots, bindings, demands, instances, adapters and composition rules to their normative definitions and tests.
3. Check whether there is an actual recursive composite interface, aggregate-law semantics and substitution rule. Do not infer presence from category-theoretic terminology.
4. Construct a minimal two-layer example showing both a successful replacement and an observable behavioral counterexample. Mark hypothetical artifacts clearly.
5. Compare designs: manual wrapper contract, first-class composite contract, and flattening-only assembly. Analyze failure modes, verification burden, incremental rebuild cost and language neutrality.
6. Deliver a self-contained Markdown report (TL;DR first, jargon, evidence matrix, source citations, PROV front matter, implementation gaps and design recommendation). No invented guarantees.
