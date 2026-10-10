// Purpose: Greet-only consumer for the arm-trial comparative fixture (aoq.3).
// Responsibilities: Call the dept API that survives the excluded major 2.0.0.
// Rationale: Range exclusions and authorized delivery are exercised through
//   real Cargo resolution in every arm under identical authority.
fn main() {
    println!("{}", dept::greet("consumer"));
}
