# Governance

Human Writing Rules is maintained as an open specification with a bundled
reference toolchain. Specification authority, runtime guidance, examples, and
implementation evidence remain separate.

## Maintainer responsibilities

The repository maintainer:

- accepts or rejects changes;
- assigns RFC and object revisions;
- protects stable identifiers from reuse;
- ensures normative changes are reviewed before dependent runtime changes;
- publishes compatibility and migration notes;
- coordinates security reports and releases.

A maintainer decision does not turn an unsupported editorial claim into
evidence. Normative and benchmark claims remain subject to their declared
review contracts.

## Change classes

| Change | Required process |
| --- | --- |
| Typo or clarification with no semantic effect | Review, validation, patch release when published |
| Backward-compatible runtime guidance | Object review, examples, validation, minor release |
| Normative clarification preserving 1.x behavior | RFC review, conformance mapping, tests, minor or patch release according to impact |
| Breaking normative, schema, protocol, or identifier change | New major release, migration guide, compatibility notice |
| Security fix | Private coordination when needed, regression test, supported-line release |

## RFC process

1. Describe the problem, scope, alternatives, and compatibility impact.
2. Update the governing RFC before dependent runtime modules.
3. Preserve requirement IDs when semantics remain the same.
4. Retire rather than reuse removed requirement or object IDs.
5. Update conformance mapping, fixtures, examples, and migration notes.
6. Pass the manifest-defined release gates.

Normative RFCs with `status: active` define the stable profile. Draft RFCs may
propose future behavior but are not part of a stable conformance claim unless a
profile explicitly incorporates them.

## Decision records

Material decisions belong in the affected RFC, release manifest, compatibility
document, or migration guide. Issue and pull-request discussion is useful
evidence but does not silently modify the specification.

## External review

External review is encouraged for normative, safety-sensitive, cultural, and
interoperability changes. The repository records whether a release received
independent review; it does not label maintainer or agent review as external.

## Releases

The release manifest pins the distribution version, specification revision,
registry source revision, required artifacts, counts, compatibility policy,
and executable gates. A GitHub tag or release must identify the exact commit
that passed those gates.
