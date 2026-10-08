"""Contract tests for the wild spec corpus.

The corpus under openspec/specs is dual-format (openspec scenarios +
specodelic grammar). The gate requires it lint-clean with a closed
reference graph.
"""

import json
import os
import re
import subprocess
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

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
    assert data.get("files_linted", 0) == len(list((CORPUS / "specs").glob("*/spec.md")))
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
    dangling = json.loads(proc.stdout)["data"]["dangling"]
    assert not dangling, dangling

@pytest.mark.parametrize("capability", sorted(p.parent.name for p in (CORPUS / "specs").glob("*/spec.md")))
def test_design_contract_is_self_contained(capability):
    """Check design coverage and local schema references, not future runtime behavior."""
    text = (CORPUS / "specs" / capability / "spec.md").read_text()
    constraints = text.split("## Constraints", 1)[1].split("## Model", 1)[0]
    ids = re.findall(r"^\| ([a-z_]+) \| (?:invariant|advisory|extension_point|effect) \|", constraints, re.M)
    rules = text.split("## Design acceptance cases", 1)[1].split("## Requirements", 1)[0]
    for constraint_id in ids:
        assert f"The system SHALL satisfy `{constraint_id}`" in rules, constraint_id
    assert rules.count("#### Acceptance case:") >= len(ids)
    assert "### Requirement:" in text and "## Purpose" in text
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if not target.startswith(("https:", "http:")):
            assert ((CORPUS / "specs" / capability) / target).is_file(), target
    schema = json.loads((REPO / "schemas" / "wild-v1.schema.json").read_text())
    Draft202012Validator.check_schema(schema)


def test_openspec_strict_discovers_all_capabilities():
    """Prevent a lint-clean corpus from containing zero OpenSpec requirements."""
    env = {**os.environ, "OPENSPEC_TELEMETRY": "0"}
    proc = subprocess.run(
        ["openspec", "validate", "--all", "--strict", "--no-interactive", "--json"],
        cwd=REPO, env=env, capture_output=True, text=True, check=True,
    )
    report = json.loads(proc.stdout)
    expected = {p.parent.name for p in (CORPUS / "specs").glob("*/spec.md")}
    expected_changes = {p.parent.name for p in (CORPUS / "changes").glob("*/proposal.md")}
    assert {item["id"] for item in report["items"]} == expected | expected_changes
    assert report["summary"]["totals"]["failed"] == 0
    for capability in sorted(expected):
        shown = subprocess.run(
            ["openspec", "show", capability, "--type", "spec", "--json"],
            cwd=REPO, env=env, capture_output=True, text=True, check=True,
        )
        parsed = json.loads(shown.stdout)
        source = (CORPUS / "specs" / capability / "spec.md").read_text()
        assert parsed["requirementCount"] == source.count("### Requirement:"), capability


def test_v1_examples_cover_every_document_kind():
    """Structural examples cover each wire variant; their digests/signatures are illustrative."""
    schema = json.loads((REPO / "schemas" / "wild-v1.schema.json").read_text())
    examples = json.loads((REPO / "schemas" / "examples-v1.json").read_text())
    validator = Draft202012Validator(schema)
    kinds = {r["$ref"].rsplit("/", 1)[1] for r in schema["$defs"]["wire_document"]["oneOf"]}
    assert set(examples) == kinds | {"bundle"}
    for document in examples.values():
        validator.validate(document)


@pytest.mark.parametrize("invalid_case", [
    ("certificate", "policy", "latest"),
    ("contract", "schema_version", "99"),
    ("law_result", "method", "exact_seeded"),
    ("observation", "confidence_ppm", 1000001),
    ("attestation", "signature_algorithm", "none"),
    ("manifest", "contract", "sha256:BAD"),
])
def test_v1_schema_refuses_invalid_identity_or_assurance(invalid_case):
    """Prevent malformed identities and unsupported assurance claims entering the protocol."""
    schema = json.loads((REPO / "schemas" / "wild-v1.schema.json").read_text())
    examples = json.loads((REPO / "schemas" / "examples-v1.json").read_text())
    kind, field, value = invalid_case
    document = {**examples[kind], field: value}
    assert not Draft202012Validator(schema).is_valid(document)


def test_v1_certificate_requires_commitments_and_refuses_unknown_fields():
    schema = json.loads((REPO / "schemas" / "wild-v1.schema.json").read_text())
    examples = json.loads((REPO / "schemas" / "examples-v1.json").read_text())
    validator = Draft202012Validator(schema)
    certificate = examples["certificate"]
    for field in ("assembly", "policy", "checker", "evaluated_at"):
        incomplete = {k: v for k, v in certificate.items() if k != field}
        assert not validator.is_valid(incomplete), field
    assert not validator.is_valid({**certificate, "trust_me": True})
