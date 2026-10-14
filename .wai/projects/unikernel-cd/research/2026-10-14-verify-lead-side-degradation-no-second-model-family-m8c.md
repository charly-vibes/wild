---
tags: [pipeline-run:epic-orchestrator-2026-10-14-wild-m8c-composition-certificate, pipeline-step:verify]
---

VERIFY: wild-m8c — verdict **REVIEW_REQUIRED** (lead-side degradation path: implementor and lead share the same model family, no second model family available for independent review; per the wild-7e9 precedent this does not block ship).

Artifacts read: brief `.wai/projects/unikernel-cd/briefs/wild-m8c-composition-certificate.md`; implementor report `.wai/projects/unikernel-cd/runs/wild-m8c.report.md` (red output pasted, judgment calls disclosed); spawn log; diffs `d311089..HEAD` (`git diff --stat`, name-only).

Diff scope: exactly the four brief files — `prototype/wild_compose.py` (+276 new), `tests/test_prototype_smoke.py` (+46: one test + loader), `results/composition-cert-2026-10-14.txt`, report. **No file touched outside scope** (name-only grep = NONE); D1 held — no existing prototype file modified.

Fresh meter runs (lead-executed this session, not trusted from the report):
- `python3 -m pytest tests/test_prototype_smoke.py -q` → **5 passed** in 72.09s
- `python3 prototype/wild_compose.py` → exit 0; 60 services / 162 edges, merkle_root=75e7aab7…, verdict=accept, tamper labels `tampered:components` / `tampered:edges` distinct
- `python3 prototype/wild_sim.py`, `python3 prototype/wild_cd_sim.py` → exit 0 (untouched)
- Determinism: two consecutive full runs differ ONLY in the four `MEASURED` wall-clock lines (15–18); deterministic portion proven byte-identical (`cmp` exit 0 on lines 1–14 and the tail). Same MEASURED-vs-seeded caveat as `wild_cd_sim` bench D accepted by the wild-5gb ruling — not a defect.

Findings: none blocking. Brief's D6 intended wall-clock bench; the smoke test correctly asserts seeded determinism at the certify/fleet-dict level, which passed fresh.
