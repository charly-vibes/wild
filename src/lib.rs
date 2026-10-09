// Purpose: Library root of the wild extractor (beads wild-mh5.1).
// Responsibilities: Declare the strict v1 JSON formats module and the
//   rust-cargo-local-1 extraction module for the `wild` binary.
// Rationale: A thin library root keeps the executable entrypoint separate
//   from the testable format and extraction logic, matching the slice's
//   proposed layout (src/{main,lib,formats,extract}.rs).

pub mod extract;
pub mod formats;
