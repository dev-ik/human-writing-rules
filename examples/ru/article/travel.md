# Example: RU Travel Planning Article

## Task framing

- Language: Russian
- Content type: article
- Topic: travel
- Platform: generic blog
- Audience: editors preparing practical destination guides
- Intent: show which assumptions and current facts must be pinned before drafting
- Author perspective: neutral editorial
- Risk: medium
- Visual mode: none
- Sources: `rules/topic/travel/foundation.md`, `rules/sources/source-integrity.md`

## Resolved modules

`core.writing-pipeline` → `format.article.foundation` → `topic.travel.foundation` → `platform.blog.foundation` → `language.ru.foundation` → source, human-signal, format, topic, platform, and editor reviewers.

## Evidence map

- Verified repository rule: entry rules, transport, closures, safety notices, accessibility, seasonal conditions, and opening times require current authoritative sources.
- Verified repository rule: prices and availability retain dates.
- Verified repository rule: origin, timing, mobility, budget, and other material assumptions remain visible.
- Verified repository rule: firsthand experience is separate from retrieved information.

## Context gate

The article gives no destination-specific instruction, price, timetable, entry rule, closure, or safety assessment. It explains what a real travel brief must contain before current research begins.

## Content design

- Reader promise: the reader can detect when a travel guide is too under-specified to draft safely.
- Working thesis: itinerary advice is conditional on traveller context and dated local information.
- Structure: freeze the traveller → freeze the date → verify changeable facts → preserve source boundaries.

## Final artifact

# Маршрут начинается не с списка мест

Практический путеводитель меняется вместе с путешественником. Точка отправления влияет на правила въезда, сезон — на транспорт и доступ, мобильность — на саму возможность пройти маршрут, а бюджет — на смысл слова «доступно».

Поэтому сначала фиксируется контекст: откуда едет человек, когда, на какой срок, с каким бюджетом и ограничениями. Без этих данных универсальный маршрут легко становится неприменимым.

Затем проверяются изменяемые факты. Расписание, закрытие, цена, доступность, предупреждение и часы работы требуют даты и прямого источника. Старая ссылка не становится актуальной только потому, что страница всё ещё открывается.

Личный опыт нужно подписывать как личный опыт. Он может объяснить впечатление или практическую деталь, но не подтверждает текущие правила и не позволяет объявить место безопасным, дешёвым или «неизведанным» для всех.

Если часть условий неизвестна, это должно изменить текст: ограничить маршрут, предложить проверку перед поездкой или остановить публикацию конкретного совета. Неопределённость здесь — часть полезной информации.

## Media decision

Decision: no visual. Карта или фотография без выбранного места, проверенного доступа и актуальных условий создала бы ложное впечатление конкретного маршрута.

## Source notes

- `rules/topic/travel/foundation.md` supports freshness, traveller assumptions, source boundaries, accessibility, pricing, and community care.
- `rules/sources/source-integrity.md` supports authoritative sourcing and uncertainty.
- No current travel condition, destination claim, personal trip, price, or safety advice is included.

## Review result

- Reviewed revision: `ru-travel-planning-article-r1`.
- Source, language, human-signals, format, topic, platform, and editor reviewers: pass.
- Travel check: current destination facts are deliberately absent; assumptions and stop conditions are explicit.
- Open blocker or major findings: none.
- Readiness: publication-ready as an editorial-method article.
