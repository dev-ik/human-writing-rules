# Human Writing Rules reference runner

The reference runner enforces deterministic editorial decisions around work
performed by a human, model, or tool adapter:

- repository and revision diagnostics;
- object discovery;
- selective module resolution and dependency ordering;
- task and claim-ledger validation;
- bounded, integrity-checked local source snapshots;
- evaluator-neutral benchmark arm execution;
- minimum context gate;
- media-decision validation;
- reviewer selection;
- vendor-neutral adapter packets;
- guarded design, draft, edit, visual, review, revision, and finalization transitions;
- versioned run-record planning and validation.

The core runner is offline, uses only the Python standard library, requires no
authentication, and does not call a model or generate prose. An external
adapter receives a bounded packet and returns JSON matching the declared stage
schema. The optional OpenAI adapter is isolated behind that same boundary.

The repository-wide validator loads every example task through this runner,
validates the resulting run record, requires both a `context-ready` and a
deliberately `blocked` example, and executes one lifecycle through `ready`.

## Quick start

```text
python3 tools/hwr.py --json doctor

python3 tools/hwr.py --json modules resolve \
  --config starter-kit/.human-writing-rules/config.json \
  --task examples/tasks/ru-science-article.json

python3 tools/hwr.py --json runs plan \
  --config starter-kit/.human-writing-rules/config.json \
  --task examples/tasks/ru-science-article.json \
  --out /tmp/hwr-science-run.json

python3 tools/hwr.py --json runs check \
  --file /tmp/hwr-science-run.json
```

Use `--repo /absolute/path/to/human-writing-rules` when running another copy of
the CLI or when the script cannot infer its repository.

## Commands

| Command | Purpose |
| --- | --- |
| `doctor` | Check repository availability, revisions, indexes, and capabilities |
| `registry get NAME` | Read one raw registry document |
| `objects list` | Discover registered objects with bounded filters |
| `objects get ID` | Read one object record by stable ID |
| `sources snapshot` | Pin one local UTF-8 source by content, size, and SHA-256 |
| `modules resolve` | Resolve config and task overrides into roots and dependency order |
| `runs questions` | Build the next bounded agent-led intake question batch |
| `runs plan` | Build a pre-draft run record with gates and output slots |
| `runs check` | Validate a saved run record against current registries |
| `adapters packet` | Export bounded inputs and the required output schema for one stage |
| `adapters run` | Invoke one trusted stdin/stdout adapter and apply its result |
| `workflows run` | Execute and persist one complete adapter-driven editorial workflow |
| `workflows resume` | Explicitly resume a stopped workflow for at most one revision cycle |
| `runs apply-design` | Apply content design and enter `media-decided` |
| `runs apply-artifact` | Apply a `draft`, `edit`, or `revision` artifact |
| `runs apply-visual` | Apply visual assets produced for the current artifact revision |
| `runs apply-review` | Apply a complete RFC-0005 review report |
| `runs finalize` | Enter `ready` only when every completion invariant passes |

Run `python3 tools/hwr.py --help` and each noun's `--help` for the complete
argument reference.

## Agent-led intake questions

`runs questions` converts missing material inputs, unresolved user choices,
and unconfirmed project defaults into a bounded question batch:

```sh
python3 tools/hwr.py --json runs questions \
  --config starter-kit/.human-writing-rules/config.json \
  --limit 5
```

The task file is optional. With no `--task`, the command starts an
`interactive-intake` record. With a partial task, it preserves explicit task
values and asks only about remaining material choices:

```sh
python3 tools/hwr.py --json runs questions \
  --config starter-kit/.human-writing-rules/config.json \
  --task path/to/partial-task.json \
  --limit 3
```

The result separates:

- `question_batch`: user decisions that currently block drafting;
- `agent_actions`: research, claim classification, freshness checks, and other
  work the agent should perform itself;
- `proposed_defaults`: config-origin values that the current task has not
  explicitly confirmed;
- `remaining_question_count`: questions reserved for a later round.

The CLI does not open an interactive prompt or mutate the task. A conversational
agent or product UI asks the returned batch, records the answers in the task,
and requests the next batch. See
[`guides/agent-led-intake.md`](../guides/agent-led-intake.md) and
[`schemas/intake-plan.schema.json`](../schemas/intake-plan.schema.json).

Run `npm run check` to validate the registries, schemas, starter config, example
tasks, generated run plans, RFC conformance data, and local documentation links
together.

The separate [benchmark runner](../benchmarks/README.md) executes pinned
baseline and rules-assisted arms through the same bounded subprocess boundary.
It preserves every attempt and deliberately leaves scoring and comparative
conclusions to a declared evaluator protocol.

## Generated registry index

The files `registry/objects.json`, `languages.json`, `formats.json`,
`topics.json`, `platforms.json`, `skills.json`, `tones.json`, and `rfcs.json`
remain canonical. The generator combines them into the derived
[`registry/generated-index.json`](../registry/generated-index.json) resolver
manifest. It contains:

- a compact object, dependency, selector, status, and path index;
- public value records with their display and default metadata preserved;
- RFC records and specification revision;
- counts, topic fallback, source-file list, and the canonical registry SHA-256.

No generation timestamp is included, so the same canonical registries produce
the same bytes:

```sh
npm run generate:registry-index
npm run check:registry-index
```

`npm run check` also rejects a missing, stale, invalid, or non-canonically
formatted generated index. Edit the canonical registry files, regenerate the
derived index, inspect the change, and commit both parts together. Consumers
may use the consolidated file for discovery or resolution, but must treat its
`source_revision` as the compatibility boundary.

The document conforms to
[`schemas/generated-registry-index.schema.json`](../schemas/generated-registry-index.schema.json).

## Local source snapshots

The runner does not retrieve URLs. `sources snapshot` accepts one existing
local UTF-8 file and creates a versioned JSON record conforming to
[`schemas/source-snapshot.schema.json`](../schemas/source-snapshot.schema.json).
The snapshot preserves the exact content supplied to an adapter, its media
type, byte count, relative origin, source ID, and SHA-256 digest.

```sh
python3 tools/hwr.py --json sources snapshot \
  --source-root examples/source-snapshots \
  --input materials/evidence-boundary-note.md \
  --source-id SRC-LOCAL-001 \
  --snapshot-id SNAP-EVIDENCE-BOUNDARY-001 \
  --media-type text/markdown \
  --captured-at 2026-07-26 \
  --out /tmp/evidence-boundary-note.snapshot.json
```

Attach the document to a task source:

```json
{
  "id": "SRC-LOCAL-001",
  "title": "Evidence boundary note",
  "role": "local supplied material",
  "snapshot_path": "snapshots/evidence-boundary-note.snapshot.json"
}
```

`runs plan` and `workflows run` resolve `snapshot_path` under the task file's
directory by default. `--source-root PATH` may select a different explicit
root. Absolute paths, `..` traversal, symlink escapes, missing files, invalid
UTF-8, NUL bytes, mismatched source IDs, byte counts, or hashes are rejected.
The limits are 2 MiB per source, 8 MiB total source content, and a bounded
snapshot JSON document.

Snapshot integrity is not source verification: a matching digest proves which
bytes entered the run, not whether their claims are true. Source status,
freshness, scope, rights, and claim classification still require editorial
assessment.

The full snapshot content is stored in the run record and sent in adapter
packets. A persisted workflow therefore contains the supplied source text, and
a live provider adapter transmits it to that provider. Do not attach secrets or
material that may not enter the selected workspace or provider. The separated
`source-notes.json` list omits snapshot content and retains its metadata.

See the complete reproducible
[`examples/source-snapshots/`](../examples/source-snapshots/README.md) fixture.

## Adapter lifecycle

The runner preserves the normative ordering:

```text
context-ready → media-decided → drafted → edited
                                      │
                         selected media produced
                                      │
                                      ↓
                                 reviewed → ready
                                      ↑       |
                                      └ revising
```

The `design` transition enters `media-decided` because `runs plan` has already
recorded the media decision. It refuses the transition while that decision is
pending or blocked.

Use a fresh temporary directory to execute the complete fixture lifecycle:

```sh
RUN_DIR="$(mktemp -d)"

python3 tools/hwr.py --json runs plan \
  --config starter-kit/.human-writing-rules/config.json \
  --task examples/tasks/ru-science-article.json \
  --out "$RUN_DIR/run-0.json"

python3 tools/hwr.py --json adapters packet \
  --file "$RUN_DIR/run-0.json" \
  --stage design

python3 tools/hwr.py --json runs apply-design \
  --file "$RUN_DIR/run-0.json" \
  --input examples/transitions/ru-science-design.json \
  --out "$RUN_DIR/run-1.json"

python3 tools/hwr.py --json runs apply-artifact \
  --file "$RUN_DIR/run-1.json" \
  --input examples/transitions/ru-science-draft.json \
  --out "$RUN_DIR/run-2.json"

python3 tools/hwr.py --json runs apply-artifact \
  --file "$RUN_DIR/run-2.json" \
  --input examples/transitions/ru-science-edit.json \
  --out "$RUN_DIR/run-3.json"

python3 tools/hwr.py --json adapters packet \
  --file "$RUN_DIR/run-3.json" \
  --stage review

python3 tools/hwr.py --json runs apply-review \
  --file "$RUN_DIR/run-3.json" \
  --input examples/transitions/ru-science-review.json \
  --out "$RUN_DIR/run-4.json"

python3 tools/hwr.py --json runs finalize \
  --file "$RUN_DIR/run-4.json" \
  --out "$RUN_DIR/run-5.json"

python3 tools/hwr.py --json runs check \
  --file "$RUN_DIR/run-5.json"
```

The final record contains separated publication copy, visual assets, source
notes, review report, revision summary, and audit history.

## Adapter protocol

`adapters packet` supports `design`, `draft`, `edit`, `visual`, `review`, and
`revision`.
Each packet includes:

- the exact input state and run ID;
- required output schema;
- resolved module manifest with the selected module contents;
- task framing and constraints;
- sources and claim ledger;
- context and media gate records;
- current content design and artifact;
- visual and review context.

An adapter returns one of:

| Stage | Result schema |
| --- | --- |
| `design` | `schemas/content-design.schema.json` |
| `draft`, `edit`, `revision` | `schemas/artifact-record.schema.json` |
| `visual` | `schemas/visual-assets-record.schema.json` |
| `review` | `schemas/review-report.schema.json` |

The runner rejects stale run IDs, reused artifact revisions, wrong parent
revisions, unknown or omitted claims, incomplete selected visuals, undeclared
reviewers, review reports for a stale artifact, and readiness claims that
conflict with open blocker or major findings.

An `edit` or `revision` result may still include complete visual assets for
backward compatibility. When selected media is omitted from the edit result,
the runner records `visual_assets.status = pending-production`, accepts a
separate `visual` result, and blocks both review-packet export and direct review
application until the assets exist.

## Automated stdin/stdout adapters

`adapters run` automates the packet/apply pair without coupling the core runner
to a model vendor:

```sh
RUN_DIR="$(mktemp -d)"
PYTHON_BIN="$(command -v python3)"

python3 tools/hwr.py --json runs plan \
  --config starter-kit/.human-writing-rules/config.json \
  --task examples/tasks/ru-science-article.json \
  --out "$RUN_DIR/run-0.json"

python3 tools/hwr.py --json adapters run \
  --file "$RUN_DIR/run-0.json" \
  --stage design \
  --executable "$PYTHON_BIN" \
  --arg tools/hwr_fixture_adapter.py \
  --out "$RUN_DIR/run-1.json"
```

The fixture adapter is offline test data, not a writing model. Replace the
executable and arguments with a trusted adapter that implements the same
contract.

The child process:

1. receives one adapter packet as UTF-8 JSON on stdin;
2. writes exactly one stage-result JSON object to stdout;
3. sends logs and diagnostics to stderr;
4. exits zero only when the result is complete.

The runtime never invokes a shell. It resolves one executable and supplies
arguments as an array. Use `--arg=-x` when an argument begins with `-`.

By default the child receives only `PATH`, available locale variables, and
existing valid temporary-directory variables. Pass credentials by
environment-variable name, never as an argument:

```sh
python3 tools/hwr.py --json adapters run \
  --file "$RUN_DIR/run-0.json" \
  --stage design \
  --executable ./my-model-adapter \
  --pass-env PROVIDER_API_KEY \
  --out "$RUN_DIR/run-1.json"
```

`--pass-env` copies an existing variable without printing or storing its value.
The audit record retains only the variable name, executable basename, argument
count, duration, and byte counts. Token-like stderr values are redacted before
they enter a JSON error or warning.

Safety limits:

- default timeout: 120 seconds; allowed maximum: 600 seconds;
- default stdout limit: 10 MiB; allowed maximum: 100 MiB;
- stderr hard limit: 1 MiB, with at most 64 KiB retained for diagnostics;
- packet limit: 25 MiB;
- non-zero exit, timeout, invalid UTF-8, non-object JSON, oversized output, and
  stage mismatch fail without changing the input run file;
- stdout and stderr are monitored while the adapter runs; the process is
  stopped when either hard limit is exceeded.

Treat adapter executables as trusted code. A packet contains selected rule
contents and may contain full source snapshots plus private task or source
notes. Pass only the environment variables and source material that adapter
genuinely needs.

## Persisted end-to-end workflow

`workflows run` turns the guarded transitions into one controlled execution. It
plans the run, invokes the same adapter for each applicable stage, saves every
intermediate run record, conditionally runs `visual`, reviews the frozen
artifact, and finalizes only a passing result.

Fixture example that deliberately exercises the separate visual stage:

```sh
WORKSPACE="$(mktemp -d)"
PYTHON_BIN="$(command -v python3)"

python3 tools/hwr.py --json workflows run \
  --config starter-kit/.human-writing-rules/config.json \
  --task examples/tasks/ru-science-article.json \
  --workspace "$WORKSPACE" \
  --executable "$PYTHON_BIN" \
  --arg tools/hwr_fixture_adapter.py \
  --arg=--separate-visual
```

The workspace must be new or empty. The command never reuses or clears a
non-empty directory. Adapter arguments support two literal placeholders:
`{workspace}` expands to the absolute workflow directory and `{stage}` expands
to the current adapter stage.

On success the directory contains:

```text
workflow.json
runs/
  run-00-planned.json
  run-01-design.json
  run-02-draft.json
  run-03-edit.json
  run-04-visual.json
  run-05-review.json
  run-06-finalized.json
output/
  publication.md
  visual-assets.json
  source-notes.json
  review-report.json
  revision-summary.json
  audit.json
  run-final.json
```

`workflow.json` conforms to
[`schemas/workflow-record.schema.json`](../schemas/workflow-record.schema.json).
Its terminal status is:

- `complete`: every gate passed and the separated output package exists;
- `blocked`: the initial context gate failed; no adapter was invoked;
- `needs-revision`: review found an unresolved blocker or major issue;
- `failed`: execution or validation failed; the manifest identifies the last
  valid run and a structured error.

The workflow intentionally does not auto-loop through revisions. A material
finding may require new research or an editorial decision, so `needs-revision`
is a controlled stop rather than permission to repeatedly rewrite unaffected
text. After inspecting the report and supplying any missing evidence, explicitly
resume it:

```sh
python3 tools/hwr.py --json workflows resume \
  --workspace "$WORKSPACE" \
  --executable "$PYTHON_BIN" \
  --arg tools/hwr_fixture_adapter.py
```

One resume invocation may apply one `revision`, conditionally produce or
re-produce visuals, re-run review, and finalize. If material findings remain,
it returns to `needs-revision`; another cycle requires another explicit command.
It can also recover a `failed` or interrupted workflow from its last persisted
valid state. `blocked` and `complete` workflows are not resumable.

## Optional OpenAI adapter

[`tools/hwr_openai_adapter.py`](../tools/hwr_openai_adapter.py) is the first
provider implementation. It uses the Responses API with strict Structured
Outputs for `design`, `draft`, `edit`, `review`, and `revision`. For `visual`,
it first produces grounded prompt/caption/alt/provenance metadata through the
Responses API and then creates one PNG through the Image API.
Its text stages always return an empty `visuals` array: a language-model
response is not allowed to claim that an asset exists. Selected media therefore
uses the separate `visual` call, which writes and validates the actual file.

The adapter is fail-closed:

- it has no implicit network mode;
- `--live` is required for every live execution;
- `OPENAI_API_KEY` must be explicitly allowlisted through `--pass-env`;
- credentials are read from the environment, never from CLI arguments or files;
- its API base URL is fixed to `https://api.openai.com/v1`;
- fixture mode requires no credential and exercises the same response parsers;
- generated images are size-limited and must have a PNG signature.

For offline verification:

```sh
PYTHON_BIN="$(command -v python3)"

python3 tools/hwr.py --json adapters run \
  --file "$RUN_DIR/run-0.json" \
  --stage design \
  --executable "$PYTHON_BIN" \
  --arg tools/hwr_openai_adapter.py \
  --arg=--fixture-response \
  --arg examples/provider-fixtures/openai-design-response.json \
  --out "$RUN_DIR/run-1.json"
```

For an explicit live design call:

```sh
export OPENAI_API_KEY="..."
PYTHON_BIN="$(command -v python3)"

python3 tools/hwr.py --json adapters run \
  --file "$RUN_DIR/run-0.json" \
  --stage design \
  --executable "$PYTHON_BIN" \
  --arg tools/hwr_openai_adapter.py \
  --arg=--live \
  --pass-env OPENAI_API_KEY \
  --timeout-seconds 300 \
  --out "$RUN_DIR/run-1.json"
```

The same provider can drive a complete workflow:

```sh
export OPENAI_API_KEY="..."
WORKSPACE="$(mktemp -d)"
PYTHON_BIN="$(command -v python3)"

python3 tools/hwr.py --json workflows run \
  --config starter-kit/.human-writing-rules/config.json \
  --task examples/tasks/ru-science-article.json \
  --workspace "$WORKSPACE" \
  --executable "$PYTHON_BIN" \
  --arg tools/hwr_openai_adapter.py \
  --arg=--live \
  --arg=--asset-dir \
  --arg={workspace}/assets \
  --pass-env OPENAI_API_KEY \
  --timeout-seconds 600
```

For a selected illustration after an edit that returned an empty `visuals`
array:

```sh
python3 tools/hwr.py --json adapters run \
  --file "$RUN_DIR/run-3.json" \
  --stage visual \
  --executable "$PYTHON_BIN" \
  --arg tools/hwr_openai_adapter.py \
  --arg=--live \
  --arg=--asset-dir \
  --arg "$RUN_DIR/assets" \
  --pass-env OPENAI_API_KEY \
  --timeout-seconds 600 \
  --out "$RUN_DIR/run-visual.json"
```

The defaults are `gpt-5.6-sol` for text and `gpt-image-2` for images. Pin them
with `--arg=--text-model`, `--arg MODEL_ID`, `--arg=--image-model`, and
`--arg IMAGE_MODEL_ID` when reproducibility matters. Other controls include
`--reasoning-effort`, `--max-output-tokens`, `--request-timeout`,
`--image-size`, and `--image-quality`.

The adapter sends the complete stage packet—including selected module contents,
sources, claims, and current artifact—to the API. Do not use live mode when
those inputs may not leave the local environment. Image generation may also
require OpenAI organization verification. See the official
[Responses text guide](https://developers.openai.com/api/docs/guides/text),
[Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs),
and [Image generation guide](https://developers.openai.com/api/docs/guides/image-generation).

Live requests are intentionally not part of repository tests: they require
credentials, network access, incur provider usage, and are not deterministic.
The checked-in raw-response fixtures verify parsing, lifecycle application, and
PNG handoff without claiming live-provider availability.

## JSON policy

With global `--json`, stdout contains one compact JSON envelope and no progress
text.

Success:

```json
{
  "ok": true,
  "command": "runs.check",
  "data": {},
  "warnings": []
}
```

Error:

```json
{
  "ok": false,
  "command": "runs.check",
  "error": {
    "code": "RUN_INVALID",
    "message": "Run record is invalid",
    "details": []
  }
}
```

Errors return a non-zero exit code. A successfully planned editorial run may
itself have `state: blocked`; that is a valid command result containing explicit
blockers and remediation.

## Resolution behavior

The runner:

1. preserves task values over project config values;
2. validates pinned specification and registry revisions;
3. maps public values through registry indexes;
4. falls back from an unknown topic to `general`;
5. falls back from an unknown or missing platform to `blog` for articles or
   `social` for social posts;
6. rejects unknown skills, tones, reviewers, and incompatible platform-format
   combinations;
7. adds required core, rule, format, topic, platform, visual, and reviewer
   roots;
8. emits dependencies before dependants.

Every fallback and inference remains visible in the resolution record.

## Gate boundary

`runs plan` checks whether drafting may begin. It blocks missing material
context, required sources, unresolved freshness or platform constraints,
unauthorized first-person or expert perspective, unsupported material claims,
unknown claims selected for use, and incomplete required visual decisions.

The runner does not:

- retrieve sources;
- determine whether a source is true;
- infer private author experience;
- generate text or images;
- execute model review;
- trust an adapter's readiness claim without validating it.

`runs finalize` may label a run `ready`, but only after a complete review,
material-finding checks, selected visual review, and output-package consistency
checks pass.
