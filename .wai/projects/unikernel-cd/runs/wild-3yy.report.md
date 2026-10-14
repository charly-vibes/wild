# Implementor report — wild-3yy (functor-signature extraction pilot)

- **Ticket**: wild-3yy (P2, in_progress under epic wild-wsz)
- **Brief**: `.wai/projects/unikernel-cd/briefs/wild-3yy-functor-pilot.md`
- **Session history**: spawned `subagent:wild-3yy` (pid 2871117, nohup+timeout 3600s); the
  subagent landed the RED commit `a27d415` and then **died mid-green** — its spawn log
  contains a provider-side "quota exceeded" termination (VIP.aaa key), not a brief
  failure. **Manual resume per Invariant 6** (wild-7e9 precedent): the lead inspected the
  uncommitted work in flight, diagnosed, completed the slice, and ran all meters fresh.
- **Design rulings D1–D7 + toolchain ruling**: implemented; two lead-side corrections
  disclosed below.

## Sequence followed (red → green → results)

### 1. RED (subagent, before dying)
`tests/test_prototype_smoke.py::test_functor_pilot_extracts_fixture` appended with an
inline OCaml fixture before any implementation existed; proven red (ImportError path) and
committed as `a27d415`.

### 2. GREEN (manual resume)
`experiments/functor_pilot.py` was recovered from the subagent's uncommitted work-in-flight
(15 KB) and completed. Three defects found and fixed during resume, all disclosed:
1. **str/bytes regex** — `_unsupported_counts` ran a str pattern (`INCLUDE_MTO_RE`) against
   the bytes source; fixed by decoding before matching (TypeError made the red test fail).
2. **Grammar-mangled `include module type of X`** — tree-sitter-ocaml parses the top-level
   form as an `ERROR` node plus a spurious bare `module type of X` definition whose
   0/0 counts shadowed the real module type in the test's name-keyed dict. Fix: a
   module_type_definition carrying an ERROR child is never inventoried as a real
   signature (the ERROR stays disclosed in `unsupported_constructs.unparsed_error_nodes`).
3. **LEAD CORRECTION — corpus dirs**: the brief's D2 named `tutorial/` + `example/`;
   at the pin `example/` does not exist and grep verified the functor-bearing devices
   live under `applications/` (e.g. `module Make (DNS : Dns_client_mirage.S)` at
   applications/dun/unikernel.ml:12 — note: applications/dns, typo corrected here).
   `CORPUS_DIRS = ("tutorial", "applications", "device-usage")`; brief amended and the
   correction recorded in the state file and below.

Also completed per D1: `requirements-dev.txt` gained the three pins
(`tree-sitter==0.26.0`, `tree-sitter-rust==0.24.2`, `tree-sitter-ocaml==0.26.0`) with an
explaining comment (tree-sitter-rust was already used undeclared by prototype/wild_proto.py).

### 3. Results + research update
- Full run output saved to `results/functor-pilot-2026-10-14.txt`.
- One measured paragraph appended to the MirageOS observation section of the research
  artifact, citing the headline numbers.

## Green evidence (lead-executed fresh, post-resume)
- `python3 -m pytest tests/test_prototype_smoke.py -q` → **6 passed** in 65.08s
- `python3 experiments/functor_pilot.py` → exit 0; header carries pin
  `52abe5aedb1f19f6dd3a18dc9ad81c766f813ebc` + declared `mirage {>= "4.9.0"}`;
  59 files; 3 module types (9 signature items); 17 functor boundaries (32 parameters);
  1 module application; unsupported_constructs disclosed per-kind
  (with_type_constraints=5, first_class_modules=4, rest 0, sum=9);
  the three D4 sections + verdict line printed
- two consecutive full runs byte-identical: `cmp` exit 0 (no MEASURED lines — D5 total)
- `python3 prototype/wild_sim.py`, `python3 prototype/wild_cd_sim.py` → exit 0 (untouched)

## Pilot verdict (from the output)
OCaml machine-checks 20 signature boundaries (9 shape items) for free across the corpus
with 9 unsupported constructs disclosed; 0 behavioral predicates expressible; wild adds 4
mechanism classes per boundary (law slots, accretion relation, tombstone eligibility,
artifact-bound evidence) = 68 additions over 17 functor boundaries. The signature layer is
a floor, not the contract.

## Follow-up threshold
Not triggered — tree-sitter-ocaml attributed functor parameters/result types reliably on
the real corpus; the declared mirage version was found in mirage-skeleton.opam:13.
