---
tags: [pipeline-run:tdd-ro5-2026-11-27-declared-bump-derivation-wild-zh6, pipeline-step:plan]
---

PLAN: add-declared-bump-derivation (bd wild-zh6) - 1) requirement-level corpus parser (src/bump.rs) reading openspec/specs corpora via git trees; 2) aggregated delta derivation added-only->minor/accretes, modified/removed/renamed->major/revokes, row-only/empty->patch, missing base->Unknown+missing_base_corpus (never fabricated); 3) upward-only override: lowering refused (bump_class_lowering_refused), proposal stands; 4) advisory envelope output + local-1 declared-bump-record renderer; 5) rename pairing by identical normalized bodies; 6) red tests first (tests/test_declared_bump.py incl. totality property), then green; 7) registry contract specs (.espectacular/wild-registry) + wild-registry/wild-adopt spec deltas.
