"""Contract tests for the wild spec corpus.

The corpus under openspec/specs is dual-format (openspec scenarios +
specodelic grammar). The gate requires it lint-clean with a closed
reference graph.
"""

import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "openspec"


def spk_lint() -> dict:
    proc = subprocess.run(
        ["spk", "lint", "openspec"],
        capture_output=True,
        text=True,
        cwd=REPO,
        check=True,
    )
    return json.loads(proc.stdout)


def test_spec_corpus_lint_clean():
    """Every dual-format file passes specodelic lint."""
    envelope = spk_lint()
    data = envelope.get("data") or {}
    assert envelope["ok"] is True, envelope
    assert data.get("files_linted", 0) == 9
    issues = data.get("issues") or []
    warnings = data.get("warnings") or []
    assert not issues, [i["message"] for i in issues]
    assert not warnings, [w["message"] for w in warnings]


def test_spec_graph_reference_closed():
    """No dangling references anywhere in the corpus."""
    proc = subprocess.run(
        ["specodelic", "graph", "openspec"],
        capture_output=True,
        text=True,
        cwd=REPO,
        check=True,
    )
    dangling = json.loads(proc.stdout).get("dangling") or []
    assert not dangling, dangling