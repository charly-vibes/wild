# Implementation sequence

Status lives in Beads wild-mh5, not this document. These are ordered delivery and acceptance criteria; all runtime work awaits proposal approval.

The initial fixture prerequisite is wild-aoq.5, which supplies independently specified E1/E4 examples and a small native update pair. The full E5 cohort and metric engine do not block the first extraction slice.

1. Define schemas/wild-local-v1.schema.json, examples, and docs/wild-local-v1.md for the record tables in design.md. Test duplicate keys, unknown fields, digest mismatches, and references outside a supplied bundle. Preserve existing v1 examples and semantics.
2. Add the minimal Rust CLI/library layout and v1 canonical reader needed by this profile. Test canonical bytes, semantic validation, and error/refusal/accept exit mapping; reject unsupported protocol features explicitly.
3. Implement immutable input snapshots and externally pinned invocation/obligation records. Test deleted laws, scope/policy/checker changes, stale evidence, and an authorized intentional transition before candidate execution.
4. Implement profile inventory, semantic extraction, demand, and provenance. Test direct calls/aliases, unused versus demanded removals, formatting invariance, changed opaque slots, and macro/generated/dynamic gaps. Repeated clean runs must agree.
5. Connect structural checks and bounded authored suites to the same core and v1 envelopes. Exercise unsupported sandbox capability and inconclusive evidence. Keep ordinary build/test evidence distinct from v1 laws.
6. Register runtime scenario contracts only for implemented behavior; retain existing document/prototype gates. Run strict OpenSpec validation, ah check with the change overlay, real runtime tests, and repository CI. Connect the smallest fixture to wild-nic before expanding the profile.

Release integration, scenario registration and authorized post-delivery archive belong to wild-mh5.5 in the DESIGN lane. The separate REVIEW ticket wild-mh5.6 audits the delivered output and returns defects to its implementation owner; it does not perform integration or archive. Parent completion requires both tickets to succeed.
