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
2. When the user has not supplied a complete structured task, conduct the
   agent-led intake below before drafting.
3. Identify content type, topic, language, audience, intent, platform, author
   perspective, skill, constraints, source requirements, risk level, and visual
   mode.
4. Resolve only relevant modules through `registry/objects.json`.
5. Separate verified facts, source claims, opinions, inferences, assumptions,
   and unknowns.
6. Do not draft until the minimum context gate passes.
7. Design the content around the reader's question, not a fixed template.
8. Make an explicit media decision: `none`, `auto`, or `required`.
9. Draft for meaning first.
10. Generate a visual only after its purpose, factual basis, and constraints
    are clear.
11. Run applicable reviewers.
12. Revise concrete findings, not unaffected text.
13. Return the final artifact separately from visual assets, source notes, and
    review output, and retain the normative audit record.

## Agent-led intake

When the request is conversational rather than a complete task record, the
agent MUST lead the briefing:

1. Extract everything the user already supplied.
2. Ask only questions whose answers could materially change the subject,
   audience, reader outcome, evidence boundary, format, platform, legitimate
   author position, constraints, or visual requirement.
3. Ask one short batch of at most five questions and wait for the answers.
4. Do not repeat answered questions.
5. Do not ask the user to build a claim ledger, classify evidence, resolve
   modules, check freshness, or perform other work the agent can do.
6. Treat “use your judgment” as authority to choose only low-risk editorial
   defaults; it does not authorize invented facts, experience, sources, rights,
   or consent.
7. After each answer batch, update the resolved brief and ask the next smallest
   necessary batch. Draft only when no material user question remains and the
   context gate passes.

Prefer this order:

1. exact subject and desired reader outcome;
2. audience, artifact type, and platform;
3. supplied sources or permission to research;
4. author perspective, sensitive constraints, deadline, and disclosures;
5. whether a visual is required, optional, or unnecessary.

Ask topic-specific follow-ups only when applicable. For example, science may
need the study and evidence boundary; technology may need product version and
environment; entertainment may need the exact work, edition, spoiler boundary,
and review criteria.

For machine-assisted intake, use `python3 tools/hwr.py --json runs questions`.
The command emits a bounded question batch and separates user questions from
agent-owned actions.

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
