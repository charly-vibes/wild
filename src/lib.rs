// Purpose: Library root of the wild extractor (beads wild-mh5.1, wild-mh5.2).
// Responsibilities: Declare the strict v1 JSON formats module, the
//   rust-cargo-local-1 extraction module, and the scoped structural check
//   module for the `wild` binary.
// Rationale: A thin library root keeps the executable entrypoint separate
//   from the testable format, extraction, and check logic, matching the
//   slices' proposed layout (src/{main,lib,formats,extract,check}.rs).

pub mod check;
pub mod extract;
pub mod formats;
