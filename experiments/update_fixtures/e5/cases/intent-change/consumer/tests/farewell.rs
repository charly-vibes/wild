// Purpose: Intent-changed consumer test for the e5 corpus.
// Responsibilities: Express the authorized new intent (greet
//   still works) after the intent edit, replacing the former
//   farewell demand.
// Rationale: Authorized intent changes are a declared policy
//   class; the case replays the edited consumer against the
//   previously-breaking patch target.
#[test]
fn intent_now_only_greets() {
    assert!(dept::greet("consumer").contains("consumer"));
}
