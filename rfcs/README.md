# Normative RFC Profile

RFC-0001 through RFC-0006 define the stable `1.0.0` normative profile for
Human Writing Rules. Runtime modules implement narrower guidance; they do not
replace the RFC contracts.

## Normative language

The keywords have these meanings:

- **MUST / REQUIRED:** necessary for conformance.
- **MUST NOT / PROHIBITED:** incompatible with conformance.
- **SHOULD / RECOMMENDED:** expected unless a documented task-specific reason justifies a deviation.
- **SHOULD NOT:** normally prohibited; a documented exception may be valid.
- **MAY / OPTIONAL:** permitted but not required.

`Active` means the RFC belongs to the stable 1.x profile. Normative semantics
and identifiers follow [`COMPATIBILITY.md`](../COMPATIBILITY.md). Experimental
implementation status does not make normative statements optional for an
implementation claiming conformance.

## RFC map

1. [RFC-0001 — Vision and Scope](RFC-0001-vision-and-scope.md): authority, invariants, profiles, and boundaries.
2. [RFC-0003 — Object Model](RFC-0003-object-model.md): stable objects, metadata, dependencies, and lifecycle.
3. [RFC-0004 — Selective Module Resolution](RFC-0004-selective-module-resolution.md): deterministic selection and conflict handling.
4. [RFC-0005 — Review Contract](RFC-0005-review-contract.md): reviewer input, findings, disposition, and readiness.
5. [RFC-0002 — Normative Writing Pipeline](RFC-0002-normative-writing-pipeline.md): state transitions and output package.
6. [RFC-0006 — Benchmarking](RFC-0006-benchmarking.md): reproducible evaluation and claim limits.

The numeric IDs are stable identifiers, not a required reading order.

## Profiles

- **Editorial Core:** RFC-0001 through RFC-0005; supports text artifacts and `visuals.mode: none`.
- **Editorial Visual:** Editorial Core plus the visual requirements in RFC-0002 and RFC-0005.
- **Benchmark:** Editorial Core plus RFC-0006. Visual benchmarks also require Editorial Visual.

An implementation MAY support more than one profile.

## Precedence

When requirements conflict, apply this order:

1. applicable law, contract, consent, rights, safety, privacy, and mandatory disclosure;
2. non-negotiable integrity requirements in RFC-0001 and RFC-0002;
3. explicit task facts and constraints supplied by an authorized user;
4. normative RFC contracts;
5. registered core and rule objects;
6. selected language, format, topic, platform, skill, tone, and reviewer objects;
7. implementation defaults;
8. examples and benchmark outputs.

An explicit stylistic choice MAY override a default or recommendation. It MUST NOT override factual integrity, legitimate perspective, required disclosure, rights, or a failed context or visual gate.

Within the same level, a narrower applicable module overrides a broader one only for its declared scope. A platform module cannot weaken a topic evidence requirement. A tone module cannot authorize fabricated first-person experience.

## Conformance statement

An implementation claiming conformance MUST report:

- specification revision or pinned repository commit;
- supported profile or profiles;
- supported object kinds and registry indexes;
- unsupported required capabilities;
- documented deviations from `SHOULD` requirements;
- validation and benchmark evidence used for the claim.

Conformance describes process behavior. It MUST NOT be advertised as proof that every output is factual, safe, legally compliant, or high quality.

## Informative material

README files, examples, roadmap entries, benchmark outputs, and commentary are informative unless an RFC explicitly incorporates them. They illustrate the contract but cannot silently add or remove normative requirements.
