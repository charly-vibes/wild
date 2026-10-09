// Purpose: Library root of the wild extractor (beads wild-mh5.1, wild-mh5.2).
// Responsibilities: Declare the strict v1 JSON formats module, the
//   rust-cargo-local-1 extraction module, the scoped structural check
//   module, the authored-obligation enforcement module, and the sandboxed
//   law-execution harness for the `wild` binary.
// Rationale: A thin library root keeps the executable entrypoint separate
//   from the testable format, extraction, check, and harness logic,
//   matching the slices' proposed layout
//   (src/{main,lib,formats,extract,check,harness,obligations}.rs).

pub mod check;
pub mod extract;
pub mod formats;
pub mod harness;
pub(crate) mod obligations;
