# Changelog

## Unreleased

## 1.1.1 — 2026-09-25

- Added a practical editing guide with six RU/EN worked examples, including
  passages that should remain unchanged. Clarified preservation of supplied
  voice, meaning checks, contextual style findings, and when to stop revising
  in the human-signals rule and editor review checklists.
- Fixed CLI version and help output to use the installed package version
  instead of the specification revision, with a regression check from outside
  the repository and without Python on PATH.
- Polished README and package positioning to emphasize grounded AI-assisted
  editorial workflow, evidence boundaries, review contracts, and audit records
  rather than detector-oriented naturalness.

## 1.1.0 — 2026-08-13

- Made the Node.js/TypeScript CLI the primary user entry point and ported
  repository diagnostics, registry/object discovery, module resolution,
  agent-led intake, source-snapshot loading, and run planning. Added complete
  JSON parity tests against the stable Python implementation, Node 20 CI, an
  installable `hwr` binary, and an explicit compatibility roadmap for the
  remaining Python-backed commands.
- Added agent-led intake for conversational writing requests: bounded adaptive
  question rounds, config-default confirmation, separation of user decisions
  from agent-owned research and claim work, a machine-readable intake-plan
  schema, the `runs questions` CLI command, starter-kit instructions, and
  executable tests.
- Added a Dzen platform module for feed-discovered article constraints and a
  reviewed Dzen method example, while tightening Habr publication metadata,
  hub, tag, difficulty, translation, news, and preview checks.
- Added style tone profiles for `blogger`, `developer`, `writer`,
  `screenwriter`, and `amateur`, with explicit guards that tone changes
  delivery but never grants unsupplied authority, experience, scenes, or
  expertise.
- Added GitHub, vc.ru, DEV Community, and newsletter platform modules with
  reviewed examples for release notes, product positioning, tutorial
  boundaries, and source digests.
- Strengthened the content model boundary that platform selection never grants
  topic, evidence standard, tone, author expertise, or first-person claims.
- Strengthened human-signal rules and review checks against stock AI-like
  setup, hype, and transition phrases.
- Added an originality boundary to source integrity: original artifacts need
  their own task-fit structure and must not disguise close paraphrase or
  optimize for AI-detector evasion.
- Added Russian README navigation, synchronized README/content-model platform
  and tone documentation, and excluded Python compatibility tooling from
  GitHub language detection through `.gitattributes`.
- Expanded the reviewed example catalog to 21 examples covering all 11
  registered topics and all 11 registered platform families.

## 1.0.0 — 2026-07-26

- Promoted RFC-0001 through RFC-0006 and all 50 registered runtime objects to
  the stable `1.0.0` profile, with explicit 1.x compatibility, identifier,
  migration, governance, support, security, and release policies.
- Added a machine-readable internal stability review that records the
  non-independent review boundary, passes eight release dimensions, and
  explicitly leaves external review and public comparative model-quality
  evidence unclaimed.
- Prepared the stable `1.0.0` distribution with a
  machine-readable release manifest, synchronized `VERSION` and package
  metadata, pinned specification and registry source revisions, compatibility
  policy, required-artifact and expected-count checks, eight canonical offline
  release gates, shell-free verification, Python 3.9/3.12 CI integration, and
  a finalization runbook.
- Added an offline reference CLI for deterministic module resolution, context
  and visual gates, claim-ledger planning, reviewer selection, and versioned
  run-record validation.
- Added vendor-neutral adapter packets and guarded content-design, draft, edit,
  review, revision, and readiness transitions with a complete executable
  article lifecycle.
- Added a shell-free stdin/stdout adapter runtime with explicit environment
  allowlisting, timeouts, output limits, diagnostic redaction, and an offline
  fixture adapter.
- Added a separately gated visual-production adapter stage and an optional
  fail-closed OpenAI Responses/Image adapter with strict structured outputs,
  explicit live opt-in, environment-only credentials, offline raw-response
  fixtures, and PNG asset handoff.
- Added `workflows run` for a persisted end-to-end editorial execution,
  including atomic run records, conditional visual production, controlled
  `needs-revision` stops, explicit single-cycle `workflows resume`, and a
  separated ready output package.
- Added a reviewed Russian mysticism article pilot with a bounded
  entertainment-topic claim ledger, reproducible stage records, an original
  generated editorial cover, complete review, and a validated ready package.
- Added bounded local source snapshots with a standalone schema, safe
  root-relative loading, symlink-escape protection, UTF-8 and size limits,
  SHA-256 revalidation, adapter-packet content handoff, redacted source-note
  metadata, CLI support, and a reproducible example.
- Added a deterministic consolidated registry index with a standalone schema,
  canonical object/value/RFC projections, source-revision pinning, atomic
  generation, stale and non-canonical checks, CI integration, and contributor
  commands.
- Added an evaluator-neutral benchmark runner with formal case, plan, arm
  result, and run-record schemas; pinned local source snapshots; controlled
  baseline/rules-assisted packets; shell-free bounded execution; raw-result
  retention; explicit failure counts; offline fixtures; and runnable science
  and Telegram benchmark cases.
- Added visual benchmark fixture and acceptance-record contracts with separate
  media-decision and asset applicability, frozen publication and PNG digests,
  visual-record handoff checks, an `auto → none` case, a reviewed generated
  cover, an expected false-documentary hard failure, and standalone validation.
- Added a machine-readable reviewed-example catalog with pinned revisions and
  SHA-256 values, canonical editorial sections, reviewer and visual-decision
  checks, orphan detection, and complete coverage of all 11 registered topics
  and all 6 platform families; added eight bounded RU examples for the
  previously uncovered topic and platform values.
- Added a complete conformance matrix for mandatory and recommended RFC terms,
  lifecycle and evidence rules, a checker, and executable negative fixtures.
- Added an end-to-end article production guide and expanded science,
  technology, and entertainment article rules with research records,
  evidence boundaries, visual decisions, and completion gates.
- Added an end-to-end social-post production guide, deeper generic-social,
  Telegram, and LinkedIn contracts, and complete science, technology, and
  entertainment post examples.
- Expanded RFC-0001 through RFC-0006 into a complete normative profile with
  conformance, precedence, pipeline state, object lifecycle, resolver errors,
  structured review findings, and reproducible benchmark requirements.
- Added a normative RFC index and explicit RFC-first contribution workflow.
- Added independent article/social-post formats and generic blog/social platform foundations.
- Added topic foundations for general, science, technology, entertainment, business, health, finance, culture, lifestyle, education, and travel content.
- Added a visual decision stage, illustration integrity rule, output asset contract, and visual reviewer.
- Added format and topic reviewers and expanded all existing reviewer contracts.
- Added content-model and deterministic context-selection documentation.
- Expanded config, registries, validation expectations, starter kit, skills, platform rules, RFCs, examples, and benchmark contract.

## 0.1.0-init — 2026-07-25

Initial architecture, pipeline, language and platform modules, skills, reviewers, schemas, registry, benchmark case, CI, and starter kit.
