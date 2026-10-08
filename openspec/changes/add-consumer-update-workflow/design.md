# Consumer update design

## Context and boundaries

Rust/Cargo is the proposed first host adapter. Use the bounded checker from [local checking](../add-local-contract-checking/design.md). The host resolver remains authoritative for its proposed manifest; Wild validates its actual output. This is an explicit local update mode, separate from advice-only check/observe and from native registry newest-tip resolution.

The first workflow requires a caller-selected exact package identity and release in a finite catalog. A catalog pins index/source archives and their authenticated provenance or explicitly trusted local-fixture origin. Release names locate candidates; source artifact digests identify them; contracts assess declared compatibility. Trust in a fixture catalog must never be reported as publisher attestation.

## Commands and immutable records

```text
wild update plan --request update.json --output plan.json
wild update evaluate --plan plan.json --authority authority.json --output result/
```

Both commands emit the existing v1 envelope. Extend only the separate local-1 schema with plan, authority, and update-report records. JSON record digests follow v1 canonicalization. Planning success means a well-formed eligible proposal, not an accepted compatibility check; include plan-ready diagnostics, Unknown compatibility assurance until checked, and never a completed-update disposition. A plan explicitly reports which checks remain pending.

| Record | Required fields and semantics |
| --- | --- |
| Update request | Immutable base source and manifest/lock commitments, consumer/scope, package id, exact desired release and source artifact digest, catalog snapshot, environment/toolchain/target/features, policy/obligation commitments, and optional supplied migration patch digest |
| Plan | Request digest, original range, exact proposed manifest edit, why the constraint changes, target artifact, allowed changed paths, optional migration digest, required validation commands, and pending checks; edits use base-file digests as preconditions |
| Authority | Trusted invocation identity and project policy commitment authorizing this exact plan digest, allowed edits/actions, and validity context; supplied outside candidate control, including under existing automated policy |
| Update report | Plan/authority/input commitments, v1 envelope and local check report, actual package identities and full lock closure, artifact and build-input digests, command/execution evidence, constraint results, pinned output diff digest, update class, and delivered/refused/unknown/error disposition |

An arbitrary authority.json file supplied by candidate code is not trusted. The invoking CI/local authority must pin its commitment externally using the same mechanism as local checking. No new per-update human approval is required when an existing project policy already authorizes the exact class of edit. If no authority is present, planning remains possible and evaluation refuses before applying changes.

The first adapter accepts one selected Cargo package target and an explicit manifest location. Ambiguous package ids, inherited workspace ranges without an identified owner, unexpected manifest layouts, and unsupported lock versions refuse with diagnostics. It must not guess which dependency declaration to rewrite. The manifest edit pins the desired release exactly; the complete lockfile records the actual closure. A dependency alias is provenance, not an artifact identity.

## State transitions

1. Snapshot the base and record baseline build/test validation as pending. No project code executes during planning.
2. Plan the exact manifest change and supplied migration diff, retaining all unrelated constraints. Planning reads supplied inputs and writes only the requested plan; it does not run candidate code or mutate the project.
3. Verify external authority and all base/plan/configuration commitments. Create a disposable workspace and isolated Cargo home using the catalog. Refuse symlink/path escapes. Tool subprocesses have resource limits and no access to the original worktree or credentials. Verify the baseline build/test there under the frozen environment before candidate edits. Record pre-existing failure rather than attribute it to the candidate; baseline failure prevents validated delivery in this first profile.
4. Apply only the proposed changes. Invoke real Cargo resolution offline with the pinned toolchain, using the exact target selection (for example, cargo update with --precise). Lock generation is intentionally allowed in this step. Do not use --ignore-rust-version or rewrite runtime, target, provenance, license, or organization constraints to make resolution succeed.
5. Read the actual resolved metadata/lock and inspect raw package sources. Verify the intended target was selected from the approved source and that every new/transitive dependency is accounted for. Revalidate selected features, target, supported Rust version, declared singleton constraints, and external policy predicates. Missing evidence for a required constraint yields unknown. Preserve uncontracted dependencies as Unknown entries; host compilation does not manufacture their contracts.
6. Build/test with the lock fixed and the same environment. Confirm those commands did not change manifest/lock/source inputs. Run scoped contract checks and protected base obligations against these exact artifacts. The independent benchmark oracle is separate and never exposed to agents; it grades the produced result afterward. User-provided independent acceptance tests can also be required by the project policy.
7. Produce a diff and report only when required checks pass, all preconditions still match, and output artifacts are durably written. A direct update changes only manifest/lock; a migration includes the supplied consumer/adapter diff. An intent transition is separately labelled. No command applies the diff to the original checkout, publishes, merges, or deploys it.
8. Dispose of the workspace on success/failure, retaining requested reports and failure logs. A crash cannot leave changes in the caller's checkout. Reapplying an old result later requires unchanged base commitments and current policy/evidence evaluation.

Build/test subprocesses use a separate sandbox from strict law execution. A Cargo build is an integration check; compilation may require child processes. Pin the toolchain, environment and local sources, block network and ambient access, and bound time/memory/process count. If the necessary build sandbox is unavailable, fail explicitly rather than claim isolation. Build scripts/proc macros may execute only there, but rust-cargo-local-1 still marks their analysis gaps; a successful build does not remove Unknown demand. Test crashes/timeouts are recorded with a reason; infrastructure errors are distinguished from adjudicated candidate incompatibility.

## Acceptance and identity

Validate every required input in the chosen dependency closure even if the changed provider's public outputs demanded by the root are few. Compare outputs under demand restriction without assuming package-wide accretion. Check Rust source compatibility through the actual consumer build as well as the conservative extraction profile. A local source-bundle digest uses sorted relative paths and raw file digests; a registry archive digest hashes its bytes. Keep these identities and built artifact identities separate and link them in the report.

The compatibility fields retain local-check semantics. A delivered update additionally requires successful actual resolution/build/tests and durable pinned output. A plan or structural pass cannot set delivered. Wrong-target selection is an explicit refusal; an unavailable required blob is unknown or an input error according to whether it is evidence or a mandatory request file. An unsatisfiable Cargo resolution is a refusal with a host-resolution reason, not automatically a structural counterexample. Runtime/platform/policy ineligibility is distinct from compatibility. Report each stage independently so benchmark classification need not infer it from process exit alone.

For migrations, keep the original consumer demand and protected obligations as the comparison baseline, record added/changed consumer demands, and validate the resulting complete closure. Removing an old consumer call does not itself prove its intended behavior was preserved. The first workflow accepts a caller-supplied migration; agent generation is external. A failed direct check may be followed by a separately committed migration plan, not relabelled in place.

## Existing spec reconciliation

During apply/archive, preserve full existing requirement blocks and reconcile dual-format design tables explicitly:

| Location | Integration wording |
| --- | --- |
| wild-adopt safe_update_advice and its property/acceptance case | Advice/check/observe never modify the manifest or host selection. Only explicit update evaluation may apply an authorized proposed manifest in isolation; Cargo selects under that manifest. |
| wild-compose resolution_by_lineage and resolver_deterministic | Retain registry-mode tip selection; local validation accepts a host-selected pinned assembly and makes no newest-tip claim. |
| docs/wild-formats-v1.md host-choice and certificate passages | Clarify the new mode in the local protocol reference; preserve v1 native certificate rules and wire grammar. A local report is not a registry certificate. |

OpenSpec archive applies Requirements deltas, not arbitrary Constraints tables. The implementation sequence therefore includes manual reconciliation plus reference-closure and correspondence checks. No current normative file is edited by this proposal.

## First acceptance fixtures

Use a frozen local Cargo registry with genuine version constraints and archive identities: a 1.x consumer excluding a 2.0 release that removes only an unused function; a permitted 1.x patch removing a used function; an added incompatible transitive dependency; wrong-source/target selection; and a supplied migration preserving protected behavior. Local path substitution that bypasses the version constraint is not a valid range-friction test. Integration failures and analysis gaps must be retained even when a test alone happens to pass.
