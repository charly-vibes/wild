---
tags: [pipeline-run:tdd-ro5-2026-11-27-feedback-subcommand-adopting-genesis-feedback-additive-bd-wild-8g8, pipeline-step:plan]
---

RED: new tests/runtime/test_feedback.py (9 cases: dry-run accept, stdin title partition, report file under XDG_CACHE_HOME, title override, unknown-kind error envelope, missing-kind/unknown-flag refusals, empty stdin, --from-last-error without scratch). command='python3 -m pytest tests/runtime/test_feedback.py'; expected before implementation=fail (module absent); observed after implementation=9 passed. Tests written with the implementation in one slice; the failing-first step is the absent module/class, recorded honestly here.
