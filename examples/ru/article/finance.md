# Example: RU Finance Claims Article

## Task framing

- Language: Russian
- Content type: article
- Topic: finance
- Platform: generic blog
- Audience: editors checking financial comparisons
- Intent: explain why every financial number needs date, unit, jurisdiction, and calculation method
- Author perspective: neutral editorial
- Risk: high
- Visual mode: none
- Sources: `rules/topic/finance/foundation.md`, `rules/sources/source-integrity.md`

## Resolved modules

`core.writing-pipeline` → `format.article.foundation` → `topic.finance.foundation` → `platform.blog.foundation` → `language.ru.foundation` → source, human-signal, format, topic, platform, and editor reviewers.

## Evidence map

- Verified repository rule: price, rate, valuation, rule, and market condition retain a date.
- Verified repository rule: currency, units, timezone, market, jurisdiction, and calculation method remain visible.
- Verified repository rule: historical facts, current observations, forecasts, scenarios, and opinions are separate.
- Verified repository rule: derived values are recalculated and estimates are labelled.

## Context gate

The article teaches record structure and contains no current price, rate, tax rule, investment recommendation, or forecast. It cannot be used to make a financial decision without external data, and it says so directly.

## Content design

- Reader promise: the reader can reject an under-specified financial number before publication.
- Working thesis: a number without its measurement frame is not yet a usable financial claim.
- Structure: freeze the value → expose the frame → separate time layers → verify calculations.

## Final artifact

# Финансовому числу нужен адрес

Число само по себе не сообщает, что именно измерено. «Ставка выросла», «актив подорожал», «компания стоит дороже» — каждая фраза требует даты, единицы и источника, а часто ещё рынка, часового пояса и юрисдикции.

Следующий слой — метод. Процент может означать изменение цены, доходность за период или долю от другой величины. Полученное редакцией значение нужно пересчитать, а допущения — оставить рядом с выводом.

Не менее важно разделить время. Исторический результат не становится прогнозом автоматически. Текущая котировка не описывает будущий диапазон. Сценарий остаётся сценарием, даже если основан на правдоподобных предпосылках.

Перед публикацией полезно проверить конфликт интересов: позицию автора, рекламную связь, реферальную модель или иной стимул. Отсутствие такого раскрытия может изменить смысл рекомендации сильнее, чем ещё один знак после запятой.

Этот метод не отвечает, что покупать или продавать. Он отвечает на более ранний редакционный вопрос: достаточно ли определено утверждение, чтобы читатель понял его границы.

## Media decision

Decision: no visual. График без проверенного набора данных, единиц, периода и масштаба был бы вымышленным доказательством.

## Source notes

- `rules/topic/finance/foundation.md` supports dating, units, jurisdiction, calculation, scenarios, downside cases, and conflict disclosure.
- `rules/sources/source-integrity.md` supports source and uncertainty handling.
- No personalized financial, legal, tax, credit, insurance, or investment advice is included.

## Review result

- Reviewed revision: `ru-finance-claims-article-r1`.
- Source, language, human-signals, format, topic, platform, and editor reviewers: pass.
- High-risk check: no current market data, forecast, transaction instruction, or personalized advice.
- Open blocker or major findings: none.
- Readiness: publication-ready as editorial methodology.
