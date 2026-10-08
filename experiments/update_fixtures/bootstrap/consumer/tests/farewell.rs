// Purpose: Consumer test exercising the dept API removed in the permitted
//   in-range patch 1.2.4.
// Responsibilities: Fail to compile against dept versions lacking
//   `farewell`, and pass against the 1.2.3 baseline.
// Rationale: Demonstrates that an in-range patch breaks the consumer —
//   the misclassification the evaluation harness must expose.
#[test]
fn says_farewell() {
    assert!(dept::farewell("consumer").contains("consumer"));
}
