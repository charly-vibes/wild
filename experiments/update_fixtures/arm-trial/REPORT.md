# A–D synthetic fixture report (arm-trial-e3)

## What ran

Protocol `arm-trial-e3` (mode `fixture`, seed 7) from this directory's
`study.json`, executed once through `python3 experiments/update_eval.py
execute --protocol study.json --output results/` with real Cargo resolving
against the offline local registry. Twelve arm-trial task_result records
(3 tasks × 4 arms × 1 trial) were published under `results/`, and
`summary.json` was produced by `experiments/update_eval.py summarize` from
exactly those records; the reproduction test in
`tests/test_update_eval_execution.py` revalidates and recomputes both.

Every arm received the same target catalog, manifest-edit authority, budgets
(timeout 600 s, max 3 attempts), consumer, and shared host execution path;
only the feedback treatment differed (A none, B mined, C authored, D both).

## Conclusions

- **Equal authority held.** Arm A (existing-tool baseline) delivered the same
  authorized major update as arm D: real Cargo refused the exact target under
  the original range, the same authorized manifest edit resolved it through
  the shared host path, and the independent oracle validated the delivered
  artifact (8/12 completions, one per arm on the two deliverable tasks).
- **Protected accepted checks held.** In all four arms, deleting the arm's
  accepted check produced a policy rejection (not a compatibility verdict)
  because the host re-enforced the protected copy; no arm gained acceptance
  by weakening its baseline.
- **Abstention stayed visible.** On the dynamic-usage fixture the checker
  returned `unknown` with reason `dynamic-usage` in every arm while the
  independent oracle adjudicated the same artifact compatible. The summary
  keeps both outcomes side by side: unknown rate 4/12, unsafe acceptance 0/4,
  oracle coverage 12/12 — the abstention is never relabelled as detection.

## Real, synthetic, and unresolved

- **Real:** all Cargo resolution, build, test, and grading steps ran against
  actual binaries on this machine; digests in the records commit the actual
  artifacts the oracle graded.
- **Synthetic:** every fixture (consumers, registry versions, oracles,
  accepted checks, feedback files) is hand-built for this harness. Origin is
  labelled `synthetic` throughout; nothing here is drawn from a real project.
- **Unresolved:** the dynamic-usage case's checker outcome remains `unknown`
  — missing evidence, not a false negative — and stays reported in its own
  category beside the oracle's independent verdict.

## Scope limits

- All results above are **synthetic-fixture conformance**: they show the
  harness mechanics (equal authority, protected grading, honest outcomes),
  not that Wild helps real users. No performance threshold, commercial
  value, or productivity claim is made or supported by this report.
- Human minutes and compute cost are `inapplicable` for these automated
  fixture runs; wall time is measured but tiny. Incomplete cost coverage
  forbids any cost-superiority conclusion.
- Zero bypasses observed on this fixture is not a proof of general security;
  the E4 protection suite is a fixture check, not a security guarantee.
- The held-out E3 study (recruitment, margins, statistical power) remains a
  preregistered follow-up tracked as comparative research wild-1xk, with the
  product-alignment review in wild-6ig still open. This report does not
  substitute for either.
