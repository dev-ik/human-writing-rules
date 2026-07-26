# Example: RU LinkedIn Technology Explainer

## Task framing

- Content type: `social-post`
- Topic: `technology`
- Platform: `linkedin`
- Skill: none
- Audience: developers and editorial-tool builders
- Intent: explain why a social post is a separate production artifact rather than a truncated article
- Perspective: project editorial team
- Artifact form: standalone explainer
- Visual mode: `auto`
- Sources: `guides/social-post-production.md`, `rules/format/social-post/foundation.md`, `core/content-model.md`

## Resolved modules

`core.writing-pipeline` → `format.social-post.foundation` → `topic.technology.foundation` → `platform.social.foundation` → `platform.linkedin.foundation` → `language.ru.foundation` → source, human-signal, format, topic, platform, visual, and editor reviewers.

## Evidence map

- Verified repository fact: the content model treats format, topic, platform, skill, tone, author perspective, and visual mode as separate axes.
- Verified repository rule: adapting an article means selecting one useful idea and preserving its evidence boundary.
- Verified repository rule: a post is reviewed as a separate artifact because feed context, links, crop, and selected claims differ.
- Design rationale: explicit separation makes adaptation decisions easier to inspect. This is not presented as measured performance improvement.
- Limitation: the stable specification and bundled reference tooling do not prove universal implementation conformance or publishing quality.

## Context gate

Result: `pass`.

The local files support the described architecture and limitation. The post
does not claim adoption, production maturity, or measured content improvement.
The project-team perspective is authorized by the task.

## Content design

- Communication goal: explain one architectural distinction.
- Reader promise: after reading, a developer understands why article-to-post adaptation needs a new claim and review pass.
- Primary claim: a social post is a new artifact with its own context boundary.
- Context floor: this is a stable design contract, not benchmark proof or a universal engine-conformance claim.
- Ending: bounded design consequence, no engagement request.

## Final artifact

Короткий пост — не статья, из которой удалили всё, что не поместилось.

При адаптации меняется не только длина. Текст попадает в ленту, может быть показан без ссылки, переслан отдельно от исходного материала или обрезан превью. Из-за этого у поста появляется собственная граница контекста.

В Human Writing Rules такая адаптация проходит как отдельная задача:

- выбирается одна полезная мысль из финальной версии статьи;
- сохраняются источник и главное ограничение;
- заново проверяются площадка, ссылка, первый экран и медиа;
- пост получает собственный review.

Если мысль нельзя сократить без потери важной оговорки, нужен тред, серия или исходная статья — а не более уверенная формулировка.

Это стабильный контракт процесса, а не доказательство того, что такой подход улучшает любой текст или что любой подключённый движок ему соответствует. Но он делает решение о сокращении явным и проверяемым.

## Media decision

Decision: no generated visual.

The post explains one process distinction completely in text. A generic
workflow cover would add decoration, while a detailed diagram would introduce
more components than the post needs. `Auto` therefore results in `none`.

## Source notes

All repository capability and process statements map to the listed local files.
The claimed inspectability benefit is labeled design rationale, not benchmark
evidence.

## Review result

- Reviewed revision: `ru-linkedin-technology-explainer-r2`.
- Resolved major finding: the first draft implied proven quality improvement; the final text limits the claim to explicit, inspectable process design.
- Source: specification stability, implementation conformance, and evidence boundaries remain distinct.
- Technology: specification, implementation, and measured result remain distinct.
- Platform: professional relevance is explicit without fabricated personal experience or engagement bait.
- Visual: `auto → none` has a documented reader-benefit decision.
- Readiness: no blocker or major finding remains.
