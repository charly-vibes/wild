// Purpose: Dynamic-usage consumer for the arm-trial comparative fixture.
// Responsibilities: Invoke the dept 1.7.0 exported macro whose expansion the
//   checker treatment cannot resolve into a static API inventory.
// Rationale: Unsupported dynamic usage is retained: the treatment abstains
//   (unknown) while the independent oracle adjudicates actual behavior.
fn main() {
    println!("{}", dept::greetings!("consumer"));
}
