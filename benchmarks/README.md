# Reproducible benchmarks

The benchmark runner executes pinned arms and preserves evidence. It does not
score writing, select a winner, or turn one run into a general quality claim.
The normative requirements are defined by
[`RFC-0006`](../rfcs/RFC-0006-benchmarking.md).

## Artifacts

| Artifact | Contract |
| --- | --- |
| Case | Task, sources, required modules, evaluation protocol, hard failures, output parts, and limitations |
| Plan | Shared provider/model/settings/environment, treatment difference, arms, repetitions, run date, and retry policy |
| Arm result | One adapter-produced output unit with source access, errors, manual intervention, and hard failures |
| Run record | Every attempted arm, invocation metadata, packet/result files, counts, warnings, revisions, and evaluation status |

Machine-readable schemas:

- [`benchmark-case.schema.json`](../schemas/benchmark-case.schema.json);
- [`benchmark-plan.schema.json`](../schemas/benchmark-plan.schema.json);
- [`benchmark-arm-result.schema.json`](../schemas/benchmark-arm-result.schema.json);
- [`benchmark-run-record.schema.json`](../schemas/benchmark-run-record.schema.json);
- [`visual-benchmark-fixture.schema.json`](../schemas/visual-benchmark-fixture.schema.json);
- [`visual-acceptance-record.schema.json`](../schemas/visual-acceptance-record.schema.json).

Checked-in cases live in [`cases/`](cases/). Their task/config construction
files live in [`tasks/`](tasks/) and [`configs/`](configs/). Runnable plans live
in [`plans/`](plans/).

## Visual acceptance fixtures

Visual fixtures test the media decision separately from the selected asset.
This preserves the `RFC-0006` rule that a justified `auto → none` decision is
not penalized for missing visual polish.

Checked-in fixtures live in [`visual-fixtures/`](visual-fixtures/) and point to
acceptance records in [`visual-acceptance/`](visual-acceptance/). Every fixture
pins the publication artifact, requested visual mode, decision, applicable
dimensions, hard failures, expected outcome, and—when selected—the brief,
asset bytes, dimensions, provenance, and disclosure.

| Decision | Media decision | Asset dimensions | Asset required |
| --- | --- | --- | --- |
| `none` | Evaluated | `not-applicable` | No |
| `selected` | Evaluated | Evaluated | Yes |
| `blocked` | Evaluated | `not-applicable` | No |

The required visual dimensions are media decision, factual consistency,
text-image alignment, documentary integrity, platform handoff, accessibility,
and rights/provenance. A passing record requires every applicable dimension to
pass and every declared hard failure to be `not-triggered`.

Negative fixtures are contract tests, not repository defects. They use
`fixture_purpose: negative`, declare `expected_overall: fail`, and preserve the
failed dimensions and triggered hard failures. The checked-in false-documentary
fixture verifies that a high or technically valid asset result cannot erase a
semantic hard failure. Use `fixture_purpose: boundary` with an expected
`blocked` or `incomplete` result for a required asset that cannot safely be
produced or reviewed.

Run the standalone validator:

```sh
npm run check:visual-benchmarks
```

It verifies safe repository-relative paths, bounded reads, artifact and asset
SHA-256 values, valid PNG structure and dimensions, visual-record handoff,
dimension applicability, hard-failure consistency, and the expected overall
result. It does not automate semantic judgment; acceptance evidence remains a
review artifact and records evaluator independence and limitations.

To add a fixture:

1. freeze the publication artifact and record its SHA-256;
2. declare `requested_mode`, `decision`, rationale, and all seven dimensions;
3. for `selected`, pin the brief, PNG, handoff metadata, dimensions, provenance,
   disclosure, and optional visual-production record;
4. write a separate acceptance record with evidence for every dimension and
   hard failure;
5. use `not-applicable` for every asset dimension when no asset exists;
6. run `npm run test:visual-benchmarks` and
   `npm run check:visual-benchmarks`.

## Offline fixture run

The fixture validates execution mechanics only. Its output must not be cited as
evidence that either arm writes better.

```sh
BENCH_WORKSPACE="$(mktemp -d)"
PYTHON_BIN="$(command -v python3)"

python3 tools/hwr_benchmark.py \
  --plan benchmarks/plans/offline-fixture-science-001.json \
  --workspace "$BENCH_WORKSPACE/run" \
  --executable "$PYTHON_BIN" \
  --arg tools/hwr_benchmark_fixture_adapter.py
```

The workspace must be new or empty:

```text
benchmark-run.json
attempts/
  r01-baseline/
    packet.json
    result-raw.json
  r01-rules-assisted/
    packet.json
    result-raw.json
```

Run `npm run test:benchmark` for offline contract, failure-retention, treatment
boundary, safety-limit, and CLI tests.

## Controlled inputs

For every attempt, the runner:

1. loads the task and config pinned by the case;
2. snapshots each declared repository source as bounded UTF-8 content;
3. requires the task to pass the context gate;
4. checks required modules and reviewers;
5. sends identical task, source, output, hard-failure, and shared-control data
   to every arm;
6. adds the resolved HWR module contents, claim ledger, and gates only to the
   `rules-assisted` treatment;
7. records the exact treatment difference in the run manifest.

Provider, model, model revision, generation settings, execution environment,
tool/retrieval configuration, time budget, output requirements, run date, and
retry policy are shared plan controls. The runner records these declarations;
it cannot prove that an external adapter honestly honored its provider or model
settings.

## Arm adapter protocol

The runner invokes one trusted executable for all arms through the same
shell-free, bounded stdin/stdout runtime used by editorial adapters. Each
packet has `stage: benchmark-run`. The executable returns one JSON object
conforming to `benchmark-arm-result.schema.json`.

This is a whole-arm protocol. The stage-oriented OpenAI adapter does not
implement it directly; a provider benchmark adapter must run the intended
baseline or complete HWR workflow and return the observable output unit.

Environment variables are absent unless explicitly named with `--pass-env`.
The default timeout is 120 seconds, stdout is bounded, stderr diagnostics are
bounded and redacted, and the input packet has a 25 MiB limit. Treat arm
adapters as trusted code: packets contain full pinned source text.

## Failure and ordering policy

Runner version 1.0:

- permits 1–10 repetitions and at most 50 attempts;
- performs no automatic retries;
- executes arms in their declared order and records
  `execution_order: declared-arm-order`;
- never excludes an attempt automatically;
- saves a raw JSON result before semantic validation;
- continues after a failed, blocked, or invalid arm;
- returns `complete-with-failures` when not every attempt completed.

Declared ordering can create order effects. Counterbalancing or randomized
orders require a future plan revision and must not be simulated by silently
reordering attempts.

## Evaluation boundary

`benchmark-run.json` always starts with `evaluation.status: not-run`. Evaluation
must be a separate, declared process using the case dimensions, scale anchors,
hard failures, blinding policy, and raw ratings.

Report attempted, completed, blocked, failed, invalid, hard-failure, and
excluded counts. Do not discard a run because it weakens the desired result.
Keep averages separate from hard failures, retain case/dimension detail, label
small samples exploratory, and limit conclusions to the tested cases,
languages, formats, topics, platforms, models, tools, dates, and revisions.
