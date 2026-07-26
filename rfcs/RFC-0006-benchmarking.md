---
id: RFC-0006
status: active
revision: 1.0.0
created: 2026-07-25
updated: 2026-07-26
normative: true
depends_on: RFC-0001,RFC-0002,RFC-0003,RFC-0004,RFC-0005
---

# Reproducible Benchmarking

## Abstract

This RFC defines how to evaluate Human Writing Rules without converting a small or opaque comparison into a universal quality claim. It specifies benchmark cases, controlled arms, source snapshots, execution records, review and human evaluation, visual evaluation, aggregation, reporting, and prohibited interpretations.

## Scope

This RFC applies to claims comparing:

- a baseline prompt or workflow with a rules-assisted workflow;
- two specification revisions;
- two module selections;
- two implementations claiming the same profile.

It does not require one universal score.

## Terminology

### Case

A pinned task brief, source set, configuration, expected constraints, evaluation dimensions, and acceptance conditions.

### Arm

One treatment within a case, such as baseline or rules-assisted.

### Run

One model execution for one case and arm with recorded settings.

### Output unit

The publication artifact, visual artifacts or decisions, source notes, review report, and execution record produced by one run.

### Evaluator

A structured reviewer, human rater, or validated automated check that scores or classifies an output.

## Benchmark case record

Every case MUST include:

- stable case ID and revision;
- intended conformance profile;
- language, content type, topic, platform, skill, risk, and visual mode;
- audience, intent, author perspective, and constraints;
- complete task prompt or task-record construction method;
- source snapshot or stable source references;
- source publication and retrieval dates when material;
- required module roots and reviewers;
- evaluation dimensions and instructions;
- hard failure conditions;
- expected output package parts;
- known limitations of the case.

A case MUST NOT contain invented sources or hidden facts used to penalize an output.

## Source snapshot

Mutable sources MUST be pinned, archived when permitted, or accompanied by enough identity and retrieval metadata to reproduce the evidence boundary.

The snapshot MUST preserve:

- content used by the run;
- source identity and date;
- version, jurisdiction, population, or dataset when relevant;
- access limitations and rights;
- redactions or unavailable material.

Private or licensed sources MUST NOT be published in a benchmark package without authorization. The benchmark MAY publish hashes, metadata, or an access procedure instead.

## Controlled comparison

When a benchmark claims an effect from Human Writing Rules, arms MUST keep these values equal unless the benchmark explicitly studies them:

- model and provider;
- model revision or dated identifier when available;
- generation settings;
- tool permissions and retrieval capability;
- task brief;
- source set;
- execution environment;
- time budget and retry policy;
- output requirements.

The intended treatment difference MUST be stated precisely.

A baseline MUST be credible for the tested workflow. It MUST NOT be intentionally crippled to exaggerate improvement.

## Rules-assisted arm

The rules-assisted arm MUST record:

- specification revision or pinned commit;
- configuration;
- normalized inputs;
- resolution record;
- loaded object IDs and revisions;
- gate outcomes;
- reviewer findings and revisions;
- deviations and errors.

If the implementation fails to resolve or load the intended modules, the run is an execution failure, not a low-quality completed output.

## Repeated runs

Generative outputs vary. A comparative claim SHOULD use repeated runs across more than one case and, when possible, more than one model or execution date.

The benchmark MUST report the number of:

- attempted runs;
- completed runs;
- blocked runs;
- tool or retrieval failures;
- invalid runs;
- excluded runs and reasons.

Runs MUST NOT be discarded merely because they weaken the desired result.

## Visual-mode handling

For `visuals.mode: auto`, producing no visual MAY be the correct decision.

Evaluation MUST score:

1. whether the media decision was justified;
2. the asset only when an asset was selected and produced.

An evaluator MUST NOT penalize a correct `none` decision for lacking visual polish. A required visual that cannot be produced or reviewed is a blocked or failed run, not an implicit zero-quality image unless the rubric defines that failure.

## Required execution record

Each run MUST preserve:

- case and arm ID;
- model, provider, settings, and run date;
- tool and retrieval configuration;
- prompt and message sequence sufficient for reproduction;
- source access result;
- output package;
- latency or cost only when claimed;
- errors, retries, and manual intervention;
- reviewer and human-evaluation inputs;
- specification and registry revisions.

Secrets and private chain-of-thought MUST NOT be required for benchmark reproduction. An implementation SHOULD preserve observable decisions and artifacts instead.

## Evaluation dimensions

### Text

| Dimension | Evaluates |
|---|---|
| Factuality | Claim support, attribution, qualification, and absence of fabrication |
| Native language | Idiomatic, locale-appropriate language without translated structure |
| Purpose fit | Delivery of the intended reader outcome |
| Format fit | Correct artifact shape and structure |
| Topic fit | Domain evidence, terminology, and risk handling |
| Platform fit | Publishing constraints without audience harm |
| Human signals | Coherent perspective and meaningful variation without simulated humanity |
| Limitation handling | Visibility and placement of uncertainty and boundaries |
| Revision efficiency | Correction of findings without unrelated churn |

### Visual

| Dimension | Evaluates |
|---|---|
| Media decision | Whether a visual has a justified purpose |
| Factual consistency | Alignment with evidence and absence of unsupported implications |
| Text-image alignment | Agreement with the final publication artifact |
| Documentary integrity | No generated false record or misleading simulation |
| Platform handoff | Crop, dimensions, legibility, and placement |
| Accessibility | Alt text, caption, contrast-sensitive choices, and alternatives |
| Rights and provenance | Credits, permission, likeness, trademark, and disclosure |

### Hard failures

Rubrics SHOULD separately record invariant violations such as:

- fabricated source, quotation, statistic, event, or personal experience;
- material inference presented as verified fact;
- failed context gate hidden by a fluent draft;
- generated visual presented as documentary evidence;
- required disclosure removed;
- unresolved blocker labeled publication-ready.

A high average score MUST NOT erase a hard failure.

## Evaluator protocol

Evaluation instructions MUST define:

- dimension definitions;
- scale anchors;
- whether source records are visible;
- how to handle missing or blocked artifacts;
- conflict and uncertainty handling;
- evaluator qualification for specialist topics;
- adjudication process.

Human comparison SHOULD be blinded to arm identity when practical. Evaluators MUST NOT be told the desired winner.

An automated reviewer MAY supplement human evaluation. It MUST NOT be described as independent human evidence.

## Inter-rater handling

When several human raters are used, the report SHOULD include:

- individual ratings;
- agreement or disagreement;
- adjudicated result when applicable;
- rater background relevant to the topic;
- exclusions and conflicts of interest.

Do not report only the post-adjudication average when disagreement is material.

## Aggregation

Aggregation MUST retain case and dimension detail.

Reports SHOULD include:

- counts and distributions, not only a mean;
- hard-failure rate;
- blocked and invalid run rate;
- per-topic, format, platform, and model breakdown when sample size permits;
- uncertainty or variability;
- examples of wins, losses, and neutral results.

Small samples MUST be labeled exploratory. Statistical inference MUST state its assumptions and method.

## Reporting

A public benchmark report MUST include:

- research question;
- case selection method;
- all tested arms;
- pinned configuration and revisions;
- run counts and exclusions;
- source accessibility;
- evaluator instructions;
- raw or sufficiently detailed ratings;
- aggregation method;
- limitations;
- artifacts needed for reproduction, subject to rights and privacy.

Selective publication of only favorable cases is incompatible with a comparative conformance claim unless the selection is disclosed and the claim is narrowed.

## Permitted conclusions

Conclusions MUST remain within the tested:

- cases;
- languages;
- formats;
- topics;
- platforms;
- models;
- tools;
- dates;
- implementation and specification revisions.

Permitted wording resembles:

> In these pinned cases and runs, the rules-assisted arm had fewer unsupported material claims according to the stated source-review protocol.

Prohibited wording includes:

> Human Writing Rules always makes AI writing factual and human.

## Benchmark lifecycle

Changing the task, sources, rubric, hard failures, arm construction, or required modules creates a new case revision.

Historical results MUST remain associated with the exact case and specification revision used. Re-running a changed case MUST NOT silently replace previous results.

## Security, privacy, and rights

Benchmark packages MUST remove credentials and unauthorized personal or confidential material. Visual assets, source snapshots, prompts, and outputs MUST retain copyright, trademark, likeness, and license restrictions.

Adversarial or high-risk cases SHOULD be isolated from live publishing and production systems.

## Conformance

A benchmark conforms to this RFC when it:

- pins cases, sources, arms, settings, and revisions;
- preserves failed, blocked, and excluded runs;
- evaluates text and optional visuals with declared protocols;
- separates hard failures from average quality;
- exposes material disagreement and limitations;
- makes only scope-bounded conclusions;
- provides enough authorized artifacts for independent reproduction.
