# Human Writing Rules

[English](README.md) | [Русский](README.ru.md)

> A vendor-neutral editorial specification for publication-ready articles, social posts, and optional illustrations.

Human Writing Rules helps an AI agent turn a brief and a source set into a grounded, audience-aware content package. The package may contain a long-form article, a social post, and—when it serves a clear purpose—an illustration brief and generated visual.

It is not an AI writer, an AI-detector evasion kit, or one giant prompt. It is a modular specification for a repeatable editorial process.

## Supported content

- Long-form articles for a generic blog, Habr, Dzen, Setka, GitHub, vc.ru, DEV Community, or newsletters
- Social posts for a generic social platform, Telegram, or LinkedIn
- Science, technology, entertainment, business, health, finance, culture, lifestyle, education, travel, and mixed topics
- Product launches, personal stories, tutorials, news, and open-source announcements
- Optional editorial, explanatory, cover, and diagram-like visual briefs

The registries are extensible. An unknown topic uses the general topic foundation until a narrower reviewed module exists.

## Pipeline

```text
Brief → Module resolution → Sources → Evidence map → Context gate
      → Content design → Media decision → Draft → Edit
      → Optional visual generation → Review → Revision → Output package
```

## Principles

- Research before drafting
- Facts before fluency
- Audience before format
- Meaning before engagement
- Human signals instead of cosmetic anti-AI tricks
- Native writing instead of literal translation
- Selective context loading instead of giant prompts
- Review before publishing
- Benchmarks instead of unsupported quality claims
- Model and vendor neutrality

## Content model

Each selection answers a different question:

| Axis | Question | Examples |
|---|---|---|
| `content_type` | What artifact are you making? | `article`, `social-post` |
| `topic` | What evidence and domain risks apply? | `science`, `technology`, `entertainment` |
| `platform` | Where will it be published? | `blog`, `habr`, `dzen`, `github`, `newsletter`, `telegram` |
| `skill` | What job should the artifact do? | `news`, `tutorial`, `product-launch` |
| `tone` | How should it sound? | `expert`, `friendly`, `personal`, `blogger`, `developer`, `writer`, `screenwriter`, `amateur` |
| `author_perspective` | From whose position is it written? | `editorial`, `first-person`, `expert`, `neutral` |

See [`core/content-model.md`](core/content-model.md) for resolution and fallback rules.

## Status

The current stable release is `1.1.0`, built on the active `1.0.0` normative
profile and stable 1.x identifier and compatibility boundaries. Stable
specification status does not imply that every writing engine or the bundled
reference tooling has proven full implementation conformance. See
[Compatibility](COMPATIBILITY.md), [Migration](MIGRATING-TO-1.0.md), and
[Releasing](RELEASING.md).

The repository includes RU and EN language modules, article and social-post
formats, generic and platform-specific publishing modules, topic playbooks,
tone profiles, optional visual integrity rules, reviewers, schemas,
registries, examples, a reference runner, benchmark contracts, and a starter
kit.

RFC-0001 through RFC-0006 form the [stable normative profile](rfcs/README.md). They define conformance, pipeline states, object lifecycle, module resolution, review, and benchmarking. Runtime rules implement narrower behavior and MUST NOT weaken the RFC invariants.

Verify the complete release offline:

```sh
npm run release:verify
```

The primary user-facing CLI is written in TypeScript and runs on Node.js
20.10 or newer:

```sh
npm install
npm run hwr -- --json doctor
npm run hwr -- --json runs questions \
  --config starter-kit/.human-writing-rules/config.json
```

Registry access, object discovery, module resolution, intake questions, and
run planning execute natively in TypeScript. Commands not yet ported keep
working through a temporary Python 3.9+ compatibility backend. The migration
status and removal criteria are documented in
[TypeScript CLI migration](reference-runner/typescript-migration.md).

## Quick start

Copy `starter-kit/.human-writing-rules/` into a target repository or add this repository as a pinned submodule. Then instruct an agent:

```text
Follow Human Writing Rules.
Language: ru
Content type: article
Topic: science
Platform: blog
Skill: news
Audience: curious readers without specialist training
Intent: explain what a new study found and what it did not prove
Visuals: auto
Use only verified facts from the supplied sources.
```

The agent starts with `AGENTS.md`, resolves the smallest sufficient module set through `registry/objects.json`, and follows `core/writing-pipeline.md`. `Visuals: auto` means “include a visual only when it adds explanatory or editorial value,” not “always generate an image.”

If the request is incomplete, the agent leads a bounded
[intake interview](guides/agent-led-intake.md): it asks at most five material
questions per round, waits for answers, and does not shift research,
claim-ledger, registry, or review work to the user. A user may begin simply
with “write an article about mysticism”; the agent gathers the audience,
outcome, source boundary, platform, author position, constraints, and visual
requirement before drafting.

## Expected output

Return these sections separately:

1. **Final artifact** — only publication-ready copy.
2. **Visual assets** — generated files or generation-ready briefs, prompts, captions, and alt text when selected.
3. **Source notes** — claim-to-source mapping, dates, and unresolved uncertainty.
4. **Review report** — findings and the revisions made.
5. **Audit record** — pinned specification and registry revisions, resolved modules, gates, fallbacks, and deviations; it MAY be retained by tooling instead of displayed to the publication reader.

Omit internal notes from the publication-ready artifact unless the target format requires them.

## Structure

```text
core/          mandatory pipeline and content model
principles/    durable principles
rules/         format, topic, language, platform, visual, style, source, and human-signal rules
skills/        task-specific workflows
reviewers/     independent review roles
rfcs/          stable normative specification and conformance contracts
schemas/       machine-readable formats
registry/      object indexes and dependencies
examples/      end-to-end examples
benchmarks/    reproducible evaluation cases
starter-kit/   project integration package
src/           primary TypeScript CLI and reference runtime
tools/         Python compatibility, validation, and release tooling
test-ts/       cross-runtime CLI contract tests
```

The TypeScript CLI is the primary user-facing runtime. Python files under
`tools/` and `tests/` are compatibility, validation, and release support code;
they are excluded from GitHub language detection through `.gitattributes` so
the repository language reflects the primary implementation surface.

Canonical registry files are compiled into a deterministic
[`registry/generated-index.json`](registry/generated-index.json) resolver
manifest. Regenerate it after registry changes and verify it with
`npm run check:registry-index`; see the
[generated index contract](reference-runner/README.md#generated-registry-index).

For complete end-to-end processes, use
[Producing a grounded article](guides/article-production.md) or
[Producing a grounded social post](guides/social-post-production.md). Apply the
selected [format rules](rules/format/), [topic foundations](rules/topic/),
platform module, and
[illustration integrity rule](rules/visual/illustration-integrity.md).

To execute the deterministic lifecycle, use the
[reference runner](reference-runner/README.md). It resolves modules, validates
the claim ledger and gates, exports vendor-neutral adapter packets, validates
stage results, can invoke a trusted stdin/stdout adapter without a shell, and
produces a versioned output package without depending on a model vendor.
An optional, fail-closed
[OpenAI Responses/Image adapter](reference-runner/README.md#optional-openai-adapter)
is included for explicit live use or credential-free fixture testing; the core
runner remains provider-neutral and offline.
For a complete persisted execution, `workflows run` saves every intermediate
state and returns separate publication, visual, source, review, revision, and
audit files; see the
[workflow guide](reference-runner/README.md#persisted-end-to-end-workflow).
Local materials can be pinned with
[`sources snapshot`](reference-runner/README.md#local-source-snapshots), which
checks their path, size, source identity, byte count, and SHA-256 before they
enter a run or provider packet.

For a reviewed non-trivial execution, inspect the
[Russian mysticism article pilot](examples/pilot-runs/ru-mysticism/README.md):
it includes the article, generated cover, claim ledger, stage records, review,
and validated final run.

The [reviewed example catalog](examples/README.md#reviewed-example-catalog)
covers every registered topic and platform family without requiring an
artificial full cross-product. Run `npm run check:reviewed-examples` to verify
the catalog, pinned artifact digests, editorial sections, reviewer sets, and
coverage.

For controlled comparisons, the
[benchmark runner](benchmarks/README.md) executes pinned arms, preserves
failures and raw outputs, and leaves evaluation separate from execution.
The same benchmark contract now includes
[visual acceptance fixtures](benchmarks/README.md#visual-acceptance-fixtures)
for `auto → none`, selected generated assets, and expected hard failures. Run
`npm run check:visual-benchmarks` to verify their frozen artifacts, PNG bytes,
handoff metadata, and acceptance records.

## License

MIT.
