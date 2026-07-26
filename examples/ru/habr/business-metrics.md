# Example: RU Habr Business Metrics Article

## Task framing

- Language: Russian
- Content type: article
- Topic: business
- Platform: Habr
- Audience: product engineers reading company metric announcements
- Intent: show a reproducible method for checking whether two business metrics are comparable
- Author perspective: technical editorial
- Risk: medium
- Visual mode: none
- Sources: `rules/topic/business/foundation.md`, `rules/platform/habr/foundation.md`

## Resolved modules

`core.writing-pipeline` → `format.article.foundation` → `topic.business.foundation` → `platform.blog.foundation` → `platform.habr.foundation` → `language.ru.foundation` → source, human-signal, format, topic, platform, visual, and editor reviewers.

## Evidence map

- Verified repository rule: revenue, bookings, valuation, funding, profit, cash flow, and user metrics are not interchangeable.
- Verified repository rule: company metrics retain their definition and reporting period.
- Verified repository rule: Habr analysis exposes methodology, versions, tradeoffs, limitations, and commercial relationships when material.
- Editorial inference: a small comparison table is useful only after definitions and dates are aligned.

## Context gate

The example explains a verification procedure and does not report a real company's performance. No market, customer, or leadership claim is drafted. The source boundary is sufficient for a method article.

## Content design

- Reader promise: the reader leaves with a repeatable pre-comparison checklist.
- Working thesis: equal-looking numbers are not comparable until definitions, periods, and source conditions match.
- Structure: define the record → normalize fields → expose non-comparability → report the limitation.

## Final artifact

# Как сравнивать продуктовые метрики и не сравнить разные сущности

Два отчёта могут использовать одно слово — например, «пользователи» — и считать разных людей. Один показатель включает все зарегистрированные аккаунты, другой — активных за месяц, третий — организации. Сравнение начинается не с арифметики, а с определения.

Для каждого числа полезно сохранить минимальную запись: название метрики, точное определение, период, единицу, источник и условия доступа к данным. Если хотя бы одно поле неизвестно, это ограничение результата, а не мелкая сноска.

Тот же принцип действует для денежных показателей. Выручка не равна объёму заказов, прибыль — денежному потоку, инвестиционный раунд — оценке бизнеса. Складывать или ранжировать такие значения можно только после объяснения связи между ними.

Воспроизводимый разбор должен позволять другому читателю повторить решение: открыть те же документы, применить те же определения и увидеть, почему строки сопоставимы или почему сравнение остановлено.

Иногда корректный результат проверки — не рейтинг, а формулировка «данных недостаточно для сравнения». Для технической статьи это полноценный вывод: он показывает границу метода и не маскирует её уверенным графиком.

## Media decision

Decision: no visual. Без реального набора согласованных значений график создал бы вымышленные данные. Метод передаётся через явный набор полей.

## Source notes

- `rules/topic/business/foundation.md` supports metric definitions, periods, source hierarchy, comparison consistency, and commercial disclosure.
- `rules/platform/habr/foundation.md` supports reproducibility, method detail, and limitation handling.
- No real company, metric value, market position, or performance claim is used.

## Review result

- Reviewed revision: `ru-habr-business-metrics-r1`.
- Source, language, human-signals, format, topic, platform, visual, and editor reviewers: pass.
- Habr check: method, reproducibility, failure mode, and non-promotional framing are explicit.
- Open blocker or major findings: none.
- Readiness: publication-ready as a method explainer.
