// Purpose: Test for the greet-only consumer of the excluded-compatible-major
//   cell (e5).
// Responsibilities: Pass against any dept version keeping `greet`,
//   including the excluded 2.0.0.
// Rationale: A green authorized replay at 2.0.0 proves the original range
//   excluded a compatible update.
#[test]
fn greets() {
    assert!(dept::greet("consumer").contains("consumer"));
}
