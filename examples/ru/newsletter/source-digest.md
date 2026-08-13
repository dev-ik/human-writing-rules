# Example: RU Newsletter Source Digest

## Task framing

- Language: Russian
- Content type: article
- Topic: education
- Platform: newsletter
- Audience: подписчики, которые получают еженедельную подборку материалов
- Intent: показать, как отделить редакционный вывод от пересказа источников
- Author perspective: editorial
- Risk: medium
- Visual mode: none
- Sources: `rules/platform/newsletter/foundation.md`, `rules/topic/education/foundation.md`

## Resolved modules

`core.writing-pipeline` -> `format.article.foundation` -> `topic.education.foundation` -> `platform.blog.foundation` -> `platform.newsletter.foundation` -> `language.ru.foundation` -> source, human-signal, format, topic, platform, and editor reviewers.

## Evidence map

- Verified repository rule: newsletter subject, preview, body, links, and closing action are separate publication surfaces.
- Verified repository rule: digest issues must separate editorial judgment from summarized source claims.
- Verified repository rule: education content should preserve observable learning objective, learner context, evidence limits, and non-guaranteed outcomes.
- Editorial inference: a digest example can use placeholder source categories without inventing actual studies or links.

## Context gate

Пример показывает структуру выпуска и не ссылается на реальные исследования, курсы, авторов, цены или результаты обучения. Источников достаточно для методического материала.

## Content design

- Reader promise: подписчик понимает, что редакция выбрала, что известно из источников и чего выпуск не доказывает.
- Working thesis: хороший дайджест не смешивает пересказ, оценку и призыв.
- Structure: subject/preheader -> editorial note -> source blocks -> limitation -> closing action.

## Final artifact

# Тема: три материала о том, как формулировать учебную цель

Preview text: короткий выпуск о том, что должно быть видно до выбора формата урока.

В этом выпуске мы смотрим не на «лучший» формат обучения, а на более ранний вопрос: какую проверяемую задачу должен решить материал.

Первый источник полезен как рамка: цель должна описывать наблюдаемое действие, а не настроение ученика. «Понять тему» звучит удобно, но плохо проверяется. «Сравнить два подхода по заданным критериям» уже задает действие.

Второй материал напоминает про контекст. Одна и та же цель для новичка и практикующего специалиста требует разной глубины, примеров и темпа.

Третий блок — про границы результата. Даже хорошо сформулированная цель не доказывает, что обучение сработало. Для этого нужны данные о задании, группе, периоде и способе проверки.

Редакторский вывод выпуска простой: до выбора платформы, длительности и визуалов стоит записать одно предложение о действии читателя. Если действие нельзя увидеть, материал будет сложно проверить.

## Media decision

Decision: no visual. Выпуск объясняет редакционную структуру; изображение не добавляет проверяемой информации.

## Source notes

- `rules/platform/newsletter/foundation.md` supports subject, preview text, source blocks, forwarding context, and disclosure boundaries.
- `rules/topic/education/foundation.md` supports observable learning objectives, learner context, and non-guaranteed outcomes.
- No real study, course, author, provider, price, or measured learning outcome is used.

## Review result

- Reviewed revision: `ru-newsletter-source-digest-r1`.
- Source, language, human-signals, format, topic, platform, and editor reviewers: pass.
- Newsletter check: subject, preview, editorial judgment, source boundary, and closing action are explicit.
- Open blocker or major findings: none.
- Readiness: publication-ready as a newsletter method issue.
