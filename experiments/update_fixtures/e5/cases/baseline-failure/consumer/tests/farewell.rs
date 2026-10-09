// Purpose: Baseline-failure consumer test for the e5 corpus.
// Responsibilities: Fail before any update is attempted.
// Rationale: The cohort must retain a genuine pre-update
//   failure baseline, never folded into update outcomes.
#[test]
fn says_farewell() {
    assert!(false, "baseline is intentionally broken");
}
