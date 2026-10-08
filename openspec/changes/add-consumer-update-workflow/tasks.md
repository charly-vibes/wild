# Implementation sequence

Status lives in Beads wild-nic; wild-mh5 supplies local checking. These ordered delivery criteria do not track status. Runtime work awaits proposal approval.

1. Extend the separate local-1 protocol with update request/plan/authority/report schemas and round-trip fixtures. Keep v1 wire documents unchanged. Test plan-digest binding, base preconditions, package-id ambiguity, and external authority validation.
2. Implement read-only planning and isolated execution plumbing. Exercise unauthorized actions, dirty/stale base commitments, symlink escapes, interrupted execution, and unavailable sandbox restrictions. The original checkout must remain unchanged.
3. Add the Cargo host adapter and frozen local-registry fixture. Prove the original manifest excludes the named candidate; resolve the proposed manifest with actual Cargo and inspect the selected source/target and full dependency closure.
4. Connect contract/policy checks, fixed-lock builds, protected tests/laws, and explicitly supplied migration patches. Test newly introduced transitive requirements, declared singleton conflicts, unsupported runtime/target, and unresolved dynamic demand.
5. Produce a durable pinned diff and report for the compatible major update and refuse the incompatible permitted patch. Test wrong-target selection, write failure, changed commitments after checking, and honest direct/migration/intent-change classification.
6. Reconcile the dual-format design constraints listed in design.md during apply/archive; register only implemented runtime scenarios with espectacular. Run strict validation, overlay correspondence, actual Cargo fixture tests, and repository CI. Hand the fixed runner to wild-aoq before expanding discovery or adding automatic migration generation.
