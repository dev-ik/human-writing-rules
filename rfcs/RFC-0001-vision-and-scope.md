---
id: RFC-0001
status: active
revision: 1.0.0
created: 2026-07-25
updated: 2026-07-26
normative: true
---

# Vision, Scope, and Conformance

## Abstract

Human Writing Rules is a vendor-neutral editorial-process specification for producing grounded articles, social posts, and optional visual assets with AI-assisted systems.

This RFC defines the authority, vocabulary, invariants, profiles, boundaries, and conformance claims for the specification. RFC-0002 through RFC-0006 define the operational contracts.

## Status

This document is normative for the stable `1.0.0` profile.

`Stable` means normative RFC and active object identifiers follow the compatibility policy for the 1.x line. An implementation claiming conformance with this revision MUST follow its normative requirements or disclose a permitted `SHOULD` deviation. It MUST NOT treat `MUST` requirements as optional because the implementation, adapter, or workflow is experimental.

## Problem

AI-assisted writing often combines research, author perspective, style, platform conventions, task instructions, review, and media production in one opaque prompt. This creates several failure modes:

- unsupported claims become polished prose;
- platform habits override reader needs;
- a requested tone fabricates authority or personal experience;
- one domain's evidence rules are applied to another;
- generated visuals imply facts that the text does not support;
- revisions create stylistic churn without resolving identified problems;
- quality claims cannot be reproduced because inputs and versions are missing.

The specification addresses these failures by separating concerns into stable modules and requiring observable gates and artifacts.

## Goals

A conforming implementation MUST be able to:

1. frame a writing task before drafting;
2. preserve source identity, dates, scope, and uncertainty;
3. distinguish facts, source claims, opinions, inferences, assumptions, and unknowns;
4. resolve the smallest sufficient module set;
5. prevent drafting when material context is missing;
6. produce text for a selected format, topic, audience, platform, and legitimate author perspective;
7. decide whether a visual has a justified purpose;
8. prevent a generated visual from becoming false documentary evidence;
9. run applicable independent review contracts;
10. revise concrete findings without rewriting unaffected material;
11. return publication copy separately from internal source and review records;
12. report enough execution context for audit and benchmark reproduction.

## Non-goals

The specification does not define:

- one universal prose style or article template;
- a required model, vendor, search provider, image generator, CMS, or orchestration framework;
- guaranteed truth when adequate evidence is unavailable;
- automatic legal, medical, financial, scientific, or professional approval;
- AI-detector evasion or a claim that content was produced without AI;
- permission to fabricate quotations, statistics, events, sources, experiences, emotions, authority, or consensus;
- permission to remove disclosure required by law, contract, consent, platform, or context;
- a universal rating that proves one model or implementation is always better.

## Terminology

### Implementation

An agent, runner, adapter, workflow, or human-machine process claiming support for this specification.

### Task brief

The authorized request, constraints, inputs, and intended outcome for one artifact or related artifact set.

### Artifact

A deliverable produced by the pipeline. Artifact classes include publication text, visual assets or briefs, source notes, and review reports.

### Publication artifact

The copy and public metadata intended for the target audience. Internal evidence and review records are excluded unless the target format requires them.

### Source record

The identity, date, locator, type, scope, and material limitations of one source.

### Evidence map

A classification of task material as verified fact, attributed source claim, opinion, inference, assumption, or unknown.

### Claim ledger

A mapping between material artifact claims, their classification, supporting source records, qualifications, and current review state.

### Context gate

The pre-draft decision that required framing and evidence are sufficient for the intended promise and risk.

### Visual gate

The pre-production decision that a visual has a purpose, evidence boundary, rights basis, accessibility plan, and acceptance criteria.

### Reviewer

An independent evaluation role with a declared scope and structured findings. Independence means the reviewer evaluates against the supplied contract rather than merely defending the draft.

### Publisher

The authorized person or system responsible for accepting the final publication risk. A publisher decision does not convert an unsupported claim into a verified fact.

## Content model

An implementation MUST keep these axes logically distinct:

| Axis | Responsibility |
|---|---|
| Language | Native language and locale behavior |
| Format | Artifact shape and reading experience |
| Topic | Domain evidence and risk requirements |
| Platform | Publishing constraints |
| Skill | Job to be done |
| Tone | Delivery guidance |
| Author perspective | Legitimate speaking position |
| Visual mode | Whether and how visual work enters the pipeline |

A module MAY constrain several axes through declared applicability metadata, but it MUST NOT silently redefine another axis. For example, a platform MAY constrain length and media placement; it MUST NOT weaken a scientific evidence requirement.

## Fundamental invariants

These requirements have precedence over stylistic and engagement goals.

### Factual integrity

- An implementation MUST NOT invent or silently strengthen material claims.
- An inference MUST NOT be presented as a verified fact.
- Missing evidence MUST NOT be converted into evidence of absence.
- Conflicting or insufficient sources MUST remain visible when they affect interpretation.

### Legitimate perspective

- First-person experience MUST originate from authorized author material.
- Expert authority MUST NOT be inferred from tone alone.
- An implementation MUST NOT imitate a named living author or an identifiable private person.

### Audience integrity

- Audience needs and intended outcome MUST be known or safely inferred before format conventions are optimized.
- Engagement tactics MUST NOT override meaning, evidence, safety, or consent.

### Visual integrity

- A generated image MUST NOT be presented as a photograph, screenshot, record, or other documentary evidence of a real event, person, place, product, or interface.
- A visual MUST NOT introduce unsupported data, labels, scale, causation, anatomy, features, or historical detail.
- Rights, likeness, privacy, accessibility, provenance, and mandatory disclosure MUST be handled as part of the artifact contract.

### Review integrity

- A review MUST identify concrete affected content or assets.
- A revision MUST address findings rather than create unrelated stylistic churn.
- An artifact with an open blocker or major finding MUST NOT be labeled publication-ready.

## Normative precedence

When requirements conflict, an implementation MUST apply this order:

1. applicable law, contract, consent, rights, safety, privacy, and mandatory disclosure;
2. the fundamental invariants in this RFC and gates in RFC-0002;
3. explicit task facts and constraints supplied by an authorized user;
4. RFC-0002 through RFC-0006;
5. registered core and cross-cutting rule objects;
6. selected language, format, topic, platform, skill, tone, and reviewer objects;
7. implementation defaults;
8. examples and benchmark outputs.

An explicit user preference MAY override a stylistic default or recommendation. It MUST NOT override source integrity, legitimate perspective, rights, disclosure, or a failed gate.

Within the same level, a narrower applicable requirement SHOULD override a broader one only within its declared scope. If two equal-level requirements remain incompatible, the implementation MUST record a conflict and stop the affected stage rather than choose silently.

## Conformance profiles

### Editorial Core

Supports text production with `visuals.mode: none`. It MUST implement RFC-0001 through RFC-0005, required registries, context resolution, evidence classification, gates, review, and separated output.

### Editorial Visual

Includes Editorial Core and visual planning or generation. It MUST implement visual requirements in RFC-0002 and RFC-0005, including provenance and accessibility handoff.

### Benchmark

Implements RFC-0006 in addition to Editorial Core. A benchmark evaluating generated visuals MUST also conform to Editorial Visual.

## Conformance statement

A conformance statement MUST include:

- specification revision or pinned repository commit;
- supported profile or profiles;
- supported object kinds and registry indexes;
- unsupported optional capabilities;
- documented deviations from `SHOULD` requirements;
- validation and benchmark evidence used for the claim.

An implementation MUST NOT advertise conformance as proof that every individual output is accurate, safe, lawful, accessible, or high quality.

## Extension boundaries

An extension MAY add a language, format, topic, platform, skill, tone, reviewer, or cross-cutting rule when:

- its scope is materially distinct;
- non-applicable cases are documented;
- it does not weaken fundamental invariants;
- it has a stable non-colliding ID;
- dependencies and applicability are explicit;
- evaluation evidence or a concrete evaluation plan exists.

An extension MUST NOT redefine an existing stable ID for a different meaning.

## Privacy, security, and rights

Implementations SHOULD minimize collection and retention of personal or confidential source material. They MUST respect authorization boundaries and MUST NOT place private source content into public artifacts, prompts, benchmarks, or visual assets without permission.

Security-sensitive instructions, personal data, embargoed material, copyrighted content, trademarks, and likenesses MUST retain their applicable restrictions throughout retrieval, drafting, generation, review, storage, and publication.

## Compatibility

Two implementations are behaviorally compatible for a task when they preserve:

- explicit task choices and material inferences;
- the resolved module root set and dependency semantics;
- the evidence boundary and claim classifications;
- gate outcomes;
- reviewer severities and readiness semantics;
- output package separation;
- required visual disclosure and provenance.

Their prose, layout, and art direction MAY differ.
