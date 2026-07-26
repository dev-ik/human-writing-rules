# Conformance requirements

This directory is the traceability layer between the normative RFC profile and
future validators, fixtures, and benchmark evidence. It answers three separate
questions:

1. Which normative obligations exist?
2. Who owns their implementation and verification?
3. Which obligations have evidence strong enough to claim conformance?

The matrix does not make an implementation conformant by itself. A `planned`
record proves only that the obligation is known and tracked.

## Source of truth

Normative meaning remains in [RFC-0001](../rfcs/RFC-0001-vision-and-scope.md)
through [RFC-0006](../rfcs/RFC-0006-benchmarking.md). The checked-in
[requirements matrix](requirements.json) adds stable traceability metadata; it
does not replace or weaken RFC text.

The extraction unit is one physical Markdown line containing uppercase `MUST`,
`MUST NOT`, `SHOULD`, or `SHOULD NOT`, excluding fenced code and inline code.
One unit can contain more than one normative term. If a unit ends with a colon,
its subordinate list or table remains part of the RFC obligation even though
the list is not copied into the matrix.

`MAY` defines permitted variation rather than an implementation obligation, so
it remains normative RFC context but does not receive a conformance requirement
ID. A `SHOULD` or `SHOULD NOT` record does receive an ID because an implementation
must be able to disclose a justified deviation.

This line-based rule is deliberately mechanical. Reflowing, editing, adding, or
removing a normative source line requires an explicit matrix review.

## Stable requirement IDs

Active requirements use these namespaces:

| RFC | Prefix | Ownership domain |
| --- | --- | --- |
| RFC-0001 | `HWR-SCOPE` | specification governance |
| RFC-0002 | `HWR-PIPE` | writing pipeline |
| RFC-0003 | `HWR-OBJ` | object model |
| RFC-0004 | `HWR-RESOLVE` | module resolver |
| RFC-0005 | `HWR-REVIEW` | review contract |
| RFC-0006 | `HWR-BENCH` | benchmarking |

An assigned ID is never reused for another meaning. When its source obligation
is removed, move the ID to `retired_requirements` with the removal revision and
reason. Gaps in a namespace are valid.

## Status and evidence

| Status | Meaning | Evidence rule |
| --- | --- | --- |
| `planned` | Requirement is mapped but not implemented or proven | No conformance claim |
| `implemented` | Intended behavior exists | Verification is still incomplete |
| `verified` | The declared verification method passed | `evidence` is required |
| `not-applicable` | The requirement cannot apply to the claimed implementation | `rationale` is required |

Defaults assign each RFC an owner, applicable conformance profiles, and a
verification method. An individual requirement may override those fields when
its real verification boundary is narrower.

Evidence should name a repository-relative test, fixture, validator rule,
benchmark record, or review artifact. A prose assertion such as “implemented”
is not sufficient evidence.

## Change workflow

When normative RFC text changes:

1. Run `python3 tools/check_conformance_requirements.py`.
2. For every reported unmapped unit, assign the next unused ID in that RFC
   namespace and add a `planned` record.
3. For every stale record, decide whether the obligation was reworded, replaced,
   or removed. Preserve its ID only when its meaning is preserved.
4. Move removed IDs to `retired_requirements`; never recycle them.
5. Update owner, profiles, verification method, status, and evidence only from
   concrete implementation facts.
6. Run `npm run check`.
7. Run `npm run test:conformance` after changing the checker or matrix contract.

The checker enforces one-to-one source coverage for mandatory and recommended
requirements, exact normative-term counts, valid namespaces, non-reused active
or retired IDs, RFC revision alignment, and the evidence rules for terminal
statuses.

## Executable fixtures

Fixtures in [fixtures](fixtures/) test the conformance control itself. They
cover the valid baseline and failure modes such as normative-source drift, an
unmapped `SHOULD`, duplicate or reused IDs, revision mismatch, changed keyword
counts, and `verified` without evidence.

Run them with:

```text
npm run test:fixtures
```

These fixtures prove that traceability failures are detected. They do not prove
that an external writing implementation satisfies the 200 editorial
requirements. Those records remain `planned` until an implementation supplies
the declared validator, test, review, or benchmark evidence.

## Current verification boundary

The matrix intentionally marks all editorial requirements `planned`.
Traceability and checker failure modes are now executable, but the repository
does not contain a conforming writing-engine implementation. Later stages may
add implementation fixtures and verification artifacts, but must not relabel
requirements `verified` without evidence.
