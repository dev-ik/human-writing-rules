---
id: RFC-0005
status: active
revision: 1.0.0
created: 2026-07-25
updated: 2026-07-26
normative: true
depends_on: RFC-0001,RFC-0003
---

# Review Contract

## Abstract

This RFC defines reviewer roles, required inputs, structured findings, severity, disposition, aggregation, revision, re-review, readiness, and audit requirements.

Review is an evidence-producing stage. It is not a request to rewrite the artifact until it merely looks different.

## Goals

A conforming review process MUST:

- evaluate the artifact against the task, evidence, and resolved modules;
- identify concrete affected text, metadata, or visual assets;
- distinguish publication blockers from optional improvements;
- propose the smallest useful correction;
- preserve findings across revision and re-review;
- determine publication readiness without hiding unresolved risk.

## Reviewer roles

Editorial Core requires:

- `reviewer.source`;
- `reviewer.language`;
- `reviewer.human-signals`;
- `reviewer.editor`.

Add:

- `reviewer.format` when a format is selected;
- `reviewer.topic` when a topic module is selected;
- `reviewer.platform` when a platform is selected;
- `reviewer.visual` when visual mode is `auto` or `required`;
- task or extension reviewers when selected modules require them.

One implementation MAY execute several roles, but it MUST preserve each role's scope and findings separately. A combined reviewer MUST NOT omit a required checklist merely because another role appears to cover it.

## Independence

A reviewer SHOULD evaluate an artifact from the supplied task and evidence record rather than from the draft author's hidden rationale.

The reviewer MUST NOT:

- invent a missing source to rescue a claim;
- infer author experience or authority absent from the task;
- lower severity to protect the draft;
- demand a preferred style outside the selected modules;
- rewrite unaffected passages as proof that review occurred.

For high-risk tasks, implementations SHOULD use a distinct review pass or independent evaluator when practical.

## Review input

Every review run MUST identify:

| Input | Requirement |
|---|---|
| Artifact revision | Required |
| Task framing and reader promise | Required |
| Resolved object IDs and revisions | Required |
| Source records | Required when claims use sources |
| Evidence map and claim ledger | Required |
| Author perspective and provenance | Required |
| Constraints, risk, and disclosures | Required |
| Visual brief, prompt, asset, and provenance | Required for produced visuals |
| Previous findings | Required for re-review |

A reviewer MUST return an input error rather than guess when a missing item prevents evaluation within its scope.

## Finding schema

Each finding MUST contain:

| Field | Meaning |
|---|---|
| `id` | Stable within the review run |
| `reviewer` | Reviewer object ID |
| `severity` | `blocker`, `major`, `minor`, or `note` |
| `location` | Text range, section, metadata field, claim ID, asset, or global |
| `summary` | Concise problem statement |
| `reason` | Why the issue matters |
| `rule` | Applicable RFC or object ID when available |
| `claim_ids` | Affected claim-ledger IDs when applicable |
| `correction` | Smallest useful corrective action |
| `status` | Finding disposition |

Example:

```json
{
  "id": "source-003",
  "reviewer": "reviewer.source",
  "severity": "major",
  "location": "section-2.paragraph-1",
  "summary": "Association is described as causation",
  "reason": "The cited study does not establish the causal claim",
  "rule": "topic.science.foundation",
  "claim_ids": ["claim-014"],
  "correction": "Replace the causal wording with the measured association and add the study limitation",
  "status": "open"
}
```

Exact serialization MAY differ, but the fields and semantics MUST remain recoverable.

## Severity

### Blocker

Use `blocker` when publication would be materially false, harmful, unauthorized, privacy-violating, rights-infringing, inaccessible for a required use, or incompatible with a non-negotiable task requirement.

Examples include:

- fabricated quotation or evidence;
- high-risk instruction unsupported by adequate sources;
- generated image presented as documentary evidence;
- unauthorized private material;
- required disclosure removed;
- wrong subject, language, or artifact type.

### Major

Use `major` when the thesis, evidence boundary, author legitimacy, reader outcome, structure, topic fit, platform fit, or visual meaning is materially weakened but a bounded correction is available.

### Minor

Use `minor` for a localized issue that does not materially overturn interpretation or readiness, such as inconsistent terminology, an unclear transition, or incomplete optional metadata.

### Note

Use `note` for an observation, alternative, or future improvement that is not required for readiness.

Severity MUST reflect impact, not correction effort. An easy-to-fix false claim may still be a blocker.

## Finding status

Allowed dispositions are:

- `open`: not yet resolved;
- `fixed`: correction applied and awaiting or passing verification;
- `withdrawn`: reviewer determined the original finding was invalid, with reason;
- `deferred`: intentionally postponed and incompatible with publication-ready status when severity is blocker or major;
- `accepted-risk`: publisher explicitly accepts the documented risk.

`accepted-risk` MUST NOT change a claim classification or make an unsupported claim verified. An artifact with an accepted-risk blocker or major finding MUST NOT claim unqualified publication-ready status under this specification.

## Review execution

1. Freeze or identify the artifact revision.
2. Validate required review inputs.
3. Run each required reviewer against its declared scope.
4. Emit structured findings without editing the artifact.
5. Deduplicate findings that identify the same underlying issue while preserving all affected reviewer scopes.
6. Apply bounded revisions.
7. Re-run affected reviewers and any downstream reviewer whose conclusion may have changed.
8. Determine readiness.

Review MAY be parallelized when reviewers use the same frozen artifact revision. Findings from different revisions MUST NOT be merged without identifying the revision boundary.

## Aggregation

Duplicate findings SHOULD be linked to one issue rather than counted as independent evidence of severity.

When reviewers disagree:

- preserve both findings;
- compare scope and RFC-0001 precedence;
- request specialist or publisher adjudication when necessary;
- record the resolution and reason.

Aggregation MUST NOT average severities into a lower category.

## Revision contract

A revision MUST:

- identify the finding IDs it addresses;
- change the affected passage, dependency, metadata, source record, or visual;
- preserve unaffected valid content;
- update the claim ledger and evidence map when meaning changes;
- update title, lead, caption, alt text, or metadata when the corrected meaning affects them;
- create a new identifiable artifact revision.

A revision SHOULD NOT rewrite the entire artifact when a local correction is sufficient.

## Re-review

Every fixed blocker or major finding MUST be verified.

Re-review MUST inspect:

- the correction;
- adjacent text or asset context;
- dependent claims;
- title and lead when the thesis changed;
- visual and caption when the source boundary changed;
- newly introduced regressions.

A finding MAY be closed only when the correction is present in the reviewed revision.

## Visual review

When a visual is produced, review MUST compare:

- final asset against approved brief;
- asset against publication text and evidence map;
- prompt and provenance against rights and disclosure requirements;
- image text, labels, data, anatomy, UI, maps, or diagrams against verified material;
- crop, dimensions, legibility, contrast-sensitive choices, caption, and alt text against the platform handoff.

The visual reviewer MUST recommend omission when an optional asset cannot be made truthful, useful, accessible, or authorized.

## Readiness

An artifact is `publication-ready` only when:

- all required reviewers completed;
- no blocker or major finding remains open, deferred, or accepted-risk;
- required disclosures and source notes are complete;
- output package parts agree on the final meaning;
- required visual assets pass review or the task is explicitly blocked.

An artifact MAY be `ready-with-minor-findings` when only minor findings or notes remain and the publisher accepts them. The review report MUST preserve them.

If a required visual cannot pass review, the overall task is blocked. If the visual is optional, omit it and re-evaluate the text package.

## Review report

The report MUST include:

- artifact revision;
- reviewer IDs and revisions;
- run time or sequence;
- input validation failures;
- all findings and dispositions;
- revision mapping;
- unresolved limitations;
- final readiness state.

Review notes MUST remain separate from public copy unless disclosure or platform context requires publication.

## Privacy and security

Reviewers MUST receive only the source material required for their scope. Review reports MUST NOT expose private source content, credentials, hidden personal data, or confidential prompts without authorization.

## Conformance

A process conforms to this RFC when it:

- runs every required and selected reviewer;
- emits structured, traceable findings;
- applies severity and disposition consistently;
- verifies fixed blockers and majors;
- refuses unqualified publication-ready status with unresolved material findings;
- preserves an auditable mapping from finding to revision.
