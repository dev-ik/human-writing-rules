# Example: RU Technology Article

## Task framing

- Content type: `article`
- Topic: `technology`
- Platform: `blog`
- Skill: `opensource`
- Audience: developers designing AI writing workflows
- Intent: explain why the repository uses modular rules
- Perspective: project editorial team
- Visual mode: `auto`
- Sources: `README.md`, `core/content-model.md`, `core/context-selection.md`, `registry/objects.json`, `ROADMAP.md`

## Resolved modules

`core.writing-pipeline` → `format.article.foundation` → `topic.technology.foundation` → `platform.blog.foundation` → `language.ru.foundation` → `skill.opensource` → source, human-signal, format, topic, platform, visual, and editor reviewers.

## Evidence map

- Verified fact: runtime guidance is represented as stable objects with paths and `requires` relationships.
- Verified fact: the content model separates format, topic, platform, skill, tone, perspective, and visual mode.
- Verified fact: the context-selection rule instructs agents to load the smallest sufficient module set.
- Limitation: the repository includes stable specification contracts and reference tooling, but does not claim that every writing engine conforms or that the process improves every text.
- Inference used in the article: separating axes makes conflicts easier to inspect. This is presented as a design rationale, not measured performance.

## Context gate

Result: `pass`.

The source set identifies the repository's current registered objects and documented behavior. Specification stability, reference-tooling scope, and implementation conformance remain distinct. No benchmark or production-performance claim is needed for the article's thesis.

## Content design

- Primary job: architecture explainer.
- Reader promise: after reading, a developer will understand why format, topic, platform, skill, tone, and perspective resolve independently and how visuals fit that model.
- Working thesis: explicit module boundaries make editorial decisions and conflicts inspectable.
- Section path: failure of one large prompt → independent axes → registry resolution → visual decision → current limitations.

## Final artifact

# Почему правила для AI-текстов лучше разделять на модули

Когда все требования к тексту складывают в один большой промпт, разные решения начинают выглядеть как одно. Формат статьи смешивается с правилами площадки, экспертный тон — с правом говорить от первого лица, а требования к научным источникам — с общей просьбой «писать убедительно».

Human Writing Rules предлагает другую модель: разделять такие решения и загружать только те правила, которые относятся к задаче.

## Один материал — несколько независимых выборов

Статья о научной работе для корпоративного блога может иметь формат `article`, тему `science`, платформу `blog` и задачу `news`. Если ту же работу нужно представить в Telegram, меняются формат и площадка, но не стандарт доказательств для научного утверждения.

Это различие важно не из-за красоты классификации. Оно позволяет увидеть, какое правило отвечает за конкретное решение и почему оно оказалось в контексте агента.

## Реестр вместо скрытой сборки

Модули имеют стабильные идентификаторы, пути и зависимости. Агент начинает с обязательного pipeline, добавляет языковой модуль, правила источников и human signals, а затем подключает выбранные формат, тему, площадку, задачу, тон и рецензентов.

Если выбран Telegram, специфический модуль наследует общие правила социальных платформ. Habr и Setka аналогично наследуют основу для блогов. Неизвестная тема может использовать общий тематический модуль, пока для неё не появятся отдельные проверенные правила.

## Иллюстрация — тоже редакционное решение

Изображение не должно появляться только потому, что в шаблоне есть место под обложку. Сначала определяется его функция: объяснить механизм, обозначить тему, показать проверенные данные или помочь с навигацией.

Для выбранной иллюстрации фиксируются фактические границы, формат, композиция, ограничения, alt-текст и требования к раскрытию происхождения. Сгенерированное изображение нельзя выдавать за фотографию события, интерфейс реального продукта или доказательство.

## Что эта архитектура пока не решает

Репозиторий описывает спецификацию, схемы, реестры, примеры и проверки целостности. Он не является универсальным раннером и сам по себе не доказывает, что модульный подход улучшает любой текст.

Практическую ценность такой системы нужно проверять на воспроизводимых примерах: сохранять исходный brief, источники, версии модели, результаты рецензирования и человеческие оценки.

## Media decision

Decision: no generated visual. The content model table and dependency example already explain the relationship more accurately than a decorative cover would.

## Source notes

All factual statements map to the listed repository files. The claimed benefit is explicitly framed as design rationale or a proposition to be evaluated.

## Review result

- Reviewed revision: `ru-technology-article-example-r2`.
- Resolved major finding: an earlier wording implied measured quality improvement; the final article limits the benefit to design rationale requiring future benchmark evidence.
- Source: repository capability and future evaluation remain distinct.
- Topic: implementation, specification, and inference are separated.
- Format: each section advances the central question.
- Visual: `auto` correctly resulted in no generated asset.
- Readiness: no blocker or major finding remains.
