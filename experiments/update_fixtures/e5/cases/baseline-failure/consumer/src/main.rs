// Purpose: Consumer binary exercising the dept API kept across 1.2.x and 2.0.0.
// Responsibilities: Call exactly the API the frozen catalog marks as used
//   and untouched by the 2.0.0 removal.
// Rationale: `greet` survives the excluded major, so a hypothetical
//   2.0.0 consumer would build and test green — the range excludes a
//   compatible major while permitting the breaking 1.2.4 patch.
fn main() {
    println!("{}", dept::greet("consumer"));
}
