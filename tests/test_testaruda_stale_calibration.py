"""wild-z56: testaruda-gate self-heal against stale local calibration.

Repro (wild-z56): on branch A the testaruda store ingests calibration for
tests/test_X.py; switch to branch B where test_X.py does not exist; exec
selection still targets tests/test_X.py and the runner exits 4 (file not
found) — the pre-push gate goes red on local state, not on real breakage.

Fix ruling (documented in the ticket's fix direction): the gate prunes the
stale local calibration and retries once. The upstream tool should
intersect selected paths with files present at HEAD (filed upstream via
testaruda feedback); until that lands, the gate self-heals with the
documented workaround (rm -rf .testaruda && testaruda init) on exactly the
runner-failure exit code, so a genuine red still fails after the retry.
"""

import pathlib

REPO = pathlib.Path(__file__).parent.parent


def test_testaruda_gate_self_heals_on_runner_failure() -> None:
    # The gate recipe must, on a red exec, re-init the local store (pruning
    # stale calibration entries whose fingerprints no longer resolve on
    # disk) and retry exec exactly once — the documented wild-z56
    # workaround — before reporting failure.
    justfile = (REPO / "justfile").read_text()
    start = justfile.index("testaruda-gate:")
    body = justfile[start:]
    # terminate the recipe body at the next top-level recipe (if any)
    for marker in ("\n# ---", "\n\n# "):
        idx = body.find(marker)
        if idx != -1:
            body = body[:idx]
    assert "rm -rf .testaruda" in body, (
        "testaruda-gate must prune the stale local store (.testaruda) on a "
        "red exec before retrying (wild-z56)"
    )
    assert "testaruda init" in body, (
        "testaruda-gate must re-init the store after pruning (wild-z56)"
    )
    # retry once: a second exec invocation after the re-init
    assert body.count("testaruda exec") >= 2, (
        "testaruda-gate must retry exec after the stale-calibration re-init "
        "(wild-z56)"
    )


def test_self_heal_scoped_to_runner_failure_exit() -> None:
    # The retry is scoped to the runner-failure exit code (4 — file not
    # found), not a blanket catch-all: hard errors must stay red without a
    # wasteful full re-run.
    justfile = (REPO / "justfile").read_text()
    body = justfile[justfile.index("testaruda-gate:"):]
    assert "4)" in body, (
        "testaruda-gate must scope the self-heal retry to exit 4 (runner "
        "file-not-found), keeping hard errors red (wild-z56)"
    )
