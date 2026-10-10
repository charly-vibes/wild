"""wild-48s: clean-checkout Testaruda discovery of nested Rust fixtures.

Isolated clean checkouts originally failed the pre-push testaruda gate
because the rust adapter invoked `cargo` at the repo root without a
Cargo.toml (exit 101) while chasing nested fixture crates under
experiments/update_fixtures. Two guards pin the fix:

1. The repo root carries a Cargo.toml, so the adapter's `cargo test`
   invocation at the repo root always resolves a manifest.
2. The fixture tree (experiments/) is excluded from the testaruda
   discovery walk, so fixture files never route to adapters and never
   mint selection edges — the gate never runs (or reds on) the
   intentionally-failing fixture crates. This is exclusion, not gate
   skipping: the root crate's real rust tests remain discovered and
   gated.
"""

import pathlib
import tomllib

REPO = pathlib.Path(__file__).parent.parent


def test_cargo_manifest_present_at_repo_root() -> None:
    # The rust adapter runs `cargo test` from the repo root; a missing
    # manifest is the original clean-checkout exit-101 failure mode.
    assert (REPO / "Cargo.toml").is_file(), (
        "repo root Cargo.toml missing — rust adapter would exit 101 at the "
        "repo root in a clean checkout (wild-48s)"
    )


def test_fixture_tree_excluded_from_testaruda_discovery() -> None:
    # experiments/ holds intentionally-failing fixture crates (e.g.
    # e5/cases/baseline-failure). It must sit on the discovery exclude
    # list so the adapter pipeline never routes those files into the
    # selection graph.
    config = tomllib.loads((REPO / "testaruda.toml").read_text())
    exclude = config["discover"]["exclude"]
    assert "experiments" in exclude, (
        "testaruda.toml [discover].exclude must cover the nested Rust "
        "fixture tree 'experiments' (wild-48s)"
    )