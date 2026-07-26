# Migrating to 1.0

Version `1.0.0` stabilizes the specification and active runtime object set. It
does not claim that every writing engine or the bundled reference tooling
conforms to all 200 implementation requirements.

## Version changes

| Before | 1.0 |
| --- | --- |
| Distribution `0.2.0-draft.1` | Distribution `1.0.0` |
| Specification `0.2.0-draft` | Specification `1.0.0` |
| RFC status `draft` | RFC status `active` |
| Runtime object status `draft` | Runtime object status `active` |
| Draft-preview compatibility | Stable 1.x compatibility |

## Required consumer changes

1. Update pinned `spec_revision` values to `1.0.0`.
2. Regenerate or replace the pinned registry source revision.
3. Re-run module resolution against the 1.0 generated index.
4. Revalidate saved configs, tasks, fixtures, and benchmark cases.
5. Preserve schema and protocol versions independently; do not replace them
   with the distribution version.
6. Review any text that described the project itself as a draft.

Historical audit and pilot records may remain pinned to
`0.2.0-draft`; they describe the source state in which they were produced and
must not be silently rewritten as 1.0 executions.

## Compatibility guarantee

Within 1.x:

- active RFC and object IDs are not reused;
- compatible additions may introduce optional objects or fields;
- breaking normative, identifier, schema, or protocol changes require 2.0;
- a deprecation retains its identifier and migration path for the supported
  1.x line.

See [`COMPATIBILITY.md`](COMPATIBILITY.md) for the complete boundary.
