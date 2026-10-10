// Purpose: Hidden acceptance suite for the dynamic-usage task (aoq.3).
// Responsibilities: Adjudicate the macro-based behavior the checker
//   treatment abstains on, from outside the candidate workspace.
// Rationale: The oracle can adjudicate behavior the treatment cannot
//   statically verify; the abstention stays unknown and is never relabelled.
#[test]
fn greets_dynamically() {
    assert!(dept::greetings!("consumer").contains("consumer"));
}
