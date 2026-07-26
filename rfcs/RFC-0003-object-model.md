---
id: RFC-0003
status: active
revision: 1.0.0
created: 2026-07-25
updated: 2026-07-26
normative: true
depends_on: RFC-0001
---

# Object Model

## Abstract

Human Writing Rules represents reusable editorial behavior as stable objects with explicit metadata and dependencies. This RFC defines object identity, kinds, metadata, applicability, dependency rules, lifecycle, registries, compatibility, and validation.

## Scope

This RFC governs machine-resolvable objects used by an implementation. RFC documents, examples, roadmap entries, and benchmark outputs are governed by their own indexes and are not runtime modules unless an index explicitly declares otherwise.

## Object identity

Every runtime object MUST have one stable `id`.

An ID:

- MUST match `^[a-z0-9][a-z0-9._-]+$`;
- MUST be unique within a specification revision;
- SHOULD follow `<kind-or-domain>.<name>[.<variant>]`;
- MUST NOT be reused for a semantically different object;
- MUST remain unchanged when only the title, prose, or repository path changes.

Examples:

- `core.writing-pipeline`;
- `format.article.foundation`;
- `topic.science.foundation`;
- `platform.telegram.foundation`;
- `reviewer.visual`.

## Object kinds

| Kind | Responsibility | Typical selection |
|---|---|---|
| `core` | Pipeline, content model, resolution policy | Required |
| `principle` | Durable priority or invariant explanation | Dependency |
| `rule` | Cross-cutting integrity, safety, accessibility, or style | Required or conditional |
| `language` | Native language and locale behavior | Exactly one primary language |
| `format` | Artifact shape and reading experience | One primary format |
| `topic` | Domain evidence and risk requirements | One primary topic, optional additional topics |
| `platform` | Publishing constraints | Zero or one primary platform chain |
| `tone` | Delivery guidance | Zero or one primary tone |
| `skill` | Repeatable job-specific workflow | Zero or more compatible skills |
| `reviewer` | Independent evaluation contract | Required and conditional reviewers |
| `benchmark` | Indexed benchmark metadata | Evaluation only |
| `example` | Indexed example metadata | Informative unless incorporated |
| `rfc` | Indexed specification metadata | Normative according to RFC status |

An object MUST use the narrowest kind matching its responsibility. A platform object MUST NOT encode a universal evidence rule. A tone object MUST NOT create author authority. A topic object SHOULD NOT prescribe a fixed article structure unless the structure is necessary to preserve domain meaning.

## Runtime object record

A runtime object record MUST contain:

| Field | Type | Requirement |
|---|---|---|
| `id` | string | Required, stable, unique |
| `kind` | enum | Required |
| `title` | non-empty string | Required, human-readable |
| `status` | enum | Required |
| `path` | repository-relative string | Required, safe, existing |
| `tags` | array of strings | Optional |
| `languages` | array of IDs | Optional applicability |
| `platforms` | array of IDs | Optional applicability |
| `formats` | array of IDs | Optional applicability |
| `topics` | array of IDs | Optional applicability |
| `requires` | array of object IDs | Optional dependencies |

Missing optional arrays MUST be interpreted as empty arrays. An empty applicability array means “not restricted by this selector,” not “applicable nowhere.”

Example:

```json
{
  "id": "topic.science.foundation",
  "kind": "topic",
  "title": "Science Topic",
  "status": "draft",
  "path": "rules/topic/science/foundation.md",
  "tags": ["topic", "research"],
  "languages": [],
  "platforms": [],
  "formats": [],
  "topics": ["science"],
  "requires": ["topic.general.foundation"]
}
```

## Path rules

An object path:

- MUST be relative to the repository root;
- MUST NOT be absolute;
- MUST NOT contain `..` path traversal;
- MUST resolve to one file;
- MUST be unique among runtime objects;
- SHOULD remain stable when practical, but path stability is weaker than ID stability.

Moving a file without changing its semantics MUST preserve the object ID and MUST update the registry atomically.

## Frontmatter contract

Each runtime Markdown module MUST begin with frontmatter containing at least:

```yaml
---
id: topic.science.foundation
kind: topic
status: draft
---
```

The frontmatter `id`, `kind`, and `status` MUST equal the registry values. Human-readable prose outside frontmatter MUST NOT redefine those values.

Additional frontmatter MAY be used when a validator understands or safely ignores it. Required machine metadata MUST live in the registry rather than only in prose.

## Applicability

Applicability selectors narrow when an object may be selected.

- A value present in `languages`, `platforms`, `formats`, or `topics` declares compatibility with that value.
- An empty selector declares no restriction on that axis.
- A resolver MUST reject an explicitly selected object when a non-empty selector excludes the task value.
- Dependency objects MAY be broader than the dependant object.

Applicability does not select an object by itself. Selection is defined by RFC-0004.

## Dependencies

`requires` expresses semantic prerequisites.

A dependency graph:

- MUST reference known object IDs;
- MUST NOT contain self-dependencies;
- MUST NOT contain cycles;
- MUST load dependencies before dependants;
- MUST preserve transitive dependencies;
- SHOULD avoid dependencies that exist only for prose convenience.

An object MUST NOT depend on a narrower object unless that narrower scope is required for every valid use of the dependant.

For example, `platform.telegram.foundation` MAY require `platform.social.foundation`. `topic.general.foundation` MUST NOT require every specialist topic.

## Registry indexes

`registry/objects.json` is the canonical runtime object catalog.

Value indexes such as languages, formats, topics, platforms, skills, and tones:

- MUST map a public configuration value to one known object of the matching kind;
- MUST use unique value IDs and module IDs within the index;
- MUST NOT map two values to the same module unless the alias behavior is explicitly documented;
- SHOULD declare a fallback only when fallback semantics are defined by RFC-0004;
- MUST remain consistent with the object's applicability selector.

Reviewer configuration MAY use full object IDs directly.

RFCs SHOULD be listed in a separate RFC index because normative-document dependency is not runtime module dependency.

## Status lifecycle

Runtime objects use:

- `draft`: available for a draft profile and subject to incompatible change;
- `active`: stable for the declared specification release;
- `deprecated`: retained for compatibility but not selected by default.

An implementation MAY load a `draft` object only when its claimed profile permits draft objects.

A deprecated object:

- MUST retain its ID;
- SHOULD identify its replacement in prose or migration metadata;
- MUST NOT be selected by default for new configurations;
- MAY remain resolvable for pinned historical configurations.

Deleting an active or deprecated object is a breaking change unless the supported version window has ended.

## Change classification

| Change | Compatibility |
|---|---|
| Typo or clarification without semantic effect | Patch-compatible |
| New optional object or index value | Backward-compatible |
| New optional metadata field | Backward-compatible |
| Stronger `SHOULD` guidance within existing invariant | Usually backward-compatible; document |
| New `MUST`, new dependency, or narrower applicability | Potentially breaking |
| ID reuse or changed object kind | Prohibited |
| Removed active ID or changed public value mapping | Breaking |
| Changed meaning of an existing object | Breaking; create a new ID when material |

Every potentially breaking change MUST include migration notes before release.

## Extension and namespace rules

Community or vendor extensions SHOULD use a documented namespace when collision is possible. An extension MUST NOT use a core ID for different behavior.

An extension proposal MUST document:

- problem and evidence;
- object kind and ID;
- scope and non-applicable cases;
- dependencies and selectors;
- conflict behavior;
- evaluation method;
- privacy, rights, safety, and visual implications when relevant.

## Validation

A conforming object validator MUST detect:

- invalid or duplicate IDs;
- missing required fields;
- unknown kinds or statuses;
- unsafe, missing, or duplicate paths;
- frontmatter mismatch;
- unknown dependencies;
- self-dependencies and cycles;
- unregistered runtime modules;
- invalid index mappings;
- unknown configured values.

Validation failure MUST produce a non-success result and identify the affected file or object.

## Security considerations

Object paths and index values are untrusted input to tooling. Resolvers MUST prevent path traversal and MUST NOT execute module content as code merely because it is registered.

An object MAY contain sensitive guidance but MUST NOT embed private source material, credentials, tokens, or proprietary content without authorization.

## Conformance

An implementation conforms to this RFC when it:

- consumes records with the defined semantics;
- preserves stable IDs;
- validates dependency and index integrity;
- applies status and compatibility rules;
- rejects unsafe or inconsistent object metadata;
- emits the object revision or pinned repository identity in its audit record.
