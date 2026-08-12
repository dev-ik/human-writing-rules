# Examples

Examples demonstrate the complete editorial contract, not a universal writing template.

Each full example contains:

1. task framing;
2. resolved modules;
3. evidence map or source boundary;
4. publication-ready artifact;
5. media decision and visual handoff when applicable;
6. source notes;
7. reviewer findings and revision result.

An example may use the repository itself as the source set so every claim remains locally verifiable. Topic examples are intentionally about editorial practice; they demonstrate domain handling without inventing an external paper, product, film, event, or quotation.

Do not copy an example's structure into an unrelated task. Load only the format, topic, platform, skill, tone, and reviewer modules selected for the new brief.

## Reviewed example catalog

[`reviewed-examples.json`](reviewed-examples.json) is the machine-readable
inventory. It pins every example by revision and SHA-256, records its language,
format, topic, platform, visual decision, reviewers, and limitations, and
requires all sections listed above.

Coverage means:

- every registered topic has at least one reviewed example;
- every registered platform has at least one reviewed example;
- the full topic × platform cross-product is not required;
- `visuals.mode: auto` requires a visual reviewer even when the justified
  decision is `none`;
- a selected visual brief is recorded separately from a produced asset.

`status: reviewed` means the checked-in artifact passed the declared project
review contract with no unresolved blocker or major finding. It does not claim
external review, inter-rater agreement, or measured publishing quality.

Run:

```sh
npm run check:reviewed-examples
npm run test:reviewed-examples
```

The validator checks registry references, safe paths, bounded UTF-8 reads,
SHA-256, section order, task metadata, resolved modules, reviewed revision,
readiness, visual decision consistency, reviewers, uncataloged files, and
topic/platform coverage.

## Topic coverage

| Topic | Reviewed example |
| --- | --- |
| General | [Mixed-topic escalation](ru/article/general.md) |
| Science | [Study evidence boundary](ru/article/science.md) |
| Technology | [Modular writing architecture](ru/article/technology.md) |
| Entertainment | [Accountable review method](ru/article/entertainment.md) |
| Business | [Comparable business metrics for Habr](ru/habr/business-metrics.md) |
| Health | [Pre-draft health evidence gate](ru/article/health.md) |
| Finance | [Financial claim measurement frame](ru/article/finance.md) |
| Culture | [Context and interpretation for Setka](ru/setka/culture-context.md) |
| Lifestyle | [Bounded recommendation post](ru/social/lifestyle-recommendation.md) |
| Education | [Observable learning objective](ru/social/education-explainer.md) |
| Travel | [Dated travel-planning assumptions](ru/article/travel.md) |

Health and finance examples are editorial-method artifacts. They deliberately
contain no diagnosis, treatment, emergency direction, current price, market
forecast, transaction instruction, or personalized advice.

## Platform coverage

| Platform | Representative reviewed example |
| --- | --- |
| Blog | [General article](ru/article/general.md) |
| Generic social | [Education explainer](ru/social/education-explainer.md) |
| Telegram | [Science explainer](ru/telegram/science-explainer.md) |
| LinkedIn | [English open-source announcement](en/linkedin/opensource.md) |
| Habr | [Business metric method](ru/habr/business-metrics.md) |
| Dzen | [Reader promise method](ru/dzen/reader-promise.md) |
| Setka | [Culture context article](ru/setka/culture-context.md) |

## Add a reviewed example

1. Resolve the language, format, topic, platform, perspective, risk, sources,
   and visual mode before drafting.
2. Include every required section in the canonical order.
3. Keep the final artifact separate from source notes and review output.
4. Record the reviewed revision, readiness, reviewers, limitations, and media
   decision.
5. Add the file and its SHA-256 to `reviewed-examples.json`.
6. Run `npm run check:reviewed-examples` and the full `npm run check`.

The [`source-snapshots/`](source-snapshots/README.md) fixture demonstrates how
an exact local source is hashed, attached to a task, validated, and included in
an adapter packet without network retrieval.
