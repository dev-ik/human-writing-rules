---
id: RFC-0002
status: active
revision: 1.0.0
created: 2026-07-25
updated: 2026-07-26
normative: true
depends_on: RFC-0001,RFC-0003,RFC-0004,RFC-0005
---

# Normative Writing Pipeline

## Abstract

This RFC defines the stateful workflow that turns a task brief and source set into a reviewed output package. It specifies inputs, stages, gates, transitions, artifacts, failure behavior, resumption, and completion.

The pipeline is normative. A user interface MAY combine or hide stages, but a conforming implementation MUST preserve their decisions and outputs.

## Pipeline states

| State | Meaning |
|---|---|
| `received` | Task exists but has not been framed |
| `framed` | Required task dimensions are recorded |
| `resolved` | Runtime module set is valid and pinned |
| `collected` | Relevant context and source records exist |
| `mapped` | Evidence map and claim ledger exist |
| `context-blocked` | Context gate failed |
| `context-ready` | Context gate passed |
| `designed` | Reader promise and content design exist |
| `media-decided` | Visual mode produced a recorded decision |
| `drafted` | First meaning-complete text exists |
| `edited` | Editorial passes completed |
| `visual-blocked` | Required visual gate or production failed |
| `reviewed` | Required review pass completed |
| `revising` | Findings are being corrected |
| `ready` | Completion conditions passed |
| `blocked` | Task cannot progress without new authority, evidence, or capability |

An implementation MAY use additional internal states. It MUST map them to these semantics in its audit record.

## Required task record

Before drafting, the task record MUST contain or explicitly mark unknown:

- task identifier;
- intended artifact or artifact set;
- content type;
- topic;
- language and locale;
- audience;
- intent and desired reader outcome;
- platform;
- author perspective and provenance;
- skill when applicable;
- tone when applicable;
- constraints and required disclosures;
- source requirements and freshness cutoff;
- risk level;
- visual mode;
- output requirements.

Unknown values MUST remain distinguishable from omitted optional values.

## Stage 1 — Framing

### Entry

State is `received`.

### Required behavior

The implementation MUST:

1. extract explicit task values;
2. distinguish facts, constraints, preferences, and defaults;
3. identify missing values that may change thesis, risk, format, or legitimate voice;
4. record authorized assumptions separately from user-supplied facts;
5. identify external obligations such as disclosure, consent, privacy, rights, or embargo.

### Exit

State becomes `framed` when the task record is internally consistent enough for module resolution. Framing completion does not imply the context gate will pass.

## Stage 2 — Module resolution

The implementation MUST execute RFC-0004 against pinned registries.

### Exit

- Success: retain the resolution record and enter `resolved`.
- Failure: enter `blocked` with the RFC-0004 error code.

A partial or unvalidated module set MUST NOT be used for drafting.

## Stage 3 — Context collection

The implementation MUST collect only material relevant to the reader promise, evidence needs, constraints, and selected modules.

Each material source SHOULD have a source record containing:

- stable source ID;
- identity, author, publisher, or responsible organization;
- publication and update date when available;
- retrieval date for mutable sources;
- stable locator or pinned snapshot;
- source type;
- relevant version, jurisdiction, population, timeframe, or dataset;
- conflicts, sponsorship, access limitations, and rights when material.

The implementation MUST distinguish user-provided material from retrieved material. It MUST NOT treat a search result snippet, model memory, or unsourced prior output as a verified source.

### Exit

State becomes `collected` when available relevant material and known source gaps are recorded.

## Stage 4 — Evidence mapping

Every material item or planned claim MUST be classified as one of:

- `verified-fact`;
- `source-claim`;
- `opinion`;
- `inference`;
- `assumption`;
- `unknown`.

A claim ledger SHOULD contain:

```json
{
  "id": "claim-014",
  "text": "bounded internal claim representation",
  "classification": "source-claim",
  "source_ids": ["source-003"],
  "scope": {
    "date": "source-bounded",
    "population": "source-bounded",
    "version": "not-applicable"
  },
  "qualification": "required wording or limitation",
  "status": "supported"
}
```

Material claims MUST map to a source, explicit author material, or a declared non-factual classification. An unsupported claim MUST be removed, narrowed, researched further, or marked unknown.

### Exit

State becomes `mapped` when the evidence map and claim ledger can support a context-gate decision.

## Stage 5 — Context gate

The context gate MUST evaluate:

- subject and central reader question;
- content type, language, audience, intent, and author perspective;
- topic and risk modules;
- sufficiency and freshness of evidence for the intended promise;
- unsupported critical claims;
- source conflicts and unknowns;
- platform, legal, rights, privacy, consent, and disclosure constraints;
- real first-person or expert basis when selected;
- capability to meet required output conditions.

The gate MUST fail when a missing or unsupported item could materially change the thesis, factual risk, artifact type, or legitimate speaking position.

The gate MUST NOT pass because the implementation can produce fluent text.

### Decision record

```json
{
  "gate": "context",
  "status": "pass",
  "checked_at": "implementation-defined",
  "reader_promise_scope": "bounded summary",
  "unsupported_claims_removed": [],
  "qualified_claims": [],
  "open_unknowns": [],
  "assumptions": [],
  "warnings": []
}
```

### Exit

- Pass: enter `context-ready`.
- Fail with recoverable missing input: enter `context-blocked`.
- Fail because the task cannot be completed within constraints: enter `blocked`.

No draft transition is allowed from `context-blocked`.

## Stage 6 — Content design

The implementation MUST define a reader promise describing what the audience should understand, know, feel, or be able to do.

Content design MUST include:

- central question or thesis;
- minimum sufficient structure;
- section or unit purpose;
- claim and evidence placement;
- necessary definitions, examples, limitations, and transitions;
- public metadata required by the format or platform;
- candidate visual role, if any.

The design MUST follow the selected format and topic without forcing optional template elements.

### Exit

State becomes `designed`.

## Stage 7 — Media decision

Visual mode has these semantics:

- `none`: no visual artifact is requested or produced;
- `auto`: a visual is produced only if it provides documented explanatory, editorial, cover, or verified data value;
- `required`: at least one visual is required unless the task becomes blocked by integrity, rights, safety, accessibility, or capability constraints.

The media decision MUST state:

- selected or rejected;
- purpose;
- reader benefit;
- placement;
- relationship to the text;
- reason.

`Auto` MAY correctly result in no visual.

### Exit

State becomes `media-decided`.

## Stage 8 — Draft

Drafting MUST begin only when a valid `context-ready` gate record, current content design, and current media decision exist. The active state at that point is `media-decided`.

The draft MUST:

- write for meaning before engagement optimization;
- keep fact, source claim, inference, and opinion distinguishable;
- place material attribution and uncertainty near the affected claim;
- preserve source scope, dates, versions, units, population, and jurisdiction;
- use only legitimate author experience and authority;
- follow the selected language natively;
- avoid unsupported additions in title, lead, caption, metadata, or CTA.

The body SHOULD be meaning-complete before the implementation optimizes title, lead, deck, excerpt, tags, or visual copy.

### Exit

State becomes `drafted`.

## Stage 9 — Edit

The implementation MUST perform passes appropriate to:

1. truth and attribution;
2. argument and section order;
3. audience comprehension;
4. native language and terminology;
5. compression and repetition;
6. format and platform;
7. visual alignment when selected.

Edits MUST NOT remove necessary uncertainty, disclosure, context, or source boundaries merely to improve flow.

### Exit

State becomes `edited`.

## Stage 10 — Visual gate and production

This stage is skipped when media decision is `none`.

Before generation or commissioning, every selected visual MUST have:

- purpose and placement;
- content it may depict;
- unsupported implications it must avoid;
- asset type and whether generation is appropriate;
- format, dimensions, aspect ratio, crop, and legibility constraints;
- art direction;
- labels, caption, alt text, credit, and disclosure requirements;
- source, data, rights, trademark, likeness, privacy, and cultural constraints;
- acceptance criteria.

Generated imagery MUST NOT be presented as documentary evidence.

Exact documentary appearance, verified data, product interfaces, medical anatomy, maps, technical labels, code, and historical records SHOULD use verified assets or manually reviewed construction rather than unconstrained generation.

### Production failure

- Optional visual: omit it, record the reason, and continue.
- Required visual: enter `visual-blocked` until the brief, evidence, rights, asset, or requirement changes.

The implementation MUST retain generation provenance required by task, law, contract, platform, or profile.

## Stage 11 — Review

The implementation MUST execute RFC-0005 against the edited text and selected visual assets.

Review MUST use one frozen artifact revision per pass. Required reviewers MUST complete or return an input failure.

### Exit

State becomes `reviewed` with a readiness candidate and structured findings.

## Stage 12 — Revision loop

When blocker or major findings exist, state becomes `revising`.

The implementation MUST:

- map changes to finding IDs;
- update dependent text, metadata, evidence, captions, alt text, and visuals when meaning changes;
- preserve unaffected valid material;
- create a new artifact revision;
- re-run affected reviewers.

The loop continues until completion criteria pass or the task becomes blocked.

## Stage 13 — Completion

State becomes `ready` only when:

- required stages completed;
- context and visual gates have valid outcomes;
- required reviewers completed;
- no blocker or major finding remains open, deferred, or accepted-risk;
- publication artifact and metadata agree;
- visual assets, captions, alt text, provenance, and disclosure agree when present;
- source notes preserve material uncertainty and limitations.

The pipeline MUST NOT label an artifact publication-ready solely because a draft exists.

## Output package

A ready task MUST return or retain separable parts:

```json
{
  "status": "ready",
  "publication": {
    "content_type": "article",
    "text": "publication copy",
    "metadata": {}
  },
  "visuals": [
    {
      "asset": "implementation-defined reference",
      "purpose": "explanatory",
      "caption": "public caption",
      "alt_text": "accessible description",
      "credit": "when required",
      "provenance": "protected or public according to policy"
    }
  ],
  "source_notes": {
    "sources": [],
    "claim_ledger": [],
    "unknowns": []
  },
  "review": {
    "artifact_revision": "revision identifier",
    "findings": [],
    "readiness": "publication-ready"
  },
  "audit": {
    "spec_revision": "1.0.0",
    "resolution_record": {},
    "gate_records": [],
    "deviations": []
  }
}
```

Exact serialization MAY differ. Publication copy MUST remain distinguishable from internal notes.

## Blocking and resumption

A blocked record MUST identify:

- stage;
- reason code;
- missing authority, evidence, choice, capability, or external change;
- artifacts already completed;
- conditions required to resume.

Resumption MUST validate that pinned sources, registries, task constraints, and completed artifacts remain current. A material change MUST invalidate affected downstream stages.

## Invalidation rules

At minimum:

- changed task thesis invalidates design, draft, edit, visual alignment, and review;
- changed source meaning invalidates affected claims and downstream review;
- changed format or platform invalidates content design, format/platform edit, visual crop, and review;
- changed author perspective invalidates voice-dependent drafting and human-signal review;
- changed visual brief invalidates visual production and visual review;
- changed registry revision requires re-resolution.

## Auditability

A conforming implementation MUST retain enough information to identify:

- task and artifact revisions;
- explicit inputs, inferences, and fallbacks;
- resolved modules and registry revision;
- source records and evidence classifications;
- gate outcomes;
- reviewer findings and revisions;
- skipped optional stages and reasons;
- final readiness state.

## Conformance

An implementation conforms to this RFC when it:

- enforces stage entry and exit conditions;
- blocks drafting on a failed context gate;
- treats media as an explicit decision;
- enforces the visual gate when visuals are selected;
- executes RFC-0005 review and revision;
- returns a separated output package;
- preserves resumable blocked states and invalidates stale downstream work.
