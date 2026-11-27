# Purpose: Pytest bindings for the six deployed wild-core openness scenario
#   contracts (.espectacular/wild-core/*open*.toml, *.toml with closure in the
#   id). The v1 semantics live in the Rust checker tests (tests/v1_checker.rs);
#   this wrapper makes each scenario's cargo test invocable through the pytest
#   runner the hardcoded-gate pattern binds ([tests.pytest]).
# Responsibilities: Run the one cargo test that is each scenario's canonical
#   check and fail if it fails; share a session-scoped cargo build so six
#   scenarios do not compile six times.
# Rationale: The gate-wiring gate requires every hardcoded gate contract to
#   bind pytest; dispatching to the real Rust tests keeps the binding honest
#   (each wrapper runs the actual scenario test, it does not re-assert
#   anything itself).
# Dependencies: cargo; tests/v1_checker.rs.

from __future__ import annotations

import pathlib
import subprocess

import pytest

REPO = pathlib.Path(__file__).parent.parent

# scenario contract id -> the v1_checker test that is the scenario's check
SCENARIOS: dict[str, str] = {
    "omitted-open-resolves-open": "omitted_open_resolves_open",
    "unjustified-closure-rejected": "unjustified_closure_is_rejected",
    "omitted-open-and-explicit-true-are-distinct-ids-that-accrete": (
        "omitted_open_and_explicit_true_are_distinct_ids_that_accrete"
    ),
    "explicit-declarations-keep-their-semantics": (
        "extra_record_field_requires_open_target"
    ),
    "editing-a-closure-justification-is-a-break": "closure_reason_edit_is_break",
    "justified-closure-keeps-the-break-rules": "justified_closed_sum_growth_is_break",
}


@pytest.fixture(scope="session")
def v1_checker_built() -> None:
    build = subprocess.run(
        ["cargo", "test", "-q", "--test", "v1_checker", "--no-run"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    if build.returncode != 0:
        pytest.fail(f"cargo test --no-run failed:\n{build.stderr[-2000:]}")


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_openness_scenario(v1_checker_built, scenario: str) -> None:
    test_name = SCENARIOS[scenario]
    proc = subprocess.run(
        ["cargo", "test", "-q", "--test", "v1_checker", test_name],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"scenario {scenario} failed:\n{proc.stdout[-2000:]}"
