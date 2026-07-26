# Example: RU Science Article

This example explains how to write about a study. It does not describe a real study and introduces no external scientific claims.

## Task framing

- Content type: `article`
- Topic: `science`
- Platform: `blog`
- Skill: none
- Audience: general readers
- Intent: explain how to preserve a study's evidence boundary
- Perspective: editorial
- Visual mode: `auto`
- Sources: `rules/topic/science/foundation.md`, `rules/sources/source-integrity.md`

## Resolved modules

`core.writing-pipeline` → `format.article.foundation` → `topic.science.foundation` → `platform.blog.foundation` → `language.ru.foundation` → source, human-signal, format, topic, platform, visual, and editor reviewers.

## Evidence map

- Verified repository rule: a scientific article records publication status, population or material, method, comparison, outcome, timeframe, and limitations.
- Verified repository rule: association, prediction, mechanism, and causation remain distinct.
- Verified repository rule: press releases and interviews are attributed interpretation rather than substitutes for the research.
- Editorial inference: a compact pre-draft record makes accidental claim strengthening easier to notice. The article presents this as useful practice, not a measured performance result.
- Unknown: whether the method improves accuracy in a particular newsroom. The artifact makes no such claim.

## Context gate

Result: `pass`.

The example is about the repository's editorial method, not a real study. The selected local sources support every prescriptive statement, no external scientific result is implied, the editorial perspective is legitimate, and the visual can remain conceptual.

## Content design

- Primary job: explainer.
- Reader promise: after reading, a beginning writer will know which study boundaries to record and why limitations belong near the reported result.
- Working thesis: clear scientific writing narrows a source claim to its real evidence boundary instead of making it more dramatic.
- Section path: research object → claim boundary → uncertainty → precise translation.

## Final artifact

# Как писать о новом исследовании и не превращать результат в сенсацию

Новое исследование редко отвечает на большой вопрос целиком. Оно проверяет конкретную гипотезу на определённых данных, выбранным методом и в известных границах. Поэтому хорошая статья начинается не со слова «прорыв», а с точного ответа: что именно изучали?

## Сначала работа, потом её пересказ

Пресс-релиз или интервью помогают понять, почему авторы считают результат важным. Но это интерпретация. Для фактической основы нужны сама работа и доступные приложения: описание методов, выборки, измеряемых показателей и ограничений.

Редактору полезно отдельно записать:

- кто или что изучалось;
- с чем сравнивали результат;
- какой показатель измеряли;
- за какой период;
- что авторы обнаружили;
- чего выбранный метод установить не позволяет.

Такая запись становится границей будущей статьи. Если источник говорит о связи между двумя показателями, текст не должен незаметно превращать её в причинно-следственную связь.

## Значение результата зависит от масштаба

Одна работа может быть новой частью более широкой картины, предварительным сигналом или проверкой уже известного эффекта. Эти варианты требуют разной подачи. Формулировка «исследование показало» сама по себе недостаточна: читателю нужно понимать статус публикации, контекст и ограничения.

Неопределённость не стоит прятать в последний абзац. Если она меняет смысл результата, её нужно объяснить рядом с основным утверждением.

## Упрощать можно язык, но не вывод

Термин следует переводить на понятный язык только до тех пор, пока сохраняется исходное значение. Иногда точнее оставить специальное слово и коротко его объяснить, чем заменить его знакомым, но более сильным понятием.

Хороший научный текст не заставляет читателя выбирать между ясностью и аккуратностью. Он показывает, что известно, на чём это основано и где заканчивается уверенность.

## Media decision

Decision: create one explanatory visual because it makes the evidence path easier to inspect.

Brief:

- Purpose: show the path from an announcement to a bounded article claim.
- Content: four connected stages—press release, original paper, methods and limitations, article claim.
- Must not imply: that peer review guarantees truth or that every source set has the same hierarchy.
- Format: horizontal editorial diagram for a blog article.
- Text in image: avoid; add verified labels during layout.
- Caption: “A publication claim should become narrower, not stronger, as it moves through editorial verification.”
- Alt text: “Diagram showing a press release checked against the original paper, its methods and limitations, before a bounded claim is written.”

## Source notes

The artifact paraphrases only the selected repository rules. It does not cite or characterize a real paper.

## Review result

- Reviewed revision: `ru-science-article-example-r2`.
- Resolved minor finding: the first draft placed uncertainty only in the closing section; the revision moved it beside the result it constrains.
- Source: prescriptive statements remain bounded to the selected repository method.
- Topic: association, causation, publication status, methods, and limitations are distinguished.
- Visual: conceptual purpose and prohibited implication are explicit.
- Readiness: no blocker or major finding remains.
