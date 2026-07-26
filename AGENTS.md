# Instructions for AI Agents

This repository is a specification and knowledge base. Do not treat it as one giant prompt.

## Normative authority

RFC-0001 through RFC-0006 are the active normative `1.0.0` profile. Before
changing architecture, object kinds, resolution, pipeline stages, review
semantics, or benchmark claims, read `rfcs/README.md` and every affected RFC.

For an ordinary writing task, begin with the runtime workflow below. Load a full RFC only when resolving ambiguity or auditing conformance; selective context rules still apply.

Runtime modules, examples, and configuration MUST NOT weaken RFC invariants. Examples are informative, not templates or hidden requirements.

## Required workflow

1. Read `core/writing-pipeline.md`.
2. Identify content type, topic, language, audience, intent, platform, author perspective, skill, constraints, source requirements, risk level, and visual mode.
3. Resolve only relevant modules through `registry/objects.json`.
4. Separate verified facts, source claims, opinions, inferences, assumptions, and unknowns.
5. Do not draft until the minimum context gate passes.
6. Design the content around the reader's question, not a fixed template.
7. Make an explicit media decision: `none`, `auto`, or `required`.
8. Draft for meaning first.
9. Generate a visual only after its purpose, factual basis, and constraints are clear.
10. Run applicable reviewers.
11. Revise concrete findings, not unaffected text.
12. Return the final artifact separately from visual assets, source notes, and review output, and retain the normative audit record.

## Non-negotiable rules

- Never invent quotes, statistics, events, features, sources, or personal stories.
- Never present an inference as a verified fact.
- Never conceal uncertainty behind confident prose.
- Do not imitate a named living author or identifiable private person.
- Do not add spelling mistakes or awkwardness to appear human.
- Do not optimize for AI-detector evasion.
- Do not claim the text was written without AI.
- Do not remove disclosure required by law, contract, platform, or context.
- Do not force hooks, lists, emojis, CTA, or controversy.
- Do not copy source wording unless quoting is requested and permitted.
- Do not present a generated illustration as documentary evidence.
- Do not place unsupported numbers, labels, interfaces, people, events, or causal relationships in a visual.
- Do not generate media merely to satisfy a template.

## Minimum modules

- `core.writing-pipeline`
- `core.content-model`
- `core.context-selection`
- one language module
- `rule.source-integrity`
- `rule.human-signals.core`
- one format module when the content type is known
- one topic module for domain-sensitive work; use `topic.general.foundation` as the fallback
- `rule.visual-integrity` and `reviewer.visual` when visuals are `auto` or `required`
- `reviewer.source`
- `reviewer.language`
- `reviewer.human-signals`
- `reviewer.editor`
- format, topic, platform, task, and visual reviewers when applicable
