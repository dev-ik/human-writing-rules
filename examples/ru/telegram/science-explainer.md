# Example: RU Telegram Science Explainer

This example explains an editorial method. It does not report a real study or
introduce external scientific claims.

## Task framing

- Content type: `social-post`
- Topic: `science`
- Platform: `telegram`
- Skill: none
- Audience: non-specialist readers who encounter research news in feeds
- Intent: show the minimum evidence boundary a short science post should retain
- Perspective: editorial
- Artifact form: standalone post
- Visual mode: `auto`
- Sources: `rules/format/social-post/foundation.md`, `rules/topic/science/foundation.md`, `rules/visual/illustration-integrity.md`

## Resolved modules

`core.writing-pipeline` → `format.social-post.foundation` → `topic.science.foundation` → `platform.social.foundation` → `platform.telegram.foundation` → `language.ru.foundation` → source, human-signal, format, topic, platform, visual, and editor reviewers.

## Evidence map

- Verified repository rule: a science post keeps the research object, publication status, population or material, method, measured outcome, and important limitation identifiable.
- Verified repository rule: one study, a body of evidence, and scientific consensus remain distinct.
- Verified repository rule: generated imagery cannot act as documentary or experimental evidence.
- Editorial inference: four compact questions can expose common evidence-boundary omissions before publication. The post presents this as a workflow, not as measured proof of accuracy improvement.
- Unknown: how the workflow affects a particular publication's error rate. The post makes no such claim.

## Context gate

Result: `pass`.

The post is about locally documented editorial rules. It makes no external
scientific claim, uses a legitimate editorial perspective, fits one dominant
idea, and can preserve its limitation without a linked article.

## Content design

- Communication goal: give the reader a compact pre-publication check.
- Reader promise: after reading, the audience can identify four evidence boundaries that a short research post should retain.
- Primary claim: short format reduces the claim budget, not the evidence threshold.
- Context floor: the checklist is editorial guidance and does not guarantee scientific accuracy.
- Ending: bounded conclusion without a CTA.

## Final artifact

Короткий пост об исследовании не обязан пересказывать всю работу. Но короткий формат не отменяет границы доказательств.

Перед публикацией полезно ответить на четыре вопроса:

1. Что именно изучали и на ком или на чём?
2. Что измеряли и с чем сравнивали?
3. Какой результат получили?
4. Чего этот метод установить не позволяет?

Если работа показывает связь между показателями, пост не должен незаметно превращать её в причинность. Если речь идёт об одной работе, нельзя повышать её статус до «наука доказала».

В коротком тексте лучше оставить один аккуратный вывод и главное ограничение, чем несколько эффектных утверждений без границ.

## Media decision

Decision: create one explanatory visual. The four-question check benefits from a
single view and remains useful when the post is forwarded.

Visual handoff:

- Purpose: explanatory checklist, not documentary evidence.
- Placement: attached to the post; the copy remains complete without it.
- Content: four connected neutral cards representing object, method and comparison, measured result, and limitation.
- Must not imply: a real paper, real dataset, universal scientific hierarchy, laboratory event, causal proof, or guaranteed accuracy.
- Format: landscape editorial diagram; final dimensions and crop verified in the publishing workflow.
- Text handling: generate without text; add the four verified labels manually during layout.
- Art direction: restrained editorial geometry, high contrast, generous spacing, no laboratory photography, logos, paper titles, charts, equations, or people.
- Generation prompt: “Conceptual editorial diagram with four connected blank cards representing research object, method and comparison, measured result, and limitation; restrained geometric composition, clear left-to-right hierarchy, high contrast, generous negative space, no text, no numbers, no charts, no laboratory, no people, no logos, no documentary photography.”
- Caption: “Короткий научный пост сохраняет объект, метод, результат и главное ограничение.”
- Alt text: “Четыре связанные карточки показывают путь от объекта и метода исследования к измеренному результату и его ограничению.”
- Disclosure: identify the asset as a generated conceptual illustration when the publishing context requires it.
- Fallback: omit the asset if labels, crop, contrast, or conceptual status cannot be verified.

## Source notes

All prescriptive content paraphrases the selected repository modules. No real
paper, dataset, scientist, experiment, result, or quotation is described.

## Review result

- Reviewed revision: `ru-telegram-science-explainer-r2`.
- Resolved major finding: an earlier sentence could be read as a universal guarantee; the final post frames the questions as an editorial check.
- Source: no external scientific claim or fabricated study.
- Topic: association, causation, single-study scope, and limitation remain distinct.
- Platform: the post survives forwarding and does not depend on a link.
- Visual: the asset is conceptual, optional, accessible, and bounded from documentary use.
- Readiness: no blocker or major finding remains.
