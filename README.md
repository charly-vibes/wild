# wild

> *"Oh baby baby, it's a wild world*
> *It's hard to get by just upon a smile*
> *Oh baby baby, it's a wild world*
> *I'll always remember you like a child, girl"*
> — Cat Stevens

Machine-checked compatibility and composition of software components, modelled as a category of contracts.

Part of the [charly-vibes](https://github.com/charly-vibes) toolshed.

**Status.** A design with a prototype and a Rust implementation. The `wild extract` and `wild check` subcommands are implemented and runtime-tested (see `src/` and `tests/runtime/`); the manual describes the intended interface and marks what is implemented.

**Crates.io.** The publishable package is `wild-vibes` — the `wild` crate name on crates.io belongs to an unrelated glob-expansion crate. The repository, binary, and wire-format identities remain `wild`; see `Cargo.toml` for the rationale.

## Layout

| Path | What it is |
|---|---|
| `docs/wild-manual.md` | How the tool works and how to use it (start here) |
| `docs/integration-failures.md` | 112 integration failure cases with verdicts against the design |
| `docs/integration-failures-part2.md` | 50 more cases (113 to 162); rows 113 to 122 web-checked, the rest from memory |
| `src/` | Rust implementation of the `wild extract` and `wild check` subcommands (beads wild-mh5.x) |
| `openspec/specs/` | Nine specodelic specs (`wild`, `wild-core`, `wild-tiers`, `wild-compose`, `wild-registry`, `wild-bridge`, `wild-adopt`, `wild-deploy`, `wild-extract`) |
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

Last run: nine files, no issues, no warnings. Compile, model-check, and verify were not run.

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
