# Security Policy

Human Writing Rules processes source material, prompts, generated artifacts,
adapter packets, and optional provider credentials. Treat every external
adapter and source snapshot as a trust-boundary crossing.

## Supported versions

Security fixes are provided for the latest stable `1.x` release. A
release-candidate or historical draft receives a fix only when the issue also
affects the supported stable line or blocks stabilization.

## Report a vulnerability

Use GitHub private vulnerability reporting for
`dev-ik/human-writing-rules`. Do not open a public issue containing an exploit,
credential, private source, personal data, unpublished communication, or
proprietary benchmark input.

Include:

- affected version and commit when known;
- affected command, schema, adapter, or workflow;
- reproduction steps using synthetic data;
- expected and observed security boundary;
- impact and whether network or live-provider access is required.

If private vulnerability reporting is unavailable, open a public issue without
sensitive details and request a private contact channel.

## Response expectations

The maintainer should acknowledge a report within seven days, confirm scope
before publishing details, and coordinate a fix and disclosure date with the
reporter. These are project targets, not a service-level agreement.

## Security boundaries

- Core validation and release verification are offline by default.
- Provider credentials belong in environment variables and must not enter
  tasks, fixtures, logs, release manifests, or adapter results.
- Source snapshots reject unsafe paths, symlink escapes, oversized files, and
  digest mismatches.
- Subprocess adapters are trusted code but receive a bounded packet and
  shell-free invocation.
- Generated visuals, prompts, source material, and benchmark inputs retain
  their privacy, license, likeness, and disclosure obligations.

Never include real secrets or private data in a proof of concept.
