# Purpose: Red-first command-level runtime tests for the v1 canonical reader
#   and semantic schema validation slice (beads wild-3rr bounded slice): the
#   `wild v1` CLI against v1 `contract` wire documents.
# Responsibilities: Build the real binary once per session and exercise
#   `wild v1 --input <file> --output <file>` as a subprocess. Pin the named
#   behaviors from docs/wild-formats-v1.md: canonical bytes for reordered
#   object keys and equivalent escape spellings; refusals for duplicate keys
#   and floating-point numbers; semantic contract refusals (duplicate slot
#   names across slots/tombstones, non-required outputs, inverted integer
#   intervals, defaults that do not inhabit their declared type, duplicate
#   law ids, unsorted set arrays, unknown facets, tombstone polarity);
#   unknown kinds and versions refused; the accept/refuse/error exit
#   mapping (0/1/2). Assert observable records and exit codes, never
#   implementation internals.
# Rationale: The slice's acceptance is an honest semantic reader whose
#   refusals match the format document rather than a hand-written semver
#   oracle; synthetic success would prove nothing. Written before the
#   implementation exists per the ticket's TDD mandate; every test here
#   must fail red against the current binary (which implements only
#   extract/check/update) and stay green unchanged once the slice lands.

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
BIN = REPO / "target" / "debug" / "wild"

EXAMPLES = REPO / "schemas" / "examples-v1.json"


def run_v1(input_path: Path, output_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(BIN), "v1", "--input", str(input_path), "--output", str(output_path)],
        capture_output=True,
        text=True,
        timeout=60,
    )


def build_bin() -> None:
    result = subprocess.run(
        ["cargo", "build"], cwd=REPO, capture_output=True, text=True, timeout=600
    )
    if result.returncode != 0:
        pytest.fail(f"cargo build failed:\n{result.stderr[-2000:]}")


@pytest.fixture(scope="module", autouse=True)
def binary() -> None:
    build_bin()


def base_contract() -> dict:
    with open(EXAMPLES) as f:
        return json.load(f)["contract"]


def write(tmp_path: Path, document: dict | str, name: str = "input.json") -> Path:
    path = tmp_path / name
    if isinstance(document, str):
        path.write_text(document)
    else:
        path.write_text(json.dumps(document))
    return path


def out(tmp_path: Path) -> Path:
    return tmp_path / "canonical.json"


def diagnostics(result: subprocess.CompletedProcess[str]) -> list[dict]:
    envelope = json.loads(result.stdout)
    return envelope["diagnostics"]


def codes(result: subprocess.CompletedProcess[str]) -> list[str]:
    return [d["code"] for d in diagnostics(result)]


def test_valid_example_contract_is_accepted_with_canonical_bytes(
    tmp_path: Path,
) -> None:
    contract = base_contract()
    source = write(tmp_path, contract)
    target = out(tmp_path)
    result = run_v1(source, target)
    assert result.returncode == 0, result.stdout + result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["decision"] == "accept"
    assert envelope["kind"] == "envelope"
    assert envelope["command"] == "v1-read"
    # The output file is the canonical form of the read document.
    canonical = subprocess.run(
        [sys.executable, "-c", "pass"], capture_output=True, text=True
    )
    assert canonical.stderr == ""
    # Key order and whitespace in the input must not change canonical bytes.
    reordered = {
        "kind": contract["kind"],
        "schema_version": contract["schema_version"],
        "relations": contract["relations"],
        "laws": contract["laws"],
        "tombstones": contract["tombstones"],
        "slots": contract["slots"],
        "sunsets": contract["sunsets"],
    }
    first = write(tmp_path, contract, "first.json")
    second = write(tmp_path, reordered, "second.json")
    first_target = tmp_path / "first.out.json"
    second_target = tmp_path / "second.out.json"
    assert run_v1(first, first_target).returncode == 0
    assert run_v1(second, second_target).returncode == 0
    assert first_target.read_bytes() == second_target.read_bytes()


def test_escape_spelling_has_no_effect_on_canonical_bytes(tmp_path: Path) -> None:
    contract = base_contract()
    contract["slots"][0]["meaning"] = "example.result"
    direct = write(tmp_path, json.dumps(contract), "direct.json")
    escaped_text = json.dumps(contract).replace("example.result", "\\u0065xample.result")
    escaped = write(tmp_path, escaped_text, "escaped.json")
    direct_target = tmp_path / "direct.out.json"
    escaped_target = tmp_path / "escaped.out.json"
    assert run_v1(direct, direct_target).returncode == 0
    assert run_v1(escaped, escaped_target).returncode == 0
    assert direct_target.read_bytes() == escaped_target.read_bytes()
    assert b"example.result" in direct_target.read_bytes()


def test_duplicate_object_key_is_refused(tmp_path: Path) -> None:
    source = write(tmp_path, '{"schema_version":"1","kind":"contract","schema_version":"1"}')
    result = run_v1(source, out(tmp_path))
    assert result.returncode == 2, result.stdout
    envelope = json.loads(result.stdout)
    assert envelope["decision"] == "error"


def test_floating_point_number_is_refused(tmp_path: Path) -> None:
    contract = base_contract()
    contract["slots"][0]["type"]["max"] = 1.0
    source = write(tmp_path, json.dumps(contract))
    result = run_v1(source, out(tmp_path))
    assert result.returncode == 2, result.stdout
    envelope = json.loads(result.stdout)
    assert envelope["decision"] == "error"


def test_refused_semantic_contract_keeps_exit_one_with_diagnostics(
    tmp_path: Path,
) -> None:
    contract = base_contract()
    tombstone = dict(contract["slots"][0])
    tombstone["name"] = "result"
    tombstone["polarity"] = "in"
    contract["tombstones"] = [tombstone]
    source = write(tmp_path, contract)
    result = run_v1(source, out(tmp_path))
    assert result.returncode == 1, result.stdout
    assert json.loads(result.stdout)["decision"] == "refuse"
    assert "slot-name-duplicate" in codes(result)


def test_output_slot_must_be_required(tmp_path: Path) -> None:
    contract = base_contract()
    contract["slots"][0]["required"] = False
    result = run_v1(write(tmp_path, contract), out(tmp_path))
    assert result.returncode == 1
    assert "output-required" in codes(result)


def test_inverted_integer_interval_is_refused(tmp_path: Path) -> None:
    contract = base_contract()
    contract["slots"][0]["type"]["min"] = 10
    contract["slots"][0]["type"]["max"] = 0
    result = run_v1(write(tmp_path, contract), out(tmp_path))
    assert result.returncode == 1
    assert "integer-interval" in codes(result)


def test_default_must_inhabit_declared_type(tmp_path: Path) -> None:
    contract = base_contract()
    contract["slots"][0]["default"] = {"present": True, "value": "zero"}
    result = run_v1(write(tmp_path, contract), out(tmp_path))
    assert result.returncode == 1
    assert "default-type-mismatch" in codes(result)


def test_default_outside_integer_interval_is_refused(tmp_path: Path) -> None:
    contract = base_contract()
    contract["slots"][0]["default"] = {"present": True, "value": 99}
    result = run_v1(write(tmp_path, contract), out(tmp_path))
    assert result.returncode == 1
    assert "default-type-mismatch" in codes(result)


def test_duplicate_law_id_is_refused(tmp_path: Path) -> None:
    contract = base_contract()
    law = {
        "id": "example.law",
        "suite_digest": "sha256:" + "1" * 64,
        "slots": [],
    }
    contract["laws"] = [law, dict(law)]
    result = run_v1(write(tmp_path, contract), out(tmp_path))
    assert result.returncode == 1
    assert "law-id-duplicate" in codes(result)


def test_unsorted_slot_array_is_refused(tmp_path: Path) -> None:
    contract = base_contract()
    extra = json.loads(json.dumps(contract["slots"][0]))
    extra["name"] = "aaa"
    extra["meaning"] = "example.aaa"
    contract["slots"] = [contract["slots"][0], extra]
    result = run_v1(write(tmp_path, contract), out(tmp_path))
    assert result.returncode == 1
    assert "set-order" in codes(result)


def test_unknown_facet_is_refused(tmp_path: Path) -> None:
    contract = base_contract()
    contract["slots"][0]["facet"] = "vibes"
    result = run_v1(write(tmp_path, contract), out(tmp_path))
    assert result.returncode == 1
    assert "facet-unknown" in codes(result)


def test_tombstone_must_be_an_input_slot(tmp_path: Path) -> None:
    contract = base_contract()
    tombstone = dict(contract["slots"][0])
    tombstone["name"] = "legacy"
    tombstone["polarity"] = "out"
    contract["tombstones"] = [tombstone]
    result = run_v1(write(tmp_path, contract), out(tmp_path))
    assert result.returncode == 1
    assert "tombstone-polarity" in codes(result)


def test_unknown_kind_is_refused(tmp_path: Path) -> None:
    source = write(tmp_path, {"schema_version": "1", "kind": "vibes"})
    result = run_v1(source, out(tmp_path))
    assert result.returncode == 1
    assert "kind-unsupported" in codes(result)


def test_unknown_schema_version_is_refused(tmp_path: Path) -> None:
    contract = base_contract()
    contract["schema_version"] = "2"
    result = run_v1(write(tmp_path, contract), out(tmp_path))
    assert result.returncode == 2
    assert json.loads(result.stdout)["decision"] == "error"


def test_manifest_kind_is_out_of_this_slice(tmp_path: Path) -> None:
    contract = base_contract()
    source = write(tmp_path, {"schema_version": "1", "kind": "manifest"})
    result = run_v1(source, out(tmp_path))
    assert result.returncode == 1
    assert "kind-unsupported" in codes(result)
