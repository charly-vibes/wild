// Purpose: bounded demand-path resolution for the rust-cargo-local-1
//   profile (beads wild-158) — the single place that turns a syntactic
//   path into a crate-qualified demand target under design ruling D1.
// Responsibilities: own the bounded resolution rules (declared dependency
//   heads, import aliases with rest, crate-qualified heads, module-relative
//   multi-segment candidates validated at demand-resolution time), the
//   demand-entry recording shared by direct calls, expression paths,
//   struct literals, and method calls, and the method-receiver resolution
//   shapes (constructor calls with recorded return types, plain type
//   paths) — never type inference beyond those shapes.
// Rationale: keeping resolution semantics out of extract.rs honors the
//   pretender line-count ratchet (mirroring extract/mod_files.rs) and makes
//   the "gaps never cure silently" rule auditable in one place.

use super::*;

impl<'a> SourceWalk<'a> {
    /// module-relative same-crate candidate for a locally-written path
    /// (wild-158): paths resolve relative to the current module, so the
    /// candidate is validated against the inventory at demand-resolution
    /// time instead of being resolved by identifier guessing here.
    pub(super) fn module_relative_target(&self, joined: &str) -> String {
        if self.module_prefix.is_empty() {
            format!("{}::{joined}", self.crate_name)
        } else {
            format!(
                "{}::{}::{joined}",
                self.crate_name,
                self.module_prefix.join("::")
            )
        }
    }

    /// Bounded demand-path resolution (wild-158). Returns the
    /// crate-qualified target and, when the head was an import alias, the
    /// alias name. Resolution is purely syntactic against the declared
    /// workspace facts: declared dependency heads, import aliases,
    /// crate-qualified heads, and local module-relative multi-segment
    /// paths. Module-relative candidates are validated against the
    /// inventory at demand-resolution time — an unknown candidate keeps
    /// the honest incomplete-demand gap there, never an invented
    /// resolution. Bare single-segment and `self`/`super`-qualified paths
    /// stay outside the demand profile (unchanged treatment).
    pub(super) fn bounded_target(
        &self,
        head: &str,
        rest: &[&str],
    ) -> Option<(String, Option<String>)> {
        if rest.is_empty() {
            return self
                .alias_map
                .get(head)
                .map(|t| (t.clone(), Some(head.to_string())));
        }
        if self.dep_names.iter().any(|d| d == head) {
            return Some((format!("{head}::{}", rest.join("::")), None));
        }
        if let Some(target) = self.alias_map.get(head) {
            return Some((
                format!("{target}::{}", rest.join("::")),
                Some(head.to_string()),
            ));
        }
        if head == "crate" || head == self.crate_name {
            return Some((
                format!("{}::{}", self.crate_name, rest.join("::")),
                None,
            ));
        }
        if head == "self" || head == "super" {
            return None;
        }
        let joined = format!("{head}::{}", rest.join("::"));
        Some((self.module_relative_target(&joined), None))
    }

    /// Record one demand entry against an already-resolved target
    /// (wild-158 method-call resolution routes here). Unsupplied provider
    /// sources keep the incumbent gap; slot presence is validated at
    /// demand-resolution time.
    pub(super) fn record_resolved_demand(
        &mut self,
        target: &str,
        alias: Option<&str>,
        span: proc_macro2::Span,
    ) {
        if let Some(provider_slot) = self.meaning_of(target) {
            self.demand.push(formats::obj(vec![
                ("consumer", formats::s(&self.crate_name)),
                ("called", formats::s(target)),
                (
                    "alias",
                    match alias {
                        Some(a) => formats::s(a),
                        None => Value::Null,
                    },
                ),
                ("provider_slot", formats::s(&provider_slot)),
            ]));
            let loc = span.start();
            self.locations.push(formats::obj(vec![
                ("slot", formats::s(target)),
                ("file", formats::s(&self.current_file)),
                ("line", formats::i(loc.line as i64)),
                ("col", formats::i(loc.column as i64)),
            ]));
        } else {
            self.gap(
                "incomplete-demand",
                format!(
                    "demand `{target}` cannot resolve: provider source is not supplied in the bundle"
                ),
                true,
            );
        }
    }

    pub(super) fn record_demand(&mut self, callee: &str, span: proc_macro2::Span) {
        let mut parts = callee.split("::");
        let head = parts.next().unwrap_or("").to_string();
        let rest: Vec<&str> = parts.collect();
        let Some((target, alias)) = self.bounded_target(&head, &rest) else {
            // `self`/`super`-qualified multi-segment paths stay outside the
            // demand profile (unchanged incumbent treatment)
            return;
        };
        self.record_resolved_demand(&target, alias.as_deref(), span);
    }
}
