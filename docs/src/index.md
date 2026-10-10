> *"Oh baby baby, it's a wild world*
> *It's hard to get by just upon a smile*
> *Oh baby baby, it's a wild world*
> *I'll always remember you like a child, girl"*
> — Cat Stevens

# wild

**wild** is a language-agnostic test selection engine... no — that's its
sibling. **wild** does machine-checked compatibility and composition of
software components, modelled as a category of contracts: contracts declare
what a component provides and requires, tiers order ecosystem authority, and a
checker verifies structural compatibility — first-party or third-party —
before an update ships.

Part of the [charly-vibes](https://github.com/charly-vibes) toolshed.

## Status

A design with a prototype and a Rust implementation. The `wild extract` and
`wild check` subcommands are implemented and runtime-tested; the manual
describes the intended interface and marks what is implemented.

**Crates.io.** The publishable package is `wild-vibes` — the `wild` crate name
on crates.io belongs to an unrelated glob-expansion crate. The repository,
binary, and wire-format identities remain `wild`.

## Quick Start

```bash
git clone https://github.com/charly-vibes/wild
cd wild
cargo build

# Extract design contracts from a Rust crate (beads wild-mh5.x)
./target/debug/wild extract --request request.json --output out/

# Run a scoped structural check against the extracted artifact
./target/debug/wild check --request request.json --format json --report report.json
```

## Key Concepts

- **Contracts**: structural manifests of what a component provides and requires
- **Tiers**: ecosystem ordering — language standard library above frameworks,
  frameworks above first-party code
- **Compatibility checking**: machine-checked structural conformance of
  candidate updates against declared contracts
- **Semantic composition**: how compatibility composes (and where it doesn't) —
  see the [Specodelic specs](specs/wild-core.md)

## Continue

- Read the complete [wild manual](wild-manual.md).
- Read the normative [wild v1 formats](wild-formats-v1.md) — protocol for
  contracts, manifests, locks, sidecars, and bundles.
- Browse the [Specodelic specs](specs/wild-core.md) backing the design.
- Skim the [integration failures](integration-failures.md) verdict reports.
- Machine-readable landing: [llms.txt](https://wild.charlyvibes.com/llms.txt).
