# Example: RU Generic Social Education Explainer

## Task framing

- Language: Russian
- Content type: social-post
- Topic: education
- Platform: generic social
- Audience: authors of short educational posts
- Intent: distinguish exposure to a concept from an observable learning result
- Author perspective: editorial
- Risk: medium
- Visual mode: none
- Sources: `rules/topic/education/foundation.md`, `rules/platform/social/foundation.md`

## Resolved modules

`core.writing-pipeline` → `format.social-post.foundation` → `topic.education.foundation` → `platform.social.foundation` → `language.ru.foundation` → source, human-signal, format, topic, platform, and editor reviewers.

## Evidence map

- Verified repository rule: an education artifact defines learner, prerequisite, objective, and observable result.
- Verified repository rule: concepts are sequenced by dependency.
- Verified repository rule: exposure or completion does not guarantee mastery.
- Editorial inference: one verification task is more useful than a broad promise to understand everything.

## Context gate

The post makes no claim about a real course, learner population, teaching intervention, or measured outcome. It demonstrates objective design from the local education module.

## Content design

- Learner: beginning author of educational content.
- Prerequisite: ability to state a topic.
- Objective: rewrite a vague learning promise as an observable action.
- Verification: the reader can identify the action and its success condition.

## Final artifact

«После поста читатель разберётся в теме» — обещание, которое невозможно проверить.

Попробуйте заменить его наблюдаемым результатом:

1. Назовите, для кого материал.
2. Укажите необходимое предварительное знание.
3. Сформулируйте действие: сравнить, объяснить, рассчитать или исправить.
4. Добавьте короткую проверку результата.

Например, не «понять причинность», а «увидеть, где автор делает причинный вывод только из совпадения».

Один пост не обещает мастерство. Он может честно дать один инструмент и способ убедиться, что инструмент понят.

## Media decision

Decision: no visual. Последовательность из четырёх действий читается без схемы; изображение конкурировало бы с учебной задачей.

## Source notes

- `rules/topic/education/foundation.md` supports learner, prerequisite, objective, verification, sequencing, and non-mastery claims.
- `rules/platform/social/foundation.md` supports standalone context and compact structure.
- The example sentence is explicitly illustrative, not a reported learning result.

## Review result

- Reviewed revision: `ru-social-education-explainer-r1`.
- Source, language, human-signals, format, topic, platform, and editor reviewers: pass.
- Education check: learner, prerequisite, observable action, and verification are present.
- Open blocker or major findings: none.
- Readiness: publication-ready.
