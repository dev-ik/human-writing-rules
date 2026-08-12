# Example: RU Dzen Reader Promise Article

## Task framing

- Language: Russian
- Content type: article
- Topic: lifestyle
- Platform: Dzen
- Audience: authors preparing practical feed-discovered articles
- Intent: show how to keep a Dzen article useful after the reader opens it from a title and cover
- Author perspective: editorial
- Risk: low
- Visual mode: none
- Sources: `rules/topic/lifestyle/foundation.md`, `rules/platform/dzen/foundation.md`

## Resolved modules

`core.writing-pipeline` -> `format.article.foundation` -> `topic.lifestyle.foundation` -> `platform.blog.foundation` -> `platform.dzen.foundation` -> `language.ru.foundation` -> source, human-signal, format, topic, platform, and editor reviewers.

## Evidence map

- Verified repository rule: lifestyle content must not invent personal experience, product use, health effects, prices, or endorsements.
- Verified repository rule: a recommendation needs a clear basis and must separate preference from supported claim.
- Verified repository rule: Dzen articles rely on a feed promise carried by title, cover, first screen, and early paragraphs.
- Verified repository rule: Dzen-specific platform assumptions that affect title, cover, length, monetization, moderation, or editing must be recorded in the audit output.
- Editorial inference: a reader who arrives from a recommendation card should see the promised practical value before the article expands into context.

## Context gate

The example explains an editorial method and does not recommend a real product, routine, diet, medicine, destination, financial choice, or personal practice. No first-person claim or current platform metric is drafted. The source boundary is sufficient for a low-risk method article.

## Content design

- Reader promise: the reader can check whether a feed headline still matches the article body.
- Working thesis: a Dzen article should earn the click and then immediately honor it.
- Structure: name the promise -> answer early -> build the useful middle -> keep the channel promise visible -> audit platform assumptions.

## Final artifact

# Заголовок обещает, текст отвечает

В рекомендательной ленте читатель сначала видит не статью, а обещание: заголовок, обложку и пару строк контекста. Если внутри открывается другой материал, доверие теряется быстрее, чем растёт охват.

Проверка начинается с простого вопроса: что человек ожидает узнать после клика? Ответ должен появиться в начале, а не после длинной раскачки. Если заголовок обещает три ошибки, первые абзацы должны показать, о каких ошибках речь и почему они важны.

Дальше статье нужен не шум, а опора. Практический пример, ограничение метода, список условий, короткий вывод после каждого блока. Так текст остаётся полезным даже для читателя, который пришёл из ленты без знания канала.

Обложка работает так же. Она может усилить тему, но не должна добавлять факты, которых нет в тексте. Фото, схема или иллюстрация должны помогать распознать материал, а не обещать чужой опыт, результат или доказательство.

Перед публикацией полезно отдельно записать платформенные допущения: длина заголовка, теги, обложка, возможная модерация, редактирование после выхода. Это не часть публичного текста, но это часть ответственной подготовки.

Хорошая статья для Дзена не просто получает открытие. Она быстро подтверждает, что читатель открыл именно то, что ему обещали.

## Media decision

Decision: no visual. The example discusses a publication method and does not need a cover image; a generated cover would only demonstrate generic feed packaging without adding evidence.

## Source notes

- `rules/topic/lifestyle/foundation.md` supports bounded recommendations, preference/claim separation, and avoidance of invented personal experience.
- `rules/platform/dzen/foundation.md` supports feed promise, continuation, title/cover integrity, editor constraints, and audit notes for platform assumptions.
- No external Dzen metric, monetization condition, title-length limit, traffic claim, or moderation outcome is used.

## Review result

- Reviewed revision: `ru-dzen-reader-promise-r1`.
- Source, language, human-signals, format, topic, platform, and editor reviewers: pass.
- Dzen check: title, cover, first screen, continuation, channel promise, and platform-assumption audit are addressed without traffic or monetization claims.
- Open blocker or major findings: none.
- Readiness: publication-ready as a method explainer.
