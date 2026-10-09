// Purpose: Dynamic-usage consumer test for the e5 corpus.
// Responsibilities: Call the dept 1.7.0 exported macro whose
//   behavior an independent oracle can adjudicate while a
//   checker treatment abstains.
// Rationale: Retains unresolved dynamic usage under its own
//   label instead of relabelling abstention as detection.
#[test]
fn greets_dynamically() {
    assert!(dept::greetings!("consumer").contains("consumer"));
}
