<p align="center">
  <img src="assets/human-writing-rules-mark.svg" width="112" height="112" alt="Знак Human Writing Rules: три узла источников соединяются в единый редакционный путь">
</p>

<h1 align="center">Human Writing Rules</h1>

<p align="center">
  Вендорно-нейтральный редакционный стандарт для обоснованных AI-assisted статей, социальных постов и необязательных иллюстраций.
</p>

<p align="center">
  <a href="LICENSE"><img alt="Лицензия: MIT" src="https://img.shields.io/badge/license-MIT-1677C8"></a>
  <a href="release/1.1.0.md"><img alt="Релиз: 1.1.0" src="https://img.shields.io/badge/release-1.1.0-2EA043"></a>
  <a href="rfcs/README.md"><img alt="Нормативный профиль: 1.0.0" src="https://img.shields.io/badge/profile-1.0.0-FF6B35"></a>
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.ru.md">Русский</a>
</p>

> **Факты важнее гладкости. Смысл важнее вовлечения.**

Human Writing Rules помогает AI-агенту превратить бриф и набор источников в готовый к публикации пакет материалов с явными границами доказательств, авторской позицией, результатом ревью и audit record. Пакет может содержать развернутую статью, социальный пост и, когда это действительно нужно, бриф для иллюстрации и сгенерированный визуал.

Это не AI-писатель, не набор приемов для обхода AI-детекторов и не один большой промпт. Это модульная спецификация для повторяемого редакционного процесса, где факты, источники, ограничения платформы, тон и легитимная авторская позиция остаются разными осями.

## Поддерживаемый контент

- Развернутые статьи для универсального блога, Habr, Dzen, Setka, GitHub, vc.ru, DEV Community или email-рассылок
- Социальные посты для универсальной социальной платформы, Telegram или LinkedIn
- Наука, технологии, развлечения, бизнес, здоровье, финансы, культура, лайфстайл, образование, путешествия и смешанные темы
- Запуски продуктов, личные истории, туториалы, новости и open-source анонсы
- Необязательные редакционные, объясняющие, обложечные и диаграммоподобные визуальные брифы

Регистры расширяемы. Неизвестная тема использует общий topic foundation, пока для нее не появится более узкий проверенный модуль.

## Пайплайн

```text
Бриф -> Разрешение модулей -> Источники -> Карта доказательств -> Контекстный гейт
      -> Дизайн материала -> Решение о медиа -> Черновик -> Редактура
      -> Необязательная генерация визуала -> Ревью -> Правка -> Пакет результата
```

## Принципы

- Исследование перед черновиком
- Факты перед гладкостью текста
- Аудитория перед форматом
- Смысл перед вовлечением
- Human signals вместо косметических анти-AI приемов
- Нативное письмо вместо буквального перевода
- Избирательная загрузка контекста вместо больших промптов
- Ревью перед публикацией
- Бенчмарки вместо неподтвержденных заявлений о качестве
- Нейтральность к моделям и вендорам

## Модель контента

Каждый выбор отвечает на отдельный вопрос:

| Ось | Вопрос | Примеры |
|---|---|---|
| `content_type` | Какой материал создается? | `article`, `social-post` |
| `topic` | Какие доказательства и доменные риски применимы? | `science`, `technology`, `entertainment` |
| `platform` | Где материал будет опубликован? | `blog`, `habr`, `dzen`, `github`, `newsletter`, `telegram` |
| `skill` | Какую задачу должен решить материал? | `news`, `tutorial`, `product-launch` |
| `tone` | Как должен звучать текст? | `expert`, `friendly`, `personal`, `blogger`, `developer`, `writer`, `screenwriter`, `amateur` |
| `author_perspective` | Из какой позиции написан материал? | `editorial`, `first-person`, `expert`, `neutral` |

Правила разрешения и fallback-логика описаны в [`core/content-model.md`](core/content-model.md).

## Статус

Текущий стабильный релиз — `1.1.0`. Он построен на активном нормативном профиле `1.0.0`, стабильных идентификаторах 1.x и границах совместимости. Стабильный статус спецификации не означает, что каждый writing engine или встроенный reference tooling уже доказал полное соответствие реализации. См. [Compatibility](COMPATIBILITY.md), [Migration](MIGRATING-TO-1.0.md) и [Releasing](RELEASING.md).

Репозиторий включает RU и EN языковые модули, форматы article и social-post, универсальные и платформенные publishing-модули, topic playbooks, tone profiles, правила visual integrity, reviewers, схемы, регистры, примеры, reference runner, benchmark contracts и starter kit.

RFC-0001 - RFC-0006 образуют [стабильный нормативный профиль](rfcs/README.md). Они определяют conformance, состояния пайплайна, жизненный цикл объектов, разрешение модулей, ревью и бенчмаркинг. Runtime rules реализуют более узкое поведение и MUST NOT ослаблять инварианты RFC.

Проверить полный релиз офлайн:

```sh
npm run release:verify
```

Основной пользовательский CLI написан на TypeScript и работает на Node.js 20.10 или новее:

```sh
npm install
npm run hwr -- --json doctor
npm run hwr -- --json runs questions \
  --config starter-kit/.human-writing-rules/config.json
```

Доступ к регистрам, discovery объектов, разрешение модулей, intake questions и run planning выполняются нативно в TypeScript. Команды, которые еще не перенесены, продолжают работать через временный Python 3.9+ compatibility backend. Статус миграции и критерии удаления Python описаны в [TypeScript CLI migration](reference-runner/typescript-migration.md).

## Быстрый старт

Скопируйте `starter-kit/.human-writing-rules/` в целевой репозиторий или добавьте этот репозиторий как закрепленный submodule. Затем дайте агенту инструкцию:

```text
Follow Human Writing Rules.
Language: ru
Content type: article
Topic: science
Platform: blog
Skill: news
Audience: curious readers without specialist training
Intent: explain what a new study found and what it did not prove
Visuals: auto
Use only verified facts from the supplied sources.
```

Агент начинает с `AGENTS.md`, разрешает минимальный достаточный набор модулей через `registry/objects.json` и следует `core/writing-pipeline.md`. `Visuals: auto` означает «добавить визуал только тогда, когда он дает объясняющую или редакционную ценность», а не «всегда генерировать изображение».

Если запрос неполный, агент проводит ограниченное [intake-интервью](guides/agent-led-intake.md): задает не больше пяти существенных вопросов за раунд, ждет ответы и не перекладывает на пользователя исследование, claim ledger, работу с регистрами или ревью. Пользователь может начать просто с «напиши статью про мистицизм»; агент до черновика соберет аудиторию, ожидаемый результат, границы источников, платформу, авторскую позицию, ограничения и требования к визуалу.

## Ожидаемый результат

Возвращайте эти секции отдельно:

1. **Final artifact** — только готовый к публикации текст.
2. **Visual assets** — сгенерированные файлы или готовые к генерации брифы, prompts, captions и alt text, если визуал выбран.
3. **Source notes** — связь утверждений с источниками, даты и нерешенная неопределенность.
4. **Review report** — найденные проблемы и внесенные правки.
5. **Audit record** — закрепленные версии спецификации и регистров, разрешенные модули, gates, fallbacks и deviations; tooling MAY хранить это отдельно и не показывать читателю публикации.

Не включайте внутренние заметки в готовый к публикации материал, если целевой формат этого не требует.

## Структура

```text
core/          обязательный пайплайн и модель контента
principles/    устойчивые принципы
rules/         правила форматов, тем, языков, платформ, визуалов, стиля, источников и human signals
skills/        task-specific workflows
reviewers/     независимые роли ревью
rfcs/          стабильная нормативная спецификация и conformance contracts
schemas/       machine-readable форматы
registry/      индексы объектов и зависимости
examples/      end-to-end примеры
benchmarks/    воспроизводимые evaluation cases
starter-kit/   пакет интеграции в проект
src/           основной TypeScript CLI и reference runtime
tools/         Python compatibility, validation и release tooling
test-ts/       cross-runtime CLI contract tests
```

TypeScript CLI — основной пользовательский runtime. Python-файлы в `tools/` и `tests/` относятся к совместимости, валидации и release support; они исключены из GitHub language detection через `.gitattributes`, чтобы язык репозитория отражал основную поверхность реализации.

Канонические registry-файлы компилируются в детерминированный resolver manifest [`registry/generated-index.json`](registry/generated-index.json). После изменений registry регенерируйте его и проверяйте командой `npm run check:registry-index`; см. [generated index contract](reference-runner/README.md#generated-registry-index).

Для полных end-to-end процессов используйте [Producing a grounded article](guides/article-production.md) или [Producing a grounded social post](guides/social-post-production.md). Применяйте выбранные [format rules](rules/format/), [topic foundations](rules/topic/), platform module и [illustration integrity rule](rules/visual/illustration-integrity.md).

Для выполнения детерминированного lifecycle используйте [reference runner](reference-runner/README.md). Он разрешает модули, валидирует claim ledger и gates, экспортирует vendor-neutral adapter packets, валидирует stage results, может запускать доверенный stdin/stdout adapter без shell и создает versioned output package без зависимости от model vendor.

Необязательный fail-closed [OpenAI Responses/Image adapter](reference-runner/README.md#optional-openai-adapter) включен для явного live-использования или credential-free fixture testing; core runner остается provider-neutral и offline.

Для полного persisted execution команда `workflows run` сохраняет каждое промежуточное состояние и возвращает отдельные publication, visual, source, review, revision и audit files; см. [workflow guide](reference-runner/README.md#persisted-end-to-end-workflow). Локальные материалы можно закреплять через [`sources snapshot`](reference-runner/README.md#local-source-snapshots), который проверяет path, size, source identity, byte count и SHA-256 до попадания материалов в run или provider packet.

Для reviewed non-trivial execution посмотрите [Russian mysticism article pilot](examples/pilot-runs/ru-mysticism/README.md): он включает статью, generated cover, claim ledger, stage records, review и validated final run.

[Reviewed example catalog](examples/README.md#reviewed-example-catalog) покрывает каждую зарегистрированную тему и platform family без искусственного полного cross-product. Запустите `npm run check:reviewed-examples`, чтобы проверить catalog, pinned artifact digests, editorial sections, reviewer sets и coverage.

Для controlled comparisons [benchmark runner](benchmarks/README.md) запускает pinned arms, сохраняет failures и raw outputs и отделяет evaluation от execution. Тот же benchmark contract теперь включает [visual acceptance fixtures](benchmarks/README.md#visual-acceptance-fixtures) для `auto -> none`, выбранных generated assets и expected hard failures. Запустите `npm run check:visual-benchmarks`, чтобы проверить frozen artifacts, PNG bytes, handoff metadata и acceptance records.

## Лицензия

MIT.
