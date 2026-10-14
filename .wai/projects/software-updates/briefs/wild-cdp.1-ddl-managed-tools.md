# Brief: wild-cdp.1 — add wild to ddl's MANAGED_TOOLS (fleet bootstrap)

## Why
Delegation rationale: small, fully-specified additive slice in the ddl repo
(`/var/home/sasha/para/areas/dev/gh/charly/dulce-de-leche`) — one registry row, one
docs block line, one compat fallback row, plus whatever the drift and conformance
tests demand. Mechanically executable; the lead orchestrator stays free to verify
and ship. No ddl behavioral change beyond catalog/status presence.

## Ticket
- **ID**: wild-cdp.1 (P2, claimed in this run; epic wild-cdp, rung 0)
- **Desired outcome**: `ddl status` / `ddl catalog` list wild; `tests/tool_registry_drift.rs`
  and any conformance tests stay green; ddl can probe an installed wild's version.

## Design rulings (PRE-APPROVED by lead — implement as stated)
- **D1 — registry row** in `src/platform.rs` `MANAGED_TOOLS`, mirroring the existing
  row shape: `name: "wild"`, `description: "Contract-based compatibility checking for software updates"`,
  `crate_name: "wild-vibes"` (publish name; lib name is `wild`), `formula_name: "wild"`
  (homebrew-charly has no wild formula yet — check: if no formula exists, still set the
  string; formula install is not this slice), `repo: "charly-vibes/wild"`,
  `npm_package: None`, `category: ToolCategory::Extension`, `maturity: Maturity::Prototype`
  (pick the enum variant that matches wild's actual maturity — wild self-describes as
  prototype/prototype gates; if the enum has no Prototype, use the least-mature variant).
- **D2 — docs block**: update the MANAGED-TOOLS managed block in `README.md`
  (Extension count 7→8: "incitaciones, bd, openspec, specodelic, funkalization, wild").
  The drift test `tests/tool_registry_drift.rs` is the harness — add the registry row
  and block line in the SAME commit; the test enforces they move together.
- **D3 — compat fallback row** in `src/compat.rs::embedded()`: `("wild", ">=0.0.0")`.
  Semantics stay version-string-advise-only (matching every other row); this is NOT
  compat-matrix behavior change (anti-goal: no wild-verdict gating in this slice).
- **D4 — version probe**: check how `installer::get_installed_version` resolves
  binaries; if it runs `<binary> --version` generically, nothing to add. If per-tool
  special-casing exists, add wild's (`wild --version` emits a version string).
- **D5 — anti-goals.** No installer/install-method changes. No wild-verdict integration
  (that is rung 2/3). No release/CI changes. Do NOT touch versions.ddl.toml semantics
  (CI pins are a separate deliberate update — leave the pin file alone this slice).

## Exact commands
- Red first: `cargo test --test tool_registry_drift -q` must FAIL after adding the
  registry row alone (or the block line alone) — prove the harness moves with you,
  then make both green.
- Full meter: `JUST_TEMPDIR=/tmp just ci` (ddl repo)
- Status probe: `cargo run --quiet -- status 2>/dev/null | head -30` — wild must appear.

## Commit protocol
- One commit in the ddl repo:
  `feat: add wild to the managed tool registry (wild-cdp.1)`
  Do NOT push and do NOT `bd close` — the orchestrator owns ship.

## Out of scope
compat.json semantics, installer changes, versions.ddl.toml pin bump, any wild-repo
change.
