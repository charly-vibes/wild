---
tags: [pipeline-run:tdd-ro5-2026-11-27-widen-method-receiver-demands-wild-8j4, pipeline-step:refactor]
---

REFACTOR: dropped the unfulfilled #[expect(clippy::too_many_arguments)] on scan_crate; cargo fmt applied; clippy on touched files clean (remaining lib warnings in bump.rs/feedback.rs and one in main.rs predate this change, files untouched). Narrow suite green: 15 passed -k widen.
