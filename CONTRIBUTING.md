# Contributing

Every contribution must explain the writing problem, evidence, scope, non-applicable cases, relationships, and evaluation method. Rules must be narrowly scoped and must not present one culture's conventions as universal. Stable IDs are never reused.

Before adding or materially changing runtime rules, read `rfcs/README.md` and the affected normative RFCs. If the proposed behavior is not supported by the current pipeline, object model, resolver, review contract, or benchmark contract, update the RFC layer first.

## Choose the right object

- Add a `format` only when the artifact shape changes.
- Add a `topic` when a domain has distinct evidence or risk requirements.
- Add a `platform` only for durable publishing constraints.
- Add a `skill` for a repeatable job to be done.
- Add a `tone` for legitimate delivery guidance.
- Add a cross-cutting `rule` for integrity, safety, accessibility, or style.

Do not encode the same concern in several object kinds.

## Required contribution path

1. Define the problem and non-applicable cases.
2. Identify the governing RFC requirements and any required normative change.
3. Update and review the normative RFC before dependent runtime rules when semantics change.
4. Add or update the module with matching frontmatter.
5. Register the object and dependencies.
6. Update the relevant format, topic, platform, tone, or configuration index.
7. Run `npm run generate:registry-index` and inspect the derived manifest.
8. Add or update a full example and benchmark contract.
9. Run `npm run check`.
10. Record limitations and skipped validation.

Changes intended for a release candidate must also update `VERSION`,
`CHANGELOG.md`, `COMPATIBILITY.md`, and `release/manifest.json` when their
pinned values or claims change. Run `npm run release:verify`; do not replace a
manifest gate with a weaker command or describe a draft profile as stable.

Visual contributions must include purpose, factual boundaries, platform constraints, alt-text expectations, rights or provenance handling, and reviewer criteria.
