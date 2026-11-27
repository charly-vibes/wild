# Purpose: Contract tests for the release-CI contract-bundle step (beads
#   wild-zjv, openspec change add-wild-contract-bundle-convention task 3.2).
# Responsibilities: Pin that scripts/make-contract-bundle.sh produces the
#   two-file bundle (contract.json + manifest.toml) with a digest-bound
#   manifest whose commit is the exact checkout HEAD and whose
#   contract_sha256 matches the recomputed digest; that exit-1 (honest gap
#   accounting) attaches while exit-2 (error class) refuses loudly; and
#   that .github/workflows/release.yml installs a pinned extractor and
#   attaches the bundle asset to the release.
# Rationale: the manifest is the trust-chain head — anything absent from it
#   is unverifiable by construction. These tests mirror the testaruda pilot
#   (wild-xc4) behavior so the fleet stays one convention.

from __future__ import annotations

import hashlib
import re
import subprocess
import tarfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
BIN = REPO / "target" / "debug" / "wild"
SCRIPT = REPO / "scripts" / "make-contract-bundle.sh"
WORKFLOW = REPO / ".github" / "workflows" / "release.yml"
VERSION = "9.9.9-test"


def run_script(args: list[str], env_bin: str | None = None, cwd: Path | None = None):
    env = {"WILD_BIN": str(BIN)}
    if env_bin is not None:
        env["WILD_BIN"] = env_bin
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env={**{"PATH": "/usr/bin:/bin"}, **env},
        cwd=cwd or REPO,
        timeout=300,
    )


@pytest.fixture(scope="session")
def wild_binary() -> Path:
    if not BIN.exists():
        build = subprocess.run(
            ["cargo", "build", "-q"], cwd=REPO, capture_output=True, text=True
        )
        if build.returncode != 0:
            pytest.fail(f"cargo build failed:\n{build.stderr[-2000:]}")
    assert BIN.exists()
    return BIN


def unpack(asset: Path, dest: Path) -> None:
    with tarfile.open(asset) as tar:
        tar.extractall(dest)


@pytest.mark.usefixtures("wild_binary")
class TestBundleArtifact:
    def test_bundle_is_exactly_two_files_with_digest_bound_manifest(self, tmp_path):
        out = tmp_path / "dist"
        proc = run_script([VERSION, str(out)])
        assert proc.returncode == 0, proc.stderr[-2000:]

        asset = out / f"wild-{VERSION}-contract-bundle.tar.gz"
        assert asset.exists(), f"bundle not written: {proc.stdout[-500:]}"

        unpack_dir = tmp_path / "unpacked"
        unpack_dir.mkdir()
        unpack(asset, unpack_dir)
        assert sorted(p.name for p in unpack_dir.iterdir()) == ["contract.json", "manifest.toml"]

        manifest = (unpack_dir / "manifest.toml").read_text()
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=REPO
        ).stdout.strip()
        assert f'tool = "wild"' in manifest
        assert f'version = "{VERSION}"' in manifest
        assert f'commit = "{commit}"' in manifest, "manifest must stamp the exact checkout HEAD"
        assert 'profile = "rust-cargo-local-1"' in manifest
        extractor_version = subprocess.run(
            [str(BIN), "--version"], capture_output=True, text=True, cwd=REPO
        ).stdout.strip()
        assert f'extractor_version = "{extractor_version}"' in manifest
        assert re.search(r'extracted_at = "\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"', manifest)

        stamped = manifest.split('contract_sha256 = "', 1)[1].split('"', 1)[0]
        contract_bytes = (unpack_dir / "contract.json").read_bytes()
        recomputed = "sha256:" + hashlib.sha256(contract_bytes).hexdigest()
        assert stamped == recomputed, "manifest.contract_sha256 must bind the packed contract.json"

    def test_error_class_extraction_refuses_loudly(self, tmp_path):
        # A binary exiting 2 on extract (error class: no contract exists to
        # stamp) must fail the script, never stamp a manifest over a missing
        # contract.
        fake = tmp_path / "fake-wild-err"
        fake.write_text('#!/bin/sh\n[ "$1" = "--version" ] && { echo "wild 0.0.0"; exit 0; }\nexit 2\n')
        fake.chmod(0o755)
        proc = run_script([VERSION, str(tmp_path / "out")], env_bin=str(fake))
        assert proc.returncode == 2
        assert not (tmp_path / "out").exists() or not any((tmp_path / "out").iterdir())

    def test_gap_accounting_exit_one_still_attaches(self, tmp_path):
        # Exit 1 is honest refuse-Unknown gap accounting: the bundle attaches
        # rather than blocks the release (shadow_never_blocks stance).
        fake = tmp_path / "fake-wild-gap"
        fake.write_text(
            '#!/bin/sh\n'
            '[ "$1" = "--version" ] && { echo "wild 0.0.0"; exit 0; }\n'
            'out=""; while [ $# -gt 0 ]; do [ "$1" = "--output" ] && out="$2"; shift; done\n'
            'mkdir -p "$out" && printf \'{"schema_version":"1"}\' > "$out/contract.json"\n'
            'echo gap\nexit 1\n'
        )
        fake.chmod(0o755)
        out = tmp_path / "out"
        proc = run_script([VERSION, str(out)], env_bin=str(fake))
        assert proc.returncode == 0, proc.stderr[-2000:]
        assert (out / f"wild-{VERSION}-contract-bundle.tar.gz").exists()


class TestReleaseWorkflowWiring:
    def test_workflow_installs_pinned_extractor_and_attaches_bundle(self):
        text = WORKFLOW.read_text()
        # Extractor version is part of the bundle's trust chain — pinned, never latest.
        install = re.search(r"cargo install wild-vibes --version (\S+)", text)
        assert install, "release.yml must install the wild extractor at a pinned version"
        assert install.group(1) != "latest"
        assert "make-contract-bundle.sh" in text, "release.yml must run the bundle script"
        # The bundle asset must be attached to the release (explicit list or glob).
        create = text.split("gh release create", 1)[1]
        assert "contract-bundle.tar.gz" in create, "bundle asset must be attached to the release"
        # Bundle extraction must run before provenance generation so the
        # bundle digest is bound into provenance.json.
        assert text.index("Extract contract bundle") < text.index("Generate provenance manifest")
