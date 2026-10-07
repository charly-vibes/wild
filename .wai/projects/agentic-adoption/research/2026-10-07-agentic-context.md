# Agentic coding: decision context

Status: design investigation, not an approved runtime specification.
Date: 2026-10-07. Beads: wild-rl0; comparative validation: wild-1xk.

## Description

The user proposes treating code and contract drafting by agents as fast and cheap. This is the design premise; local total accepted-change cost is unmeasured.
Wild has nine specs and prototypes, but no v1 runtime. Adoption currently requires ordered observe/shadow/gate/native transitions and historical reconstruction. Deployment requires registry and routing coordination.
The recorded 28-cell Python experiment has 24 passing and four failing combinations. Prototype v2 catches one failure, misses three, and falsely blocks none. Version ranges catch three failures, miss one, and falsely block six. Extractors were refined after inspecting outcomes.
The prototype omits type inference for methods on returned values. There is no controlled agent-loop value experiment.

## Diagnosis

Hypothesis A: drafting contracts dominates adoption cost. Agents could reduce it, but no measurements establish that it dominates. It is not grounds to reject the product.
Hypothesis B: sufficient demand extraction and connecting claims to implementations dominate assurance. Returned-object failures support this for the current prototype, not every extractor.
Hypothesis C: review, repair, noisy gates, and preserving intent dominate total accepted-change cost. Plausible, but requires controlled experiments.
Hypothesis D: registry/deployment prerequisites delay first value. They exist in the broad design; a local structural check does not inherently require them.

Missing contracts alone are not a sufficient diagnosis. The scoped problem is reducing the cost of independently accepted agent changes while keeping obligations stable and exposing unknown coverage.

## Scope and alternatives

Evaluate one local language/schema family and existing CI. Select an initial compiler-backed typed extractor from participating repositories. Rust is a candidate because prototypes exist; include macros, features, re-exports, target configuration, and generated inputs. Use Python as a deliberate incomplete-demand stress case.
Compare existing CI, deterministic mining, authored contracts with deterministic checking, and their combination.
Defer universal extraction, global registries, automatic range relaxation, and distributed deployment coordination from the initial product experiment.

## Evidence

Repository sources: experiments/RESULTS.md; prototype/wild_proto.py; openspec/specs/wild-adopt/spec.md; openspec/specs/wild-extract/spec.md; docs/wild-formats-v1.md.

[Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents), 2026-01-09, supports repeat trials, stable environments, and independent outcome grading. This is methodology, not evidence for Wild.
[METR: Changing our productivity experiment](https://metr.org/blog/2026-02-24-uplift-update/), 2026-02-24, discusses selection and measurement limits. Historical productivity estimates are not a universal current constant.

No product effectiveness, performance, or adoption measurements were collected in this session.
