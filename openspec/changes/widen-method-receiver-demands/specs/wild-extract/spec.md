## MODIFIED Requirements

### Requirement: Bounded method-call resolution

A method call whose receiver resolves through the declared receiver rules SHALL create the demand `<crate>::<Type>::<method>`: resolution against the inventoried impl-method or typed slots yields supported demand, and a method absent from the inventory SHALL keep the incomplete-demand gap naming the full path. The declared receiver rules are stated one per scenario below.

#### Scenario: Resolved method call becomes supported demand
- **GIVEN** a consumer whose method call's receiver is a call resolving to an inventoried same-crate constructor with a recorded syntactic return type (e.g. `Meter::new().tick()` where `new` returns `Meter`)
- **WHEN** extraction runs
- **THEN** the demand `Meter::tick` is recorded and resolves against the inventoried type-qualified impl-method slot with no incomplete-demand gap

#### Scenario: Cross-file constructor flow resolves
- **GIVEN** a bundle where a public fn or public inherent method with a recorded return type is declared in one file and a consumer module calls it and then calls a method on the bound result
- **WHEN** extraction runs
- **THEN** the method demand resolves against the inventoried slot with no incomplete-demand gap

#### Scenario: Let-bound local resolves through its initializer
- **GIVEN** a consumer with a single let-binding whose initializer is a resolved call with a recorded return type (e.g. `let r = Meter::new(); r.tick();`)
- **WHEN** extraction runs
- **THEN** the demand `Meter::tick` is recorded with no incomplete-demand gap

#### Scenario: Field-access receiver resolves via inventoried field type
- **GIVEN** a consumer calling a method on a field-access receiver whose public field type is inventoried from the struct declaration (e.g. `store.meter.tick()` where `meter: Meter` is a public field)
- **WHEN** extraction runs
- **THEN** the demand `Meter::tick` is recorded with no incomplete-demand gap

#### Scenario: self receiver inside an inherent impl body resolves
- **GIVEN** a method call on `self` or `Self` inside a public inherent impl on a named path type
- **WHEN** extraction runs
- **THEN** the demand resolves against that impl's inventoried type with no incomplete-demand gap

#### Scenario: Chain with recorded return types resolves hop by hop
- **GIVEN** a consumer with a multi-hop chain whose every callee target has a recorded return type (e.g. `Meter::new().tick().double()`)
- **WHEN** extraction runs
- **THEN** every hop's demand is recorded with no incomplete-demand gap

#### Scenario: Method absent from inventory keeps gap
- **GIVEN** a consumer whose method call's receiver resolves through the declared receiver rules but whose method is absent from the inventory (e.g. `Meter::new().tock()`)
- **WHEN** extraction runs
- **THEN** the report retains the incomplete-demand gap naming the full `<crate>::<Type>::<method>` path and refuses scoped acceptance with Unknown structural assurance

### Requirement: Unbounded method-call receivers stay disclosed

A method-call receiver outside the declared receiver rules — a trait-object or generic-typed receiver, a macro-produced receiver, a closure receiver, a re-bound or re-assigned local, a chain hop whose callee target has no recorded return type, or an unknown identifier — SHALL keep the incomplete-demand gap naming the receiver.

#### Scenario: Unbounded method receiver keeps gap
- **GIVEN** a consumer with a multi-hop method chain whose first hop resolves but whose next callee target has no recorded return type (e.g. `Meter::new().tick().untick()` where `tick` records no return type)
- **WHEN** extraction runs
- **THEN** the report retains the incomplete-demand gap naming the receiver, and the earlier resolved hop's demand is still recorded

#### Scenario: Non-syntactic receivers stay disclosed
- **GIVEN** a consumer with a method call on a trait-object receiver, a macro-produced receiver, or a re-bound local
- **WHEN** extraction runs
- **THEN** the report retains the incomplete-demand gap naming the receiver and refuses scoped acceptance with Unknown structural assurance
