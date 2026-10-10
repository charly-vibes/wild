// Purpose: Hidden acceptance suite for the out-of-range-major task (aoq.3).
// Responsibilities: Adjudicate the delivered artifact's greet behavior from
//   outside the candidate workspace; committed before any arm runs.
// Rationale: dept 2.0.0 keeps greet, so an independently compatible verdict
//   is available even though the original manifest range excludes the major.
#[test]
fn greets_after_major_update() {
    assert!(dept::greet("consumer").contains("consumer"));
}
