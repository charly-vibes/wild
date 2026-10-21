## ADDED Requirements

### Requirement: Shadow verdict rendering beside the release decision

During tool upgrade, the consumer-side adoption layer SHALL render the wild compatibility verdict (compatible / incompatible / unknown, with named reasons) beside the existing release decision (semver bump class and release age) in the same output table. The rendered verdict SHALL gate nothing in this stage: exit codes, upgrade gating behavior, and the decision itself SHALL remain unchanged, keeping the shadow path read-only and advisory consistent with `shadow_never_blocks`.

#### Scenario: Verdict renders advisory beside the release decision

- **GIVEN** an upgrade run whose candidate release carries a valid contract bundle and whose installed base has a cached contract
- **WHEN** the upgrade renders its decision
- **THEN** the wild verdict (compatible, incompatible, or unknown with named reasons) appears beside the semver/age decision in the same output, and the upgrade proceeds, defers, or refuses exactly as it would have without the verdict

### Requirement: Shadow verdict production pipeline

To produce the rendered verdict, the consumer-side adoption layer SHALL fetch the candidate release's contract bundle, verify it per the bundle refusal law, load the cached installed base contract, and run the standalone local check candidate-vs-installed-base.

#### Scenario: Invalid bundle is reported, not accepted

- **GIVEN** a candidate whose contract bundle fails digest or commit verification
- **WHEN** the upgrade renders its decision
- **THEN** the wild column reports the named refusal diagnostic instead of a verdict, and the existing decision governs unchanged

### Requirement: Unknown stays first-class in the shadow path

An Unknown verdict SHALL be rendered as Unknown with its named reasons (including `missing-base-contract` and the extractor's measured abstention diagnostics), never reinterpreted as compatible or as a refusal. Bundle presence SHALL NOT imply verdict compatibility.

#### Scenario: Unknown is a first-class rendered verdict

- **GIVEN** a candidate whose check abstains — the base cache is empty (`missing-base-contract`), or the extractor reports its measured residual gaps (non-bounded-receiver method calls, std/external references outside the bundle, trait impls, non-scalar signature fns)
- **WHEN** the upgrade renders its decision
- **THEN** the wild column reads Unknown with the named reasons attached, and the existing decision governs unchanged
