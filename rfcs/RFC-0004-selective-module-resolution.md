---
id: RFC-0004
status: active
revision: 1.0.0
created: 2026-07-25
updated: 2026-07-26
normative: true
depends_on: RFC-0001,RFC-0003
---

# Selective Module Resolution

## Abstract

This RFC defines how task choices become a deterministic, minimal, auditable set of runtime objects. It specifies input normalization, inference, fallback, root selection, dependency closure, applicability, conflict handling, ordering, errors, and the resolution record.

## Goals

Resolution MUST:

- preserve explicit authorized choices;
- load required integrity rules;
- select only relevant conditional modules;
- include transitive dependencies;
- reject unknown, incompatible, unsafe, or cyclic configurations;
- produce the same resolved object set for the same pinned inputs and registries;
- record every material inference and fallback.

Resolution MUST NOT attempt to improve prose. It prepares the instruction context for RFC-0002.

## Inputs

A resolution request contains:

| Field | Requirement | Resolution behavior |
|---|---|---|
| `language` | Required | Map through language index |
| `locale` | Optional | Validate against language behavior when material |
| `content_type` | Required for publication tasks | Map through format index |
| `topic` | Optional | Map or use documented general fallback |
| `platform` | Optional | Map through platform index |
| `skill` | Optional | Map through skill index |
| `tone` | Optional | Map through tone index |
| `author_perspective` | Required before context gate | No module required unless an extension defines one |
| `risk_level` | Required before context gate | May raise required specialist rules |
| `visuals.mode` | Required; default MAY be `auto` | Select visual rules for `auto` or `required` |
| `reviewers` | Optional explicit list | Merge with required reviewers |
| explicit object IDs | Optional | Validate kind and applicability |

Audience, intent, constraints, sources, and length do not normally select registry objects, but they MAY affect whether a choice is safe to infer.

## Input authority

The resolver MUST distinguish:

- explicit authorized user value;
- project configuration default;
- platform-derived default;
- topic fallback;
- implementation default;
- inferred value;
- unknown value.

It MUST preserve the origin of every resolved axis.

An explicit authorized value overrides a default. It does not override RFC-0001 invariants or applicability constraints.

## Normalization

Before mapping, an implementation:

1. MUST preserve the original input value in the audit record;
2. MAY normalize documented case or whitespace differences;
3. MUST NOT fuzzy-match an unknown stable ID or public value;
4. MUST NOT translate a public value into a semantically similar value without an explicit alias;
5. MUST validate the pinned registry revision before resolution.

For example, `science` MAY map to `topic.science.foundation` because the topic index declares it. `scientific` MUST NOT map automatically unless an index declares that alias.

## Required roots

Every Editorial Core resolution MUST include:

- `core.writing-pipeline`;
- `core.content-model`;
- `core.context-selection`;
- `rule.source-integrity`;
- `rule.human-signals.core`;
- the selected language module;
- `reviewer.source`;
- `reviewer.language`;
- `reviewer.human-signals`;
- `reviewer.editor`.

When `content_type` is known, include the selected format module and `reviewer.format`.

When a topic is selected or falls back to general, include its topic module and `reviewer.topic`.

When a platform is selected, include its platform module and `reviewer.platform`.

When a skill or tone is selected, include the mapped module.

When visual mode is `auto` or `required`, include `rule.visual-integrity` and `reviewer.visual`.

An implementation MAY add a specialist reviewer required by a selected extension. It MUST record the reason.

## Topic selection

The resolver SHOULD choose the narrowest topic controlling the material claims.

- A known explicit topic MUST map through the topic index.
- An unlisted, mixed, or low-risk topic MAY use the index-declared general fallback.
- A high-risk or materially specialist topic MUST NOT silently fall back to general when doing so would weaken evidence or safety requirements.
- Multiple topic modules MAY be selected when each controls material claims.

Selecting additional topics “for safety” without material applicability violates minimal resolution.

## Format and platform compatibility

A platform index MAY declare a `default_format`.

- If content type is absent and the task can safely inherit the platform default, the resolver MAY infer it and MUST record the inference.
- If an explicit content type conflicts with a non-empty platform format selector, the resolver MUST return an applicability error.
- A generic platform MAY be selected when the publishing family is known and no specific platform module exists.
- A platform default MUST NOT determine topic, skill, tone, or author perspective.

## Skill selection

A skill describes the job to be done.

- An explicit known skill MUST be loaded.
- An unknown skill MUST produce an error.
- When no skill accurately describes the task, the resolver SHOULD omit the skill.
- A resolver MUST NOT select a skill merely because its example resembles the requested subject.

Multiple skills MAY be loaded only when their jobs are materially required and compatible. The resolver MUST record the primary skill.

## Tone and perspective

Tone MAY be inferred when the audience, platform, and task establish a low-risk default. The inference MUST be recorded.

Author perspective MUST NOT be inferred as first-person or expert solely from tone, platform, or topic. If legitimate perspective is unknown and would materially affect the artifact, resolution MAY complete but RFC-0002 context gating MUST fail.

## Resolution algorithm

Given validated registries and normalized inputs:

```text
roots = required_editorial_core_roots()

roots += map(language)
roots += map(content_type) when known
roots += map(each selected topic)
roots += map(platform) when known
roots += map(each selected skill)
roots += map(tone) when known
roots += configured reviewer IDs

if content_type is known:
    roots += reviewer.format
if topic selection exists:
    roots += reviewer.topic
if platform is known:
    roots += reviewer.platform
if visuals.mode in {auto, required}:
    roots += rule.visual-integrity
    roots += reviewer.visual

validate root kinds and applicability
closure = transitive_requires(roots)
reject unknown dependencies, self-dependencies, and cycles
validate applicability of roots and constrained dependencies
order dependencies before dependants
deduplicate by stable object ID
emit resolution record
```

The root set is a set for semantic purposes. An implementation MAY preserve a stable display order for diagnostics.

## Dependency ordering

Dependencies MUST load before dependants.

When multiple valid topological orders exist, an implementation SHOULD use a deterministic order, such as:

1. declared dependency order;
2. normalized root order by axis;
3. stable object ID as final tie-breaker.

Load order MUST NOT silently become a substitute for normative precedence. Conflict handling follows RFC-0001.

## Conflict handling

For every apparent conflict:

1. apply RFC-0001 precedence;
2. determine whether the narrower module is within its declared scope;
3. preserve the stronger integrity, rights, safety, privacy, disclosure, or evidence requirement;
4. record the winning and losing requirements;
5. return an error if equal-precedence requirements remain incompatible.

Examples:

- A conversational tone MAY change phrasing but MUST NOT weaken a health disclaimer.
- A Telegram module MAY change paragraphing but MUST NOT remove a scientific limitation.
- A user MAY request no headings, but a required accessibility or platform structure MAY still apply when documented.

## Error contract

A failed resolution MUST return a machine-distinguishable code and human-readable context.

| Code | Meaning |
|---|---|
| `E_UNKNOWN_VALUE` | Public configuration value is absent from its index |
| `E_UNKNOWN_OBJECT` | Explicit or dependent object ID is unknown |
| `E_KIND_MISMATCH` | Index or explicit selection references the wrong object kind |
| `E_APPLICABILITY` | Selected object excludes the task axis |
| `E_DEPENDENCY_CYCLE` | Dependency graph contains a cycle |
| `E_UNSAFE_PATH` | Object path is absolute, escaping, missing, or invalid |
| `E_CONFLICT` | Equal-precedence requirements cannot be reconciled |
| `E_HIGH_RISK_FALLBACK` | General fallback would weaken a material high-risk requirement |
| `E_REGISTRY_INVALID` | Registry or index validation failed |

An error MUST identify the affected value or object. The resolver MUST NOT continue with a silent partial module set when a required root or dependency fails.

## Resolution record

A successful resolution MUST emit or retain:

```json
{
  "spec_revision": "1.0.0",
  "registry_revision": "pinned identifier",
  "inputs": {
    "language": "ru",
    "content_type": "article",
    "topic": "science",
    "platform": "blog",
    "visual_mode": "auto"
  },
  "origins": {
    "language": "explicit",
    "content_type": "explicit",
    "topic": "explicit",
    "platform": "explicit",
    "visual_mode": "project-default"
  },
  "root_objects": [],
  "dependency_order": [],
  "fallbacks": [],
  "inferences": [],
  "conflicts": [],
  "warnings": []
}
```

Exact serialization MAY differ, but the semantics MUST be preserved.

## Minimality

A resolution is minimal when removing any root would omit a required foundation or applicable task choice, and every non-root object is reachable through `requires`.

Implementations SHOULD expose unused explicitly requested modules as warnings or errors rather than loading them without effect.

## Conformance

An implementation conforms to this RFC when:

- the same pinned valid inputs resolve to the same object set;
- unknown and incompatible values fail explicitly;
- dependencies are complete, acyclic, and ordered;
- explicit values, defaults, inferences, and fallbacks remain distinguishable;
- the output record supports audit and RFC-0002 execution;
- no irrelevant specialist modules are loaded by default.
