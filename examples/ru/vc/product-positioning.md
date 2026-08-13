# Example: RU vc.ru Product Positioning Article

## Task framing

- Language: Russian
- Content type: article
- Topic: business
- Platform: vc
- Audience: основатели и продуктовые команды, которые готовят публичный кейс
- Intent: показать, как отделить продуктовый кейс от рекламного обещания
- Author perspective: editorial
- Risk: medium
- Visual mode: none
- Sources: `rules/platform/vc/foundation.md`, `rules/topic/business/foundation.md`

## Resolved modules

`core.writing-pipeline` -> `format.article.foundation` -> `topic.business.foundation` -> `platform.blog.foundation` -> `platform.vc.foundation` -> `language.ru.foundation` -> source, human-signal, format, topic, platform, and editor reviewers.

## Evidence map

- Verified repository rule: vc.ru framing must distinguish case study, opinion, announcement, guide, and news.
- Verified repository rule: business claims require definitions, period, geography, source, and exclusions.
- Verified repository rule: commercial interest, sponsorship, investor interest, and client relationships must stay visible.
- Editorial inference: a product case can explain method without claiming real growth.

## Context gate

Пример описывает редакционный метод и не сообщает реальные метрики компании, рынок, выручку, инвестиции или пользовательский рост. Источников достаточно для безопасного методического материала.

## Content design

- Reader promise: читатель увидит, где заканчивается кейс и начинается рекламное обещание.
- Working thesis: публичный продуктовый кейс держится на границах данных, а не на уверенном тоне.
- Structure: frame -> evidence fields -> disclosure -> usable conclusion.

## Final artifact

# Как написать продуктовый кейс и не превратить его в рекламный плакат

Продуктовый кейс начинается не с красивого результата, а с рамки: что именно произошло, с кем, за какой период и по каким данным это проверяется.

Если текст говорит «конверсия выросла», читателю нужны минимум четыре поля: определение конверсии, период сравнения, исходная база и источник данных. Без этого фраза звучит сильнее, чем доказательство за ней.

Коммерческий интерес тоже не сноска для финала. Если материал пишет команда продукта, подрядчик, инвестор или партнер, это влияет на то, как читатель оценивает выводы. Раскрытие позиции не портит кейс; оно делает его честнее.

Не каждый кейс обязан доказывать рынок. Иногда достаточно показать решение одной задачи: как команда нашла проблему, какие варианты отбросила, что сработало в этом контексте и где метод может не повториться.

Сильный вывод для vc.ru — не «делайте так же». Сильный вывод: «вот условия, при которых этот подход был осмысленным, и вот что нужно проверить перед повторением».

## Media decision

Decision: no visual. Без реальных согласованных метрик график создал бы вымышленное доказательство.

## Source notes

- `rules/platform/vc/foundation.md` supports case framing, disclosure, metric boundaries, and proportional product mentions.
- `rules/topic/business/foundation.md` supports metric definitions, periods, source hierarchy, and comparison limits.
- No real company, client, investor, market, revenue, or growth claim is used.

## Review result

- Reviewed revision: `ru-vc-product-positioning-r1`.
- Source, language, human-signals, format, topic, platform, and editor reviewers: pass.
- vc.ru check: case frame, disclosure, metric boundary, and non-promotional conclusion are explicit.
- Open blocker or major findings: none.
- Readiness: publication-ready as a business method article.
