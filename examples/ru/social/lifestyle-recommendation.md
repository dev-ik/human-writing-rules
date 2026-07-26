# Example: RU Generic Social Lifestyle Recommendation

## Task framing

- Language: Russian
- Content type: social-post
- Topic: lifestyle
- Platform: generic social
- Audience: authors preparing recommendation posts
- Intent: show how to bound a recommendation without inventing personal experience
- Author perspective: editorial
- Risk: low
- Visual mode: none
- Sources: `rules/topic/lifestyle/foundation.md`, `rules/platform/social/foundation.md`

## Resolved modules

`core.writing-pipeline` → `format.social-post.foundation` → `topic.lifestyle.foundation` → `platform.social.foundation` → `language.ru.foundation` → source, human-signal, format, topic, platform, and editor reviewers.

## Evidence map

- Verified repository rule: real experience, product claims, expert guidance, and general recommendations remain separate.
- Verified repository rule: the text identifies whom a recommendation may not suit.
- Verified repository rule: sponsorship, gifts, affiliate links, and access conditions are disclosed.
- Verified repository rule: universal routines and invented personal anecdotes are prohibited.

## Context gate

No product, health result, price, availability, or first-person experience is claimed. The post teaches a reusable editorial check, so repository rules are sufficient.

## Content design

- Reader promise: the reader can turn an absolute lifestyle tip into a bounded recommendation.
- Working thesis: usefulness comes from fit conditions, not universal confidence.
- Final artifact is intentionally short and independently reviewable.

## Final artifact

Перед публикацией совета проверьте четыре вещи:

- это ваш реальный опыт, заявление продукта, мнение специалиста или общая рекомендация;
- кому совет может не подойти;
- зависят ли цена, доступность, безопасность или совместимость от текущих данных;
— нужно ли раскрыть подарок, рекламу или партнёрскую ссылку.

Если ответ неизвестен, не заменяйте его историей «я попробовал и всё изменилось». Лучше сузить обещание: описать условия, ограничения и выбор, который остаётся за читателем.

Хорошая рекомендация не обязана подходить всем. Она должна позволять понять, подходит ли она конкретному человеку.

## Media decision

Decision: no visual. Пост является проверочным списком; декоративный before/after мог бы создать неподтверждённое обещание результата.

## Source notes

- `rules/topic/lifestyle/foundation.md` supports fit, freshness, experience, sponsorship, and transformation boundaries.
- `rules/platform/social/foundation.md` supports standalone feed context.
- No personal story, product result, endorsement, price, or affiliate relationship is asserted.

## Review result

- Reviewed revision: `ru-social-lifestyle-recommendation-r1`.
- Source, language, human-signals, format, topic, platform, and editor reviewers: pass.
- Open blocker or major findings: none.
- Readiness: publication-ready.
