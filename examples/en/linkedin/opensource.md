# Example: EN LinkedIn Open Source Announcement

## Task framing

- Content type: `social-post`
- Topic: `technology`
- Platform: `linkedin`
- Skill: `opensource`
- Audience: developers and editorial-tool builders
- Intent: explain the repository's problem and current scope
- Perspective: project team
- Visual mode: `none`
- Sources: `README.md`, `VISION.md`, `ROADMAP.md`

## Resolved modules

`core.writing-pipeline` → `format.social-post.foundation` → `topic.technology.foundation` → `platform.social.foundation` → `platform.linkedin.foundation` → `language.en.foundation` → `skill.opensource` → source, human-signal, format, topic, platform, task, and editor reviewers.

## Evidence map

- Verified locally: the repository contains the specification, registries, schemas, examples, validation tooling, and starter kit.
- Verified locally: format, topic, platform, skill, tone, perspective, and visual mode resolve as separate concerns.
- Limitation: the specification is stable, but the bundled tooling is not a universal writing engine with a full conformance claim.
- Unknown and omitted: adoption, production use, external response, and measured quality improvement.

## Context gate

Result: `pass`.

The local source set supports the architecture and current-scope statements.
The project-team perspective is authorized and no unsupported traction or
performance claim is required.

## Content design

- Communication goal: introduce the open specification and its current boundary.
- Reader promise: after reading, developers know the problem, architecture, and maturity level.
- Primary claim: the repository provides a stable modular specification and reference foundation for sourced content production.
- Context floor: stable specification status does not prove universal engine conformance.
- Ending: bounded scope statement without engagement bait.

## Final artifact

Human Writing Rules is a stable, vendor-neutral specification for turning a sourced brief into an article, social post, and—when it adds value—an illustration.

The project separates concerns that are often compressed into one large prompt: language, artifact format, topic evidence rules, publishing platform, task, tone, author perspective, and review.

An agent loads the smallest relevant module set, builds an evidence map, passes a context gate, drafts for meaning, and resolves concrete reviewer findings. Generated visuals have a separate integrity rule and cannot be presented as documentary evidence.

The bundled runner remains reference tooling rather than a universal engine with a full conformance claim. The repository contains the stable specification, registries, schemas, examples, validation tooling, and a starter kit.

## Media decision

Decision: no visual.

The architecture is sufficiently summarized in the copy. A generic open-source
cover would add no explanatory value, and a detailed dependency diagram would
exceed the post's single-idea scope.

## Source notes

All capability and scope statements map to the listed local files. No adoption,
universal engine conformance, customer, community-response, or benchmark claim is made.

## Review result

- Reviewed revision: `en-linkedin-opensource-r2`.
- No traction, universal conformance, or quality-improvement claim was added.
- The limitation appears in the post rather than only behind a link.
- No engagement bait or invented personal lesson was used.
- `Visuals: none` is justified by reader benefit rather than template absence.
- Readiness: no blocker or major finding remains.
