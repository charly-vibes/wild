// Purpose: Library root of the wild extractor (beads wild-mh5.1, wild-mh5.2,
//   wild-nic.1, wild-3rr bounded v1-reader slice).
// Responsibilities: Declare the strict v1 JSON formats module, the
//   rust-cargo-local-1 extraction module, the scoped structural check
//   module, the authored-obligation enforcement module, the sandboxed
//   law-execution harness, the read-only update-planning module, and the
//   v1 canonical reader with semantic contract validation and the
//   subtype/accretion checkers for the `wild` binary.
// Rationale: A thin library root keeps the executable entrypoint separate
//   from the testable format, extraction, check, harness, and update
//   logic, matching the slices' proposed layout
//   (src/{main,lib,formats,extract,check,harness,obligations,update}.rs).

pub mod check;
pub mod extract;
pub mod formats;
pub mod harness;
pub(crate) mod obligations;
pub mod cargo_host;
pub mod update;
pub mod v1;
