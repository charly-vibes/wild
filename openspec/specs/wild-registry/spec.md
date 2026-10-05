---
id: spec
kind: intent
statement: THE wild registry SHALL record revisions in an append-only, signed, auditable log and bind them to host ecosystem artifacts without altering those artifacts.
---

# Wild registry

The shared memory of the system: a Merkle-chained log of signed revisions, adapters, advisories, and attestations. Consumers pin hashes from it. Host ecosystems (npm, Cargo, PyPI, Maven, containers) are never modified; a sidecar record ties a host artifact digest to a revision hash.

## Constraints

| id | kind | expr | traces_to |
| -- | ---- | ---- | --------- |
| registry_append_only | invariant | `the registry is a Merkle-chained log; no revision is deleted or mutated after append` | [[spec]] |
| consistency_proofs | invariant | `any two log heads can be checked for consistency by a proof, so a mirror can be audited` | [[spec]] |
| signature_required | invariant | `every submitted revision carries a signature by the lineage owner key` | [[spec]] |
| namespace_ownership | invariant | `each lineage name maps to one owner key` | [[spec]] |
| key_rotation_signed | invariant | `key rotation is a log entry signed with the outgoing key` | [[spec]] |
| lock_pins_hashes | invariant | `every lockfile entry is lineage@hash; tags and aliases never resolve` | [[spec]] |
| sidecar_binds_artifact_digest | invariant | `a sidecar record names the host artifact digest and the revision hash it describes; a mismatch is rejected` | [[spec]] |
| ecosystem_untouched | invariant | `wild never replaces or mutates the host ecosystem's package, tag, or version; it adds a sidecar record` | [[spec]] |
| advisories_never_delete | invariant | `yanking or flagging a revision appends an advisory edge; the revision stays resolvable by hash` | [[spec]] |
| retraction_only_experimental | invariant | `only a revision of an experimental lineage may be retracted, with a notice; retraction is itself a log entry` | [[spec]] |
| mirror_equivalence | invariant | `a mirror serving the full log yields the same verdicts and certificates as the origin` | [[spec]] |
| verification_needs_no_write | invariant | `reading, resolving, and verifying never require write access to the registry` | [[spec]] |

## Model

### States

- `submitted`
- `signed`
- `appended`
- `advised`
- `retracted`

### Transitions

| id | from | to | guard |
| -- | ---- | -- | ----- |
| sign | submitted | signed | [[spec.signature_required]] ∧ [[spec.namespace_ownership]] |
| append | signed | appended | [[spec.registry_append_only]] |
| advise | appended | advised | [[spec.advisories_never_delete]] |
| retract | appended | retracted | [[spec.retraction_only_experimental]] ∧ per wild-core `stability_tiers` |

## Properties

| id | kind | derives_from | generator | predicate |
| -- | ---- | ------------ | --------- | --------- |
| rewrite_of_appended_rejected | unit | [[spec.registry_append_only]] | `log_with_attempted_rewrite()` | `append(log, rewrite) == rejected` |
| inconsistent_heads_detected | unit | [[spec.consistency_proofs]] | `two_heads_from_forked_logs()` | `consistency_check == failed` |
| unsigned_revision_rejected | unit | [[spec.signature_required]] | `submission_without_signature()` | `sign == rejected` |
| foreign_owner_rejected | unit | [[spec.namespace_ownership]] | `publish_to_lineage_with_different_key()` | `sign == rejected` |
| rotation_needs_outgoing_key | unit | [[spec.key_rotation_signed]] | `rotation_signed_with_new_key_only()` | `rotation == rejected` |
| alias_in_lock_rejected | unit | [[spec.lock_pins_hashes]] | `lockfile_entry_using_tag("latest")` | `check(lock) == failed` |
| digest_mismatch_rejected | unit | [[spec.sidecar_binds_artifact_digest]] | `sidecar_pointing_at_a_different_artifact()` | `check(sidecar) == rejected` |
| host_artifact_unchanged | unit | [[spec.ecosystem_untouched]] | `publish_with_wild_enabled()` | `host_artifact(before) == host_artifact(after)` |
| yanked_revision_still_resolves | unit | [[spec.advisories_never_delete]] | `yanked_revision()` | `resolve_by_hash == found ∧ advisory attached` |
| stable_retraction_rejected | unit | [[spec.retraction_only_experimental]] | `retract_request_on_stable_lineage()` | `retract == rejected` |
| mirror_matches_origin | unit | [[spec.mirror_equivalence]] | `same_log_served_by_origin_and_mirror()` | `verdicts(origin) == verdicts(mirror)` |
| read_only_credentials_suffice | unit | [[spec.verification_needs_no_write]] | `resolve_and_verify_with_read_only_access()` | `completes` |

## Notes

Failure cases behind this spec: left-pad (an unpublished artifact broke builds), mutable tags (a repointed action tag), dependency confusion (public names shadowing internal ones), and signing-key rotation breaking installs. Registry ownership of names is a governance problem the tool can enforce but not solve (typosquatting remains out of scope).
