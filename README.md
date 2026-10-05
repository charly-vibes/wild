# wild

Machine-checked compatibility and composition of software components, modelled as a category of contracts.

**Status.** A design with a prototype, not a finished tool. There is no `wild` command yet. The manual describes the intended interface and marks what is implemented.

## Layout

| Path | What it is |
|---|---|
| `docs/wild-manual.md` | How the tool works and how to use it (start here) |
| `docs/integration-failures.md` | 112 integration failure cases with verdicts against the design |
| `docs/integration-failures-part2.md` | 50 more cases (113 to 162); rows 113 to 122 web-checked, the rest from memory |
| `specs/` | Nine specodelic specs (`wild`, `.core`, `.tiers`, `.compose`, `.registry`, `.bridge`, `.adopt`, `.deploy`, `.extract`) |
| `prototype/wild_sim.py` | Toy checker: tier pipeline, accretion relation, tombstones |
| `prototype/wild_proto.py` | Prototype extractors (Rust via tree-sitter, Python via ast) and demand extraction |
| `prototype/wild_cat_sim.py` | Category-law, substitution, resolution, and certificate simulations |
| `prototype/wild_cd_sim.py` | Continuous-deployment simulations |
| `results/` | Saved outputs of the two simulation scripts |
| `experiments/` | Tests on real projects (genesis-vibes, specodelic, Flask/Werkzeug, requests/urllib3); see `RESULTS.md` |
| `superseded/` | Earlier single-file specs, replaced by `specs/` |

## Verify the specs

With the `specodelic` binary (v0.4.0 was used):

```
specodelic lint specs
specodelic graph specs        # expect no dangling references
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

## Not yet specified

The Contract IR schema and canonical form, the consumer manifest and lockfile formats, and the sidecar record format.
