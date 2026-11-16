# Design: add-declared-bump-derivation

## The trade-off this change settles

**Who is the source of truth for the bump class?** The Rule-of-5 review
(CORR-001) rejected the strong form of "delta kinds ARE the semver decision":
`history_reconstructed` makes version strings weak evidence that never
establishes accretion edges (`wild-adopt/spec.md:19`), and `past_claims_audited`
makes the declared bump an *audited input*, not the decision
(`wild-adopt/spec.md:20`). The settled shape:

1. **Derivation proposes** — the class is computed from the reviewed corpus
   delta (deltas passed proposal review before deployment, so revocation was
   already thought about).
2. **Human can only bump upward** — lowering would let vibes override
   evidence; raising encodes a deliberate conservatism the adopt audit can
   see (the reason is recorded).
3. **Adopt layer audits** — computed verdicts remain ground truth;
   `past_claims_audited` gains a delta-derived declared side to compare
   against, closing the loop it always assumed.

## Unknown stays first-class

House style is never-fabricated (`missing-base-contract` precedent in
add-wild-contract-bundle-convention D3). A missing or non-computable base
corpus yields Unknown + named diagnostic — measured abstention (12/12 rung-1
audits) is the honest ceiling, and a bump generator that guesses through
abstention would reintroduce exactly the vibes this change removes.

## Mapping decisions

- ADDED-only → **minor** (accretes); any MODIFIED/REMOVED → **major**
  (revokes); empty corpus delta → **patch**. The patch case presumes a
  code-only release: the generator classifies the *corpus* delta only;
  code-change detection is out of scope.
- RENAMED requirements are treated as MODIFIED+ADDED (revoke+accrete →
  major); pinned here so the classifier never invents a fifth class.

## Capability placement

- **wild-registry** owns derivation + override: it is the sidecar-record
  layer and already owns the contract-bundle release-artifact requirements
  (from add-wild-contract-bundle-convention); release metadata is its beat.
- **wild-adopt** owns the record: `past_claims_audited` lives there; the
  record format must be auditable without new verdict semantics.
- **wild-bridge** untouched: `legacy_semver_as_attestation`
  (`wild-bridge/spec.md:31`) already frames unattested bumps as unverified
  metadata; delta-derived declarations are a strictly stronger input and need
  no bridge-row change.

## Non-goals

- Standalone bundle-diff tooling (wild-xgd phase scope).
- Per-profile bump semantics (EDGE-002 from the review: profiles beyond
  `rust-cargo-local-1` will need their own extractor coverage before their
  deltas mean anything to the classifier).
- Gating: v1 is advisory; promotion to enforcement is a later change riding
  the adopt ladder (shadow → gate), not this one.
