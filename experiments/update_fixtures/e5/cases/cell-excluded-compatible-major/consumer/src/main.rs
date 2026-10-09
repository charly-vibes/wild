// Purpose: Greet-only consumer for the excluded-compatible-major cell (e5).
// Responsibilities: Use exactly the API that survives the excluded major
//   2.0.0; never touch the farewell API removed by 1.2.4.
// Rationale: The exclusion cell must show the barred major is actually
//   compatible for this consumer — proof the range is miscalibrated.
fn main() {
    println!("{}", dept::greet("consumer"));
}
