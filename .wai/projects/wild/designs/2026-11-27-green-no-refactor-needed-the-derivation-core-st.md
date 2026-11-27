---
tags: [pipeline-run:tdd-ro5-2026-11-27-declared-bump-derivation-wild-zh6, pipeline-step:green]
---

GREEN: no refactor needed - the derivation core stayed a single pure module (src/bump.rs, one requirement parser + one aggregate classifier); complexity measured clean under pretender gate mode; tests sequenced the three declared-change shapes into one test to satisfy the lazy-cluster ratchet; registry test pointers updated in .espectacular/wild-registry.
