<!-- Purpose: Declared mined-contract feedback for arm B (aoq.3).
     Responsibilities: Stand in for deterministically mined structural
       contracts over the frozen dept catalog.
     Rationale: Only declared feedback varies across arms; this file is the
       arm B treatment input, absent from A. -->
mined contract: dept::greet(name: &str) -> String is preserved across 1.2.3-2.0.0
mined contract: dept::farewell is removed in 1.2.4 and 2.0.0
