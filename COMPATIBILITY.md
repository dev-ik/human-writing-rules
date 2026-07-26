# Compatibility

Human Writing Rules `1.0.0` is the first stable specification release. Stable
refers to normative semantics, active identifiers, schemas, protocols, and
documented migration boundaries. It does not mean that every writing engine or
the bundled reference tooling has proven full implementation conformance.

## Version axes

| Axis | Current value | Meaning |
| --- | --- | --- |
| Distribution release | `1.0.0` | Version of this repository snapshot and its tooling |
| Specification revision | `1.0.0` | Normative RFC profile defined by the snapshot |
| Registry source revision | SHA-256 in the generated index | Exact active object and RFC resolver state |
| Schema or protocol version | Defined by each artifact | Compatibility boundary for a specific JSON record or adapter exchange |

Do not substitute one axis for another. A tool can target specification
`1.0.0` while exchanging records with independently versioned schemas.

## Stable 1.x guarantees

Within the 1.x line:

- active RFC, requirement, and object IDs are not silently reused;
- compatible additions may introduce optional objects, fields, or guidance;
- deprecations retain identity and a migration path;
- normative clarifications must preserve existing conforming behavior;
- breaking normative, identifier, schema, or protocol changes require 2.0;
- security fixes may tighten rejection of unsafe inputs without treating
  previously unsafe behavior as a compatibility guarantee.

Pin both `spec_revision` and `registry_source_revision` for reproducible
resolution.

## Runtime support

- Python `3.9` or newer is supported.
- CI validates Python `3.9` and `3.12`.
- Runtime and validation tooling use the Python standard library.
- npm supplies optional command aliases and is not a runtime library
  dependency.
- Core operation and release verification are offline by default.
- Provider-specific live adapters require explicit opt-in and credentials.

## Profiles and implementation claims

The stable specification defines Editorial Core, Editorial Visual, and
Benchmark profiles. An implementation claiming one of those profiles must
supply the evidence required by [`rfcs/README.md`](rfcs/README.md).

The bundled reference runner exercises resolution, gates, records, adapters,
review transitions, examples, and benchmark mechanics. Its passing tests are
tooling evidence, not a blanket claim that it satisfies every one of the 200
implementation requirements. Those requirements remain `planned` until
concrete evidence supports a stronger status.

Conformance is a process claim. It does not guarantee that every output is
factual, safe, lawful, accessible, or publication-ready.

## Historical records

Pilot runs and audit artifacts pinned to `0.2.0-draft` remain historical. They
must not be rewritten to look like 1.0 executions. Current tasks, configs,
benchmarks, examples, and release artifacts use the stable revision.

See [`MIGRATING-TO-1.0.md`](MIGRATING-TO-1.0.md) for consumer changes and
[`RELEASING.md`](RELEASING.md) for release verification.
