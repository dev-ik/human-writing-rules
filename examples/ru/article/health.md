# Example: RU Health Evidence Article

## Task framing

- Language: Russian
- Content type: article
- Topic: health
- Platform: generic blog
- Audience: generalist editors handling health-related claims
- Intent: explain the minimum evidence record before drafting
- Author perspective: neutral editorial
- Risk: high
- Visual mode: none
- Sources: `rules/topic/health/foundation.md`, `rules/sources/source-integrity.md`

## Resolved modules

`core.writing-pipeline` → `format.article.foundation` → `topic.health.foundation` → `platform.blog.foundation` → `language.ru.foundation` → source, human-signal, format, topic, platform, and editor reviewers.

## Evidence map

- Verified repository rule: health claims retain population, intervention, comparator, outcome, timeframe, and evidence quality.
- Verified repository rule: laboratory, animal, observational, and clinical evidence remain distinguishable.
- Verified repository rule: the text does not diagnose, prescribe, promise outcomes, or replace professional care.
- Verified repository rule: emergency direction requires an authoritative locale-appropriate source.

## Context gate

This is an editorial-method article, not medical guidance. It names no condition, treatment, dosage, risk figure, or urgent-care instruction. The absence of clinical specifics is intentional and prevents the method example from becoming actionable health advice.

## Content design

- Reader promise: the reader can identify when a health brief is not ready for drafting.
- Working thesis: a fluent summary cannot repair an incomplete evidence record.
- Structure: identify the claim → preserve the study frame → test actionability → block unsafe drafting.

## Final artifact

# Что проверить до того, как писать о здоровье

Фраза «подход помог участникам» слишком коротка для медицинского вывода. До черновика нужно понять, кого изучали, какое вмешательство сравнивали, с чем сравнивали, какой результат измеряли и в какой срок.

Затем определяется тип доказательства. Наблюдение за группой, эксперимент на животных и клиническое исследование отвечают на разные вопросы. Если убрать этот уровень из пересказа, осторожный результат может превратиться в совет, которого источник не давал.

Особенно важно проверить, меняет ли текст поведение читателя. Упоминание диагноза, лекарства, дозировки, противопоказания или срочного действия повышает риск. Общего предупреждения в конце недостаточно, если основной текст уже звучит как персональная рекомендация.

Иногда контекстный шлюз должен остановить работу. Нет подходящего источника, неизвестна группа, относительный эффект дан без базового риска или срочная рекомендация не подтверждена локальным официальным материалом — значит, публикационный текст пока не готов.

Это не избыточная осторожность. В теме здоровья отказ от уверенной формулировки может быть более точным редакционным результатом, чем ещё один гладкий абзац.

## Media decision

Decision: no visual. Медицинская иллюстрация без конкретной проверенной задачи могла бы добавить анатомический или диагностический смысл, отсутствующий в статье.

## Source notes

- `rules/topic/health/foundation.md` supports evidence hierarchy, PICO-like context, absolute-risk context, contraindications, and non-prescriptive boundaries.
- `rules/sources/source-integrity.md` supports the context gate and claim ledger.
- No medical advice or external medical fact is provided.

## Review result

- Reviewed revision: `ru-health-evidence-article-r1`.
- Source, language, human-signals, format, topic, platform, and editor reviewers: pass.
- High-risk check: no diagnosis, prescription, outcome promise, dosage, or emergency instruction.
- Open blocker or major findings: none.
- Readiness: publication-ready as editorial guidance, not health guidance.
