# Investigation baseline — before Rule-of-5 refinement

This is a frozen summary of the preceding discussion, not a new normative spec.

## Scope

The semantic report proposes a supported translation from Specodelic obligations to Wild laws, with independent observation/harness evidence. The hierarchical report proposes comparing manual wrappers, first-class composites, and flattening-only assemblies. Wild already specifies structural composition but does not give assemblies a recursive public contract.

## Semantic connection

Wild laws carry an id, suite digest, and slot scope. A translation must give Specodelic obligations executable meaning; copying prose to a law identifier only preserves traceability. The pending local-checking proposal already separates accepted obligations from mined facts and protects the base harness. The exact Specodelic executable subset has not yet been inspected locally in this investigation.

## Hierarchy

Distinguish assembly grouping, a reusable public component boundary, and deriving parent guarantees from children. Existing assembly composition is disjoint union with explicit renaming and bindings. The schema lacks public contract/export mapping fields.

## Example

A reservation coordinator and store expose hold, confirm, and expire. Replacing a store with unchanged signatures but weaker atomicity could allow both confirmation and expiration. Structural checks could pass; a parent behavioral check must detect the violation. Preserving external traces would be a successful replacement.

## Recommendation

Start with an authored wrapper boundary, check the internal assembly explicitly, and evaluate public laws independently. Hiding internals must not hide dependencies, singleton conflicts, or failed relations. An internal artifact change must trigger fresh behavioral evaluation even if the public contract is unchanged. Added metadata needs a separately versioned format.

## Validation recorded in preceding discussion

Wild HEAD: 60b860bc4a215f8a0825a21e3079b5afbaeee359, with a dirty working tree. Twenty-two focused spec/prototype tests passed; one full category simulation test was deselected. Reduced category, 1,000-substitution, and ten-certificate studies passed within the toy model. No v1 runtime or cross-language pilot was executed.

## Open decision

Should hierarchy package and check an authored public contract, or derive it and its guarantees from the children? Tentative answer: authored first. No comparative case matrix, measurement thresholds, or concrete observation protocol was recorded in that discussion.
