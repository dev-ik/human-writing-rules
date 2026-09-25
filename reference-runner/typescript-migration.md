# TypeScript CLI migration

The TypeScript CLI is the primary user entry point. The migration preserves the
stable 1.x command names, JSON envelopes, registry digest, resolution order,
gates, and exit-code classes while replacing the Python implementation in
bounded slices.

## Current support

Node.js 20.10 or newer is required for the native CLI:

```sh
npm install
npm run build
npm run hwr -- --json doctor
```

The package exposes `dist/src/cli.js` as the `hwr` binary. For local repeated
use, `npm link` may be used after installation and build:

```sh
npm link
hwr --json doctor
```

`hwr --version` and the top-level help report the installed distribution version
from `package.json`. The `spec_revision` in `doctor` reports the normative
profile; these versions can differ.

These commands are native TypeScript:

- `doctor`
- `registry get`
- `objects list`
- `objects get`
- `modules resolve`
- `runs questions`
- `runs plan`

The remaining v1.0 commands are delegated without a shell to
`python3 tools/hwr.py`. This compatibility path is explicit: if Python is not
available, the CLI fails instead of pretending that an unported command ran.

## Compatibility contract

Every native command retains the stable envelope:

```json
{
  "ok": true,
  "command": "doctor",
  "data": {},
  "warnings": []
}
```

Errors retain `ok`, `command`, `error.code`, `error.message`, and
`error.details`, together with the existing exit-code mapping. The parity suite
executes the TypeScript and Python CLIs over the same repository and deep
compares complete JSON results for diagnostics, registry reads, discovery,
resolution, intake, planning, and representative errors.

Run all migration checks:

```sh
npm run typecheck
npm run test:ts
npm run release:verify
```

## Remaining slices

Port in dependency order:

1. source snapshot creation and `runs check`;
2. lifecycle transitions and adapter packets;
3. subprocess adapter runtime and persisted workflows;
4. benchmark, conformance, registry-generation, and release validators;
5. provider adapters and their fixtures.

For each slice:

1. add whole-envelope parity tests before switching the npm alias;
2. keep file formats and error codes compatible within 1.x;
3. run both TypeScript and Python implementations in CI;
4. mark the Python path deprecated only after parity passes;
5. remove Python only after every release gate and documented command runs
   natively on Node.js.

Hiding Python with Linguist attributes is not a migration criterion. Completion
means users, CI, release verification, workflows, and adapters no longer need a
Python interpreter.
