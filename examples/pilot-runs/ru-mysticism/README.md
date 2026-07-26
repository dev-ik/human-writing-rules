# RU mysticism article pilot

This pilot tests a Russian blog article about mysticism without treating
supernatural events as verified facts.

## Editorial frame

- **Format:** article
- **Topic:** entertainment
- **Platform:** generic blog
- **Primary job:** critical analysis
- **Perspective:** editorial
- **Visual mode:** auto, selected
- **Reader promise:** explain how bounded uncertainty differs from arbitrary
  vagueness in a mystical story

The article does not name existing works, invent author experience, imitate a
living author, or make universal psychological claims. Its material claims are
classified as bounded editorial inference or opinion. The deliberately
universal claim `C-004` is recorded as unknown and omitted.

## Artifacts

- [`config.json`](config.json) — archived `0.2.0-draft` configuration that
  produced the checked-in result
- [`config-1.0.json`](config-1.0.json) — migrated configuration for replay
  against the stable `1.0.0` profile
- [`task.json`](task.json) — framing, sources, claim ledger, and media brief
- [`stages/`](stages/) — design, draft, edit, visual, and review adapter records
- [`result/publication.md`](result/publication.md) — publication-ready article
- [`assets/mystical-doorway-cover.png`](assets/mystical-doorway-cover.png) —
  generated 1536×1024 editorial cover
- [`result/visual-assets.json`](result/visual-assets.json) — prompt, caption,
  alt text, disclosure, provenance, dimensions, and SHA-256
- [`result/source-notes.json`](result/source-notes.json) — separated source notes
- [`result/review-report.json`](result/review-report.json) — complete eight-role review
- [`result/run-final.json`](result/run-final.json) — final validated run record

## Reproduce the lifecycle

Run from the repository root:

```sh
WORKSPACE="$(mktemp -d)"

python3 tools/hwr.py --json workflows run \
  --config examples/pilot-runs/ru-mysticism/config-1.0.json \
  --task examples/pilot-runs/ru-mysticism/task.json \
  --workspace "$WORKSPACE" \
  --executable python3 \
  --arg tools/hwr_fixture_adapter.py \
  --arg=--fixture-dir \
  --arg "$PWD/examples/pilot-runs/ru-mysticism/stages" \
  --cwd "$PWD"
```

The replay is deterministic because it consumes reviewed stage records. The
archived result remains pinned to the draft revision that produced it; the
separate `config-1.0.json` proves that the same records can be replayed against
the stable profile without rewriting provenance. This is not evidence that the
live OpenAI provider will return identical prose.

## Visual production

The cover was generated with the built-in image-generation tool, then copied
into the repository and visually inspected against the approved media brief.
It contains no person, identifiable character, logo, text, real location, or
explicit supernatural entity. The source image remains in the generator's
default storage; the project-bound copy is the asset linked above.

The final visual record identifies it as an AI-generated conceptual editorial
illustration rather than documentary evidence.

## Result

The persisted execution reached:

```text
context-ready → media-decided → drafted → edited
→ visual produced → reviewed → ready
```

The final article contains 625 whitespace-delimited words. All eight selected
reviewers passed with no findings. The review preserves two limitations:

1. the article is an editorial interpretation, not an empirical statement
   about every reader;
2. the visual is generated and non-documentary.
