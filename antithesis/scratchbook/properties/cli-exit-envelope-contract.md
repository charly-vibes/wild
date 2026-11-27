# cli-exit-envelope-contract — evidence

## Identification

Baseline candidate 4 of bd wild-wz9 (CLI exit/envelope contract); the
suite-level catalog had no CLI exit-code/envelope properties (recorded as a
coverage gap in `reports/hegel-eval-2026-11-16/README.md` §8), so this one is
new territory, not a refinement.

## The contract, from the source (not from memory)

- Commands and usage strings: `extract --request <file> --output <dir>`
  (``src/main.rs:115``), `check --request <file> --format json --report <file>`
  (`src/main.rs:201`), `update plan --request <file> --output <file>`
  (`:321+`), `v1 accretes --old <file> --new <file> --output <file>`
  (`:696`).
- Envelope members (single constructor `envelope`, `src/main.rs:37-69`):
  `schema_version`, `kind: "envelope"`, `command`, `assurance`, `decision`,
  `tier_reports`, `slots`, `coverage {numerator, denominator, ratio_ppm}`,
  `checker`, `known_consumers`, `undeclared_consumers_covered`,
  `deployment`, `diagnostics` — printed via `formats::canonical`, so stdout
  is byte-deterministic. At the pinned commit 4e26885 stdout is the bare v1
  envelope; an in-flight peer change (bd wild-lof, uncommitted, live tree)
  routes every print through `emit()` → `genesis::wrap`, carrying the v1
  envelope verbatim as `data` of a genesis shell
  (`ok`, `envelope_version`, `cli_version`, `envelope_kind` = ok/check/error,
  `warnings`, `meta`, `src/genesis.rs:26-39`), still canonical JSON. The
  v1 members and the exit mapping are unaffected by the wrapper; only the
  outermost stdout shape changes (see Open Questions).
- Exit mapping: accept 0; computed refusal (decision `refuse`, assurance
  `Reject` or `Unknown`) 1; malformed input / failed orchestration
  (`input-mismatch`, `invalid-contract`, unreadable outputs) 2. Implemented
  per command at `src/main.rs:156,241,392,511,822-826`; header rationale
  `src/main.rs:3-17`.
- `v1 accretes` verdict wiring: Holds → (`accept`, `PassDeclared`, exit 0);
  Breaks → (`refuse`, `Reject`, exit 1); Unknown → (`refuse`, `Unknown`,
  exit 1); invalid documents → (`error`, `Unknown`, `input-mismatch`, exit 2)
  (`src/main.rs:767-828`).
- `--version`/`-V` is a deliberate exception: plain version line, exit 0, no
  envelope (`src/main.rs:833-840`, beads wild-9sm).
- Write scope: only the requested output locations; `check` additionally
  writes fact records under `<report parent>/facts/{base,candidate}/`, which
  is declared contract, not leakage (`src/main.rs:9-15, 300-320`).

## What goes wrong if violated

Consumers (ddl status probes, CI scripts) key on exit codes and parse the
envelope; a non-canonical envelope breaks digest-comparing consumers, a
wrong (exit, decision) pair silently inverts accept/refuse automation, and a
write outside the requested locations violates the no-side-effects guarantee
(`src/main.rs:14-17`).

## Existing instrumentation vs. missing

None: the pytest suites (`tests/test_*.py`) cover integration scenarios end
to end but assert on specific scenarios, not on the generated space of
malformed inputs, flag orders, and arg counts. No property test spawns the
binary today.

## Seam

The binary is the seam; no library changes. In Hegel, a
`#[hegel::state_machine]` whose steps spawn `env!("CARGO_BIN_EXE_wild")` with
generated argv and input files, then assert on stdout bytes, exit status, and
a filesystem diff of the working directory (write-scope check). Runs in the
normal test harness — never inside the Landlock law sandbox
(`src/harness.rs` sandboxes candidate artifacts during law evaluation, not
tests).

## Generator sketch

- Input documents: valid contracts from the shared generator plus a
  corruption layer — truncate mid-object, duplicate a key, float literal,
  unknown `schema_version`/`kind`, wrong set ordering, empty file, unreadable
  path, path that is a directory.
- Argv layer: exact usage, reordered flags, missing/extra args, unknown
  flags, `--version`, `-V`.
- Assertion set per step: stdout parses as one canonical `kind:"envelope"`
  document with the full member set; `(exit, decision)` matches the mapping
  above; requested outputs exist (and only those); diagnostics carry stable
  codes (`input-mismatch`, `invalid-contract`, `accretion-holds`,
  `accretion-breaks`, `accretion-unknown`, `kind-unsupported`).
- Note: `v1 accretes` arg-count check is positional (`args.len() != 9`),
  so arg-shifting mutants are good cases.

## Predicted red/green

**GREEN** predicted: one envelope constructor, mapping reviewed at all five
command paths, canonical rendering shared. Residual risks worth the
property anyway: `ratio_ppm` integer-division rounding at boundary
numerators (`src/main.rs:46-49`; doc says floor(1e6·n/d) — matches, but
nothing pins it), the `--version` early-exit bypassing the envelope, and the
`check` facts-subtree write scope.

**Open Questions:**

- Which stdout shape does the CLI contract pin — bare v1 envelope, or the
  genesis shell from bd wild-lof? `(partial: bd wild-lof is in flight and uncommitted; v1 members and exit mapping are identical under both, only the outermost stdout shape differs)`
- Should the property pin exact `ratio_ppm` floor semantics at boundary
  numerators, or only the `null`-iff-zero-denominator rule? `(partial: doc says floor, code matches at reviewed sites; boundary cases unpinned)`
  - Examined: `src/main.rs:46-49`, `docs/wild-formats-v1.md` §Adoption
    ("ratio_ppm is floor(1000000 * numerator / denominator), or null when
    denominator is zero").
  - Found: identical formula; no test pins rounding at e.g.
    numerator·1e6 not divisible by denominator.
  - Conclusion: include one boundary case in the generator sketch; full
    boundary sweep unnecessary.

#### Which stdout shape does the CLI contract pin — bare v1 envelope, or the genesis shell?

- Examined: live-tree diff of `src/main.rs` (bd wild-lof, uncommitted),
  `src/genesis.rs:26-39` (`wrap`, `shell`), open-spec design note
  `.wai/projects/wild/plans/2026-11-27-behavior-every-wild-command-prints-v1-envelope-wr.md`.
- Found: every `println!(formats::canonical(&envelope…))` call site becomes
  `emit()` → `genesis::wrap`; the v1 envelope is carried verbatim as `data`;
  the shell is canonical JSON; decision maps accept→ok, refuse→check,
  else→error. The v1 member set, exit mapping, and write scope are
  untouched.
- Not found: whether wild-lof lands before wild-dr2 implements these
  properties.
- Conclusion: the invariant is written to hold under either shape (canonical
  stdout carrying the v1 envelope); the Hegel test should accept the shell
  once wild-lof lands. Tagged `(partial)` — implementer re-pins at
  implementation time.
