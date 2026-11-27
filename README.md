# wild

> *"Oh baby baby, it's a wild world*
> *It's hard to get by just upon a smile*
> *Oh baby baby, it's a wild world*
> *I'll always remember you like a child, girl"*
> — Cat Stevens

Machine-checked compatibility and composition of software components, modelled as a category of contracts. For Rust developers (and their CI) who want to know whether two crate versions compose before they ship, without a full integration-test cycle.

**Why:** dependency and composition breakage today is caught by integration tests — after you've written them, waited for them, and shipped anyway when they pass. Existing tools check version ranges declared in manifests, which the experiments in this repo show disagree with actual compatibility on real projects (e.g. 6 of 15 consecutive Rust releases where Cargo's caret rule and the contract check disagreed). Wild checks compatibility against machine-checked contracts instead of hope.

**Status.** A design with a prototype and a Rust implementation. The `wild extract` and `wild check` subcommands are implemented and runtime-tested (see `src/` and `tests/runtime/`); the manual describes the intended interface and marks what is implemented. · [FAQ & troubleshooting](docs/src/faq.md) · [Motivation & design](docs/src/index.md)

**Crates.io.** The publishable package is `wild-vibes` — the `wild` crate name on crates.io belongs to an unrelated glob-expansion crate. The repository, binary, and wire-format identities remain `wild`; see `Cargo.toml` for the rationale.

## When to use

- Use `wild` when you need to know whether a specific dependency upgrade composes with your code before you take it — checked against extracted contracts, not just declared version ranges.
- Use `wild` when a manifest range says "compatible" but you have been burned before: the check compares extracted demand and contract facts, which catches cases version rules miss.
- Use `wild` when you want every verdict (accept / refuse / error) as a machine-readable v1 envelope with exit codes your CI can gate on.

**Don't use it when** your concern is cross-language seam composition across call, effect, or trust boundaries (use [vampiro](https://github.com/charly-vibes/vampiro) instead — it proves composition at seam boundaries; wild checks dependency compatibility), or when you need to shrink which tests run for a change (use [testaruda](https://github.com/charly-vibes/testaruda) instead — it selects tests; wild checks compatibility directly). Wild assumes it is given complete, committed bundles: its verdicts are only as good as the per-file sha256 commitments in the request, and it never writes outside the locations you pass it or touches the network.

## Install

Download a pre-built binary from the releases (no Rust toolchain needed) —
Linux x86_64:

```
curl -fLO https://github.com/charly-vibes/wild/releases/latest/download/wild_linux_amd64.tar.gz
tar -xzf wild_linux_amd64.tar.gz && ./wild --help
```

Darwin (Apple silicon) and Windows (`.zip`) archives follow the same naming:
`wild_darwin_arm64.tar.gz`, `wild_windows_amd64.zip`; `checksums.txt` and
`provenance.json` in the same release list the sha256 of every asset. Or build
from source / install the crate from crates.io (package `wild-vibes`, binary
`wild`):

```
cargo install wild-vibes
```

## Quick start

`wild` speaks the local-1 wire protocol (`docs/wild-local-v1.md`); commands
take a request file with per-file sha256 commitments of the bundle. See
`schemas/examples-local.json` for structural examples of every record kind.

```sh
wild extract --request extraction.json --output facts/
# → stdout: a v1 envelope, e.g. {"schema_version":"1","kind":"envelope",
#   "command":"extract","assurance":"PassDeclared","decision":"accept",...}
# → exit 0 on accept; facts/ now contains contract.json, demand.json,
#   provenance.json, report.json
# → exit 1 with "decision":"refuse" if the inventory is incomplete;
#   exit 2 if the request is unreadable or malformed
```

Verify compatibility of a base/candidate pair and write the check report:

```sh
wild check --request check.json --format json --report report.json
# → v1 envelope on stdout; exit 0 = compatible, 1 = refused, 2 = error
```

## Common workflows

1. **Extract facts from a bundle** — `wild extract --request extraction.json --output facts/` → contract, demand, and provenance records in `facts/`, envelope on stdout.
2. **Gate an upgrade in CI** — `wild check --request check.json --format json --report report.json` → exit 0 lets the upgrade through, exit 1 fails the gate with a refused envelope; the report plus extracted base/candidate fact records land next to the report file.
3. **Plan a pinned update (read-only)** — `wild update plan --request update.json --output plan.json` → an `update-plan` record with the exact manifest edit; never executes project code or writes to the bundle.

## Commands

| Command | What it does | When |
|---|---|---|
| `wild extract --request <file> --output <dir>` | Extract contract/demand/provenance records from a bundle | Building the facts a check consumes |
| `wild check --request <file> --format json --report <file>` | Check base/candidate compatibility, write the check report | Gating an upgrade |
| `wild update plan --request <file> --output <file>` | Produce a pinned-update plan without executing anything | Planning a dependency bump |
| `wild v1` | v1 protocol helpers (canonicalization, `accretes`) | Working with wire formats directly |

Every command prints a v1 envelope on stdout; exit 0 = accept, 1 = refuse, 2 = error. Details in the [manual](docs/wild-manual.md); recurring questions in the [FAQ & troubleshooting](docs/src/faq.md).

## Contract bundle

Every release ships `wild-<version>-contract-bundle.tar.gz` — the extracted
structural contract (`contract.json`) plus a digest-bound `manifest.toml`,
consumed by the wild contract checker. The manifest is the trust-chain head:
verify the bundle before use with

```sh
tar xzf wild-<version>-contract-bundle.tar.gz
test "sha256:$(sha256sum contract.json | cut -d' ' -f1)" = \
  "$(grep contract_sha256 manifest.toml | cut -d'"' -f2)" && echo verified
```

A `contract_sha256` mismatch means the bundle was tampered with or corrupted —
refuse it (diagnostic `bundle-digest-mismatch` at the consumer side).

## Layout

| Path | What it is |
|---|---|
| `docs/wild-manual.md` | How the tool works and how to use it (start here) |
| `docs/integration-failures.md` | 112 integration failure cases with verdicts against the design |
| `docs/integration-failures-part2.md` | 50 more cases (113 to 162); rows 113 to 122 web-checked, the rest from memory |
| `src/` | Rust implementation of the `wild extract` and `wild check` subcommands (beads wild-mh5.x) |
| `openspec/specs/` | Ten specodelic specs (`wild`, `wild-core`, `wild-tiers`, `wild-compose`, `wild-registry`, `wild-bridge`, `wild-adopt`, `wild-deploy`, `wild-evaluate`, `wild-extract`) |
| `prototype/wild_sim.py` | Toy checker: tier pipeline, accretion relation, tombstones |
| `prototype/wild_proto.py` | Prototype extractors (Rust via tree-sitter, Python via ast) and demand extraction |
| `prototype/wild_cat_sim.py` | Category-law, substitution, resolution, and certificate simulations |
| `prototype/wild_cd_sim.py` | Continuous-deployment simulations |
| `results/` | Saved outputs of the two simulation scripts |
| `experiments/` | Tests on real projects (genesis-vibes, specodelic, Flask/Werkzeug, requests/urllib3); see `RESULTS.md` |
| `superseded/` | Earlier single-file specs, replaced by `openspec/specs/` |
| `book.toml`, `docs/src/` | mdBook sources for the deployed site; the docs workflow also mirrors the specs |

## Verify the specs

With the `specodelic` binary (v0.4.0 was used):

```
specodelic lint openspec/specs
specodelic graph openspec/specs        # expect no dangling references
```

Last run: ten files, no issues, no warnings. Compile, model-check, and verify were not run.

## Run the prototypes

Python 3.12, standard library only for the simulations:

```
python3 prototype/wild_sim.py        # round-1 scenarios
python3 prototype/wild_cd_sim.py     # deployment simulations
python3 prototype/wild_cat_sim.py    # laws, resolution, certificates (a few minutes)
```

`wild_proto.py` needs `pip install tree-sitter tree-sitter-rust`.

## The experiments need setup

The scripts in `experiments/` read data from `/tmp/proj` (genesis-vibes crates from crates.io, specodelic release tarballs and binaries from GitHub, Python wheels from PyPI). Those downloads are not in this bundle. `RESULTS.md` records what was fetched and what was found; adjust the paths if you re-run.

## Read results with care

- The simulations use small synthetic models with assumed parameters. They support the model and say nothing about real registries.
- The real-project experiments are small (two Python pairs with 28 combinations, one Rust pair, three CLI releases). Two extractor fixes were made after seeing failures, so those numbers are optimistic.
- Undeclared behavior is the known weak spot; the design reaches it only through laws and evidence.

## Wire formats and validation

[Wild v1 formats](docs/wild-formats-v1.md) defines the normative design protocol; [the JSON Schema](schemas/wild-v1.schema.json) and [structural examples](schemas/examples-v1.json) cover contracts, manifests, locks, sidecars, policy and certificate bundles. The prototypes are smaller models and do not implement this protocol.

Install document-test dependencies with `python3 -m pip install -r requirements-dev.txt`. Strict OpenSpec validation, specodelic lint/reference checks, schema validation, and expected round-1 prototype decisions are executable gates. Future runtime acceptance cases are labelled separately in each spec.
