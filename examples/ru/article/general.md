# Example: RU General Article

## Task framing

- Language: Russian
- Content type: article
- Topic: general
- Platform: generic blog
- Audience: editors working with mixed-topic briefs
- Intent: explain when the general topic module is sufficient and when to escalate
- Author perspective: editorial
- Risk: low until a specialist domain becomes material
- Visual mode: none
- Sources: `rules/topic/general/foundation.md`, `rules/sources/source-integrity.md`

## Resolved modules

`core.writing-pipeline` → `format.article.foundation` → `topic.general.foundation` → `platform.blog.foundation` → `language.ru.foundation` → source, human-signal, format, topic, platform, and editor reviewers.

## Evidence map

- Verified repository rule: the general module separates factual, evaluative, experiential, and predictive claims.
- Verified repository rule: time- or place-sensitive facts retain their date and scope.
- Verified repository rule: a material health, finance, legal, safety, or scientific question triggers a specialist module.
- Editorial inference: the boundary of a mixed-topic text is more useful than an exhaustive list of loosely related facts.

## Context gate

The sources define the general module and its escalation boundary. The example makes no external or current factual claim. No specialist question is material to the thesis, so the general topic module is sufficient.

## Content design

- Reader promise: the reader can decide whether a mixed brief remains general or needs specialist handling.
- Working thesis: `general` is a routing decision, not permission to lower the evidence standard.
- Structure: define the boundary → classify claims → test escalation.

## Final artifact

# «Общая тема» — это не тема без правил

Смешанный материал часто начинается без удобной рубрики: немного продукта, немного поведения пользователей, немного прогноза. В такой ситуации модуль `general` нужен не для того, чтобы отменить предметную проверку, а чтобы сначала разделить типы утверждений.

Факт отвечает на вопрос, что известно и откуда. Оценка показывает критерий автора. Личный опыт допустим только при наличии реального опыта. Прогноз остаётся сценарием, даже если звучит правдоподобно. Пока эти слои различимы, текст можно собирать без ложной уверенности.

Следующий тест — дата и область действия. Цена, правило, доступность или состояние сервиса могут меняться. Такой факт нельзя оставлять без времени и контекста только потому, что весь материал формально относится к общей теме.

Наконец, `general` должен уметь уступить место. Если вывод начинает влиять на лечение, деньги, безопасность, правовой статус или трактовку исследования, нужен соответствующий предметный модуль. Это не усложнение процесса, а признание того, что цена ошибки изменилась.

Поэтому хорошая граница звучит не как «обо всём понемногу», а как «вот какие вопросы мы решаем и какие вопросы требуют другого уровня проверки».

## Media decision

Decision: no visual. Классификация утверждений изложена непосредственно в тексте; декоративная схема не добавила бы читателю нового способа проверки.

## Source notes

- `rules/topic/general/foundation.md` supports claim classification, dating, scope, and specialist escalation.
- `rules/sources/source-integrity.md` supports the evidence boundary.
- No external facts, quotations, statistics, or personal experience are used.

## Review result

- Reviewed revision: `ru-general-article-r1`.
- Source, language, human-signals, format, topic, platform, and editor reviewers: pass.
- Open blocker or major findings: none.
- Readiness: publication-ready within the stated repository-rule scope.
