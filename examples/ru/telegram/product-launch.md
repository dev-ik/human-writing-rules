# Example: RU Telegram Product Launch

## Task framing

- Content type: `social-post`
- Topic: `technology`
- Platform: `telegram`
- Skill: `product-launch`
- Audience: authors and developers working with AI agents
- Intent: announce the repository foundation without implying proven adoption or production maturity
- Perspective: project team
- Visual mode: `none`
- Sources: `README.md`, `VISION.md`, `ROADMAP.md`, `registry/objects.json`

## Resolved modules

`core.writing-pipeline` → `format.social-post.foundation` → `topic.technology.foundation` → `platform.social.foundation` → `platform.telegram.foundation` → `language.ru.foundation` → `skill.product-launch` → source, human-signal, format, topic, platform, task, and editor reviewers.

## Evidence map

- Verified locally: the repository defines a modular editorial pipeline, RU and EN foundations, registries, topic and platform modules, reviewers, examples, and a starter kit.
- Limitation: the specification is stable, while the bundled runner remains reference tooling rather than a universal conforming writing engine.
- Unknown and therefore omitted: adoption, user count, measured quality improvement, and external community response.

## Context gate

Result: `pass`.

The source set supports the repository scope and implementation limitation. The task does
not require unavailable adoption or performance evidence, the project-team
perspective is authorized, and the post can stand alone without a visual.

## Content design

- Communication goal: announce the available repository foundation without overstating maturity.
- Reader promise: after reading, authors and developers know what the repository contains and what it does not yet provide.
- Primary claim: the first modular specification foundation is available.
- Context floor: stable specification status and absence of a universal conformance claim.
- Ending: a real documentation entry point rather than an engagement request.

## Final artifact

Собрали основу Human Writing Rules — открытой спецификации для работы AI-агентов с текстами.

Вместо одного большого промпта здесь отдельные модули: редакционный pipeline, правила источников, русский и английский языки, форматы статей и постов, площадки, тематические playbook-правила и независимые рецензенты.

Агент получает задачу, загружает только нужные модули, составляет карту доказательств, пишет черновик и исправляет конкретные замечания. Иллюстрация тоже не появляется автоматически: сначала нужно определить её пользу, фактические границы и формат.

Спецификация стабилизирована, но встроенный раннер остаётся эталонным инструментом, а не универсальным движком с доказанной полной conformance. Текущая версия позволяет воспроизводимо проверять архитектуру, примеры и критерии качества.

Начать можно с `README.md` и starter kit.

## Media decision

Decision: no visual.

The announcement is about repository structure rather than a visible product
interface. A generated product screen or adoption image would imply unsupported
capability or use. The post remains clear without decorative media.

## Source notes

Capability statements map to the selected local files. Adoption, user response,
production maturity, and measured quality improvement remain unknown and are
omitted.

## Review result

- Reviewed revision: `ru-telegram-product-launch-r2`.
- Source: no unsupported adoption or quality claim.
- Language: native Russian phrasing; no translated launch clichés.
- Human signals: no fabricated excitement, demand, or user reaction.
- Platform: one idea, readable paragraphs, no forced question or CTA.
- Visual: omission avoids unsupported interface and adoption implications.
- Readiness: no blocker or major finding remains.
