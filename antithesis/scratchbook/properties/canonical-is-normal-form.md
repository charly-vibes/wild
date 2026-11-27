# canonical-is-normal-form — evidence

## Identification

Baseline candidate 3 of bd wild-wz9; refined from the suite-level
`properties/wild.md` entry, re-verified at 4e26885.

- Strict parse: `formats::parse`, `src/formats.rs:104` — duplicate object
  keys, floats, BOM, leading zeros, out-of-range integers, invalid UTF-8
  refused (`docs/wild-formats-v1.md` §Encoding).
- Canonical writer: `formats::canonical` (`src/formats.rs:313`) /
  `write_canonical` (`:319`) — keys sorted by Unicode scalar value, no
  whitespace, `\"`/`\\` escapes, U+0000..U+001F as lowercase `\u00xx`, all
  other scalars literal UTF-8, solidus unescaped, integers base-ten without
  leading zeros or negative zero.
- Digest: sha256 over canonical bytes, `sha256:` + 64 lowercase hex
  (`src/formats.rs`, `sha256_digest`; doc §Encoding: "Raw artifacts use the
  same syntax but hash their exact raw bytes" — never substituted).
- Set ordering: contract slots/tombstones by name, laws by id, relations by
  id, etc. (`docs/wild-formats-v1.md` §Encoding list; enforced semantically
  at `src/v1.rs:150-156`).

## What goes wrong if violated

Digest identity is the substrate of every other document here: lineage tips,
tombstone immutability (`tombstone_history` compares canonical slot types,
`src/v1.rs:943-946`), `type_identical`, the CLI's `accretes-report` and
`checker` fields, and cache keys ("Structural keys are `(old_contract,
new_contract, checker)`", doc §Cache). A canonicalization instability
silently forks or merges contract identity.

## Existing instrumentation vs. missing

`tests/v1_checker.rs:101-118` pins the three canonical examples from the
format document (`{"b":2,"a":1}`, escape spellings). No roundtrip,
idempotence, permutation, or digest-stability properties.

## Seam

None needed: `parse`, `canonical`, and the digest are public; contract-level
permutation checks go through public `validate_contract`.

## Generator sketch

- Strings: `"`, `\`, each control code point U+0000..U+001F, U+2028, non-BMP
  characters (e.g. U+1F600), non-escaped vs escaped spellings of the same
  code point (`\u0061` vs `a`), 4-hex-case mixtures rejected upstream.
- Integers: ±9007199254740991 boundary, values just outside (must be
  refused), `-0` spelled forms, base-ten canonical output check.
- Objects: generated contract documents with permuted key order at every
  level; set arrays shuffled (slots/tombstones by name, laws by id,
  relations by id) — validity verdicts and canonical bytes must be
  permutation-invariant.
- Documents and values: reuse the valid-contract generator from
  `accretes-is-transitive`'s evidence (same module) plus a corruption layer
  for parser-refusal cases (duplicate key, float, BOM, leading zero).

## Predicted red/green

**GREEN.** The writer sorts keys and fixes escaping in one code path; the
strict parser refuses everything the doc forbids. The only plausible red is
an escaping edge (e.g. a control character mis-escaped, or U+2028 mishandled
by a host normalization), which is exactly what the property should pin.

**Open Questions:** None.

## Investigation Log

#### Is U+2028/U+2029 handled by the canonical writer or passed through literally?

- Examined: `src/formats.rs:313-404` (`write_canonical`, `parse_string`,
  `parse_hex4`), `docs/wild-formats-v1.md` §Encoding.
- Found: the doc escapes only quote, backslash, and U+0000..U+001F; "all
  other scalar values are literal UTF-8", so U+2028 passes through
  literally — the writer matches this.
- Conclusion: not a defect; the property pins pass-through behavior so a
  future "escape for JS embedding" change is a conscious doc+code change.
