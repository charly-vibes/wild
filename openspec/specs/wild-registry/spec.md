---
id: spec
kind: intent
statement: THE wild registry SHALL record revisions in an append-only, signed, auditable log and bind them to host ecosystem artifacts without altering those artifacts.
---

# Wild registry

## Purpose

This is a normative design specification; only the prototype and corpus gate scenarios explicitly identified below are implemented. Shared wire formats and decision rules are defined in [wild v1 formats](../../../docs/wild-formats-v1.md) and [the v1 schema](../../../schemas/wild-v1.schema.json).

The shared memory of the system: a authenticated hash-chained log with full v1 prefix proofs of signed revisions, adapters, advisories, and attestations. Consumers pin hashes from it. Host ecosystems (npm, Cargo, PyPI, Maven, containers) are never modified; a sidecar record ties a host artifact digest to a revision hash.

## Constraints

| id | kind | expr | traces_to |
| -- | ---- | ---- | --------- |
| registry_append_only | invariant | `the registry is a authenticated hash-chained log with full v1 prefix proofs; no revision is deleted or mutated after append` | [[spec]] |
| consistency_proofs | invariant | `any two log heads can be checked for consistency by a proof, so a mirror can be audited` | [[spec]] |
| signature_required | invariant | `every submitted revision carries a signature by the lineage owner key` | [[spec]] |
| namespace_ownership | invariant | `each authority-qualified lineage name maps to one active owner key at a log sequence; bootstrap requires a trusted namespace authority signature and public names never shadow a configured private authority` | [[spec]] |
| key_rotation_signed | invariant | `normal key rotation requires outgoing and incoming key signatures; compromise recovery requires the recovery key designated at namespace bootstrap, revokes the compromised key at an explicit sequence, and never rewrites historical entries` | [[spec]] |
| lock_pins_hashes | invariant | `every contracted v1 lock entry pins authority, lineage, contract hash, and artifact digest; unresolved host entries preserve their locator with Unknown status; tags and aliases are not identities` | [[spec]] |
| sidecar_binds_artifact_digest | invariant | `a signed v1 sidecar binds host ecosystem, artifact locator, artifact digest, contract hash, extractor digest, and registry sequence; fetching bytes with a different artifact digest is rejected even if the contract is unchanged` | [[spec]] |
| ecosystem_untouched | invariant | `wild never replaces or mutates the host ecosystem's package, tag, or version; it adds a sidecar record` | [[spec]] |
| advisories_never_delete | invariant | `yanking or flagging a revision appends an advisory edge; the revision stays resolvable by hash` | [[spec]] |
| retraction_only_experimental | invariant | `experimental retraction appends a notice and removes the revision from new tip selection; hash lookup retains bytes and notice; stable retraction is refused; no candidate yields Unknown` | [[spec]] |
| mirror_equivalence | invariant | `a mirror serving the same authenticated snapshot yields the same verdicts and certificates as the origin for identical caller policy, trust roots, and evaluation time` | [[spec]] |
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

## Design acceptance cases

These cases define future runtime behavior. They are not claims that the current prototypes implement the v1 protocol. Executable document and prototype gates are under Requirements.

### Rule: Registry append only

The system SHALL satisfy `registry_append_only` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Rewrite of appended rejected
- **GIVEN** the fixture domain `log_with_attempted_rewrite()`
- **WHEN** the `registry_append_only` check runs
- **THEN** `append(log, rewrite) == rejected`

### Rule: Consistency proofs

The system SHALL satisfy `consistency_proofs` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Inconsistent heads detected
- **GIVEN** the fixture domain `two_heads_from_forked_logs()`
- **WHEN** the `consistency_proofs` check runs
- **THEN** `consistency_check == failed`

### Rule: Signature required

The system SHALL satisfy `signature_required` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Unsigned revision rejected
- **GIVEN** the fixture domain `submission_without_signature()`
- **WHEN** the `signature_required` check runs
- **THEN** `sign == rejected`

### Rule: Namespace ownership

The system SHALL satisfy `namespace_ownership` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Foreign owner rejected
- **GIVEN** the fixture domain `publish_to_lineage_with_different_key()`
- **WHEN** the `namespace_ownership` check runs
- **THEN** `sign == rejected`

### Rule: Key rotation signed

The system SHALL satisfy `key_rotation_signed` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Rotation needs outgoing key
- **GIVEN** the fixture domain `rotation_signed_with_new_key_only()`
- **WHEN** the `key_rotation_signed` check runs
- **THEN** `rotation == rejected`

### Rule: Lock pins hashes

The system SHALL satisfy `lock_pins_hashes` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Alias in lock rejected
- **GIVEN** the fixture domain `lockfile_entry_using_tag("latest")`
- **WHEN** the `lock_pins_hashes` check runs
- **THEN** `check(lock) == failed`

### Rule: Sidecar binds artifact digest

The system SHALL satisfy `sidecar_binds_artifact_digest` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Digest mismatch rejected
- **GIVEN** the fixture domain `sidecar_pointing_at_a_different_artifact()`
- **WHEN** the `sidecar_binds_artifact_digest` check runs
- **THEN** `check(sidecar) == rejected`

### Rule: Ecosystem untouched

The system SHALL satisfy `ecosystem_untouched` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Host artifact unchanged
- **GIVEN** the fixture domain `publish_with_wild_enabled()`
- **WHEN** the `ecosystem_untouched` check runs
- **THEN** `host_artifact(before) == host_artifact(after)`

### Rule: Advisories never delete

The system SHALL satisfy `advisories_never_delete` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Yanked revision still resolves
- **GIVEN** the fixture domain `yanked_revision()`
- **WHEN** the `advisories_never_delete` check runs
- **THEN** `resolve_by_hash == found ∧ advisory attached`

### Rule: Retraction only experimental

The system SHALL satisfy `retraction_only_experimental` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Stable retraction rejected
- **GIVEN** the fixture domain `retract_request_on_stable_lineage()`
- **WHEN** the `retraction_only_experimental` check runs
- **THEN** `retract == rejected`

### Rule: Mirror equivalence

The system SHALL satisfy `mirror_equivalence` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Mirror matches origin
- **GIVEN** the fixture domain `same_log_served_by_origin_and_mirror()`
- **WHEN** the `mirror_equivalence` check runs
- **THEN** `verdicts(origin) == verdicts(mirror)`

### Rule: Verification needs no write

The system SHALL satisfy `verification_needs_no_write` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Read only credentials suffice
- **GIVEN** the fixture domain `resolve_and_verify_with_read_only_access()`
- **WHEN** the `verification_needs_no_write` check runs
- **THEN** `completes`

#### Acceptance case: Private namespace cannot be shadowed
- **GIVEN** a lock pins authority private.example and lineage acme.billing
- **WHEN** a public registry publishes the same lineage spelling
- **THEN** resolution retains the pinned authority and refuses public substitution

#### Acceptance case: Recovery follows the predesignated key
- **GIVEN** the owner key is compromised and a recovery key was designated at bootstrap
- **WHEN** a replacement key is submitted without outgoing-owner authorization
- **THEN** it is accepted only through the authenticated recovery entry; forged recovery refuses

#### Acceptance case: Retraction preserves pinned bytes
- **GIVEN** an experimental tip is retracted
- **WHEN** a pinned hash is read and a new unconstrained lookup runs
- **THEN** hash lookup returns bytes and notice; new lookup excludes the retracted tip and returns Unknown if no candidate exists

## Requirements

### Requirement: Wild registry design contract

The design corpus SHALL expose this capability's constraints as normative, self-contained rules with acceptance cases, and SHALL link to a structurally valid shared v1 schema without claiming future runtime behavior is implemented.

#### Scenario: Wild registry design is self-contained
- **GIVEN** this spec, `docs/wild-formats-v1.md`, and `schemas/wild-v1.schema.json`
- **WHEN** the design contract gate checks normative rule coverage, local references, and the shared schema
- **THEN** every constraint has a corresponding rule and acceptance case
- **AND** both referenced files exist and the schema is valid JSON Schema draft 2020-12
- **AND** this capability is discoverable by strict OpenSpec validation
