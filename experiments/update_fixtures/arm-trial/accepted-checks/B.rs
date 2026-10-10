// Purpose: Arm B's own accepted obligation for the arm-trial fixture.
// Responsibilities: The common trusted invocation re-enforces this check
//   from its protected host-side copy regardless of workspace edits.
// Rationale: Common protection preserves each arm's actual accepted
//   obligations; deleting the workspace copy never removes enforcement.
#[test]
fn accepted_check_arm_B() {
    assert!(dept::greet("arm-B").contains("arm-B"));
}
