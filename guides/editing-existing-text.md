# Editing without losing meaning or voice

Use this guide when an authorized draft needs clearer language, less repetition,
or better reader focus. Keep the meaning and legitimate author voice while
fixing specific problems. A good passage may need no change.

This guide applies the existing [writing pipeline](../core/writing-pipeline.md),
[human-signals rule](../rules/human-signals/core.md), and
[review contract](../rfcs/RFC-0005-review-contract.md). It introduces no new
pipeline stage, CLI command, or mandatory style. Examples are local editing
exercises, not full reviewed publication packages or evidence of measured
quality improvement.

## Establish what may change

Extract the reader, purpose, language, platform, sources, and requested change
from the brief and supplied draft. Use [agent-led intake](agent-led-intake.md)
only for missing answers that could materially change the edit. Do not ask the
user to restate an adequate brief.

Record whether the task calls for a local correction, structural editing, or
adaptation to another audience or platform. If the user only requests clearer
wording, start with local changes. Preserve the author's supplied register,
point of view, terminology, and intended emphasis unless a concrete finding
or the brief requires otherwise. Permission to edit does not establish the
truth of a claim, authorize invented experience, or permit imitation of a named
living author or identifiable private person.

Resolve the applicable modules and keep the original draft as an identifiable
revision. Check its material claims against sources and author material. An
existing draft does not bypass the context gate. If a missing fact could change
the thesis or legitimate speaking position, record the gap before rewriting
the affected content.

Make an explicit media decision. Use `none` when the brief requests only text
and excludes a visual deliverable; preserve an explicit `auto` or `required`
choice.
If an existing visual is retained, check whether the edit changes its meaning,
caption, labels, or source boundary and apply the relevant visual review.

## Make the smallest useful edit

1. **Locate the problem.** Identify the passage and what prevents the reader
   from understanding, trusting, or using it. “Sounds like AI” is not a finding.
2. **Check the evidence.** Separate a wording problem from an unsupported claim.
   Do not supply a plausible actor, number, benefit, or anecdote to fill a gap.
3. **Choose the correction.** Delete empty setup, clarify a supported action,
   move an existing limitation next to its claim, or reorganize only when the
   argument requires it. Keep a useful list, contrast, or repeated term.
4. **Compare meanings.** Check who did what, when, under which conditions, with
   what attribution and certainty. Check negation, units, scope, and required
   disclosure. A shorter sentence is worse if it changes any of these.
5. **Re-read for voice.** Preserve legitimate warmth, restraint, technical
   precision, or informality. Do not turn every author into the same narrator.

## Worked edits

The passages below were written for these exercises. They are not quotations
from users, research, or product testimonials. Their factual boundaries come
from the linked repository documents. Each **Before** is an illustrative draft;
each **After** is suitable only for the stated context. None adds personal
experience, external events, performance measurements, or generated visuals.

### 1. RU: replace a generic opening with the reader's task

Context: a short introduction for a contributor who wants to use HWR.
Source boundary: the [pipeline](../core/writing-pipeline.md) begins with framing,
module selection, and evidence before drafting.

**Before**

> В современном мире качественный контент играет важную роль. Поэтому важно
> отметить, что к написанию текста нужно подходить комплексно и осознанно.

**After**

> Перед черновиком определите, для кого вы пишете и на какой вопрос отвечаете.
> Затем выберите правила для задачи и проверьте, чем подтверждаются основные
> утверждения.

The revision gives the contributor a starting action grounded in the workflow.
It does not invent urgency, audience demand, or a promise of better results.
Without that source context, simply deleting the opening would be safer than
inventing a process to replace it.

### 2. RU: name the action without losing the condition

Context: guidance for an editor choosing an optional image.
Source boundary: [visual mode semantics](../core/writing-pipeline.md) permit
`auto` to result in no visual.

**Before**

> При осуществлении выбора визуального сопровождения в режиме auto необходимо
> проведение оценки наличия пользы для читателя, а при её отсутствии следует
> осуществить отказ от добавления изображения.

**After**

> В режиме `auto` добавляйте изображение, если оно помогает читателю понять
> материал или сориентироваться в нём. Если такой пользы нет, обойдитесь без
> изображения.

The action becomes readable and the condition survives. Replacing the passage
with “Добавьте изображение” would reverse the optional-media decision.

### 3. EN: correct an unsupported promise before polishing it

Context: an introduction to the specification for prospective users.
Source boundary: [Compatibility](../COMPATIBILITY.md) distinguishes process
conformance from guarantees about individual outputs.

**Before**

> Unlock consistently accurate content with HWR. Following the specification
> guarantees that every article is factual and ready to publish.

**After**

> HWR defines an editorial process for checking sources, reviewing drafts, and
> recording unresolved issues. Following that process does not guarantee that
> every article is accurate or ready to publish.

Removing “Unlock” alone would leave the false promise intact. The meaningful
correction is the claim boundary, including the limitation next to the claim.

### 4. EN: compress without deleting a material limitation

Context: a release note explaining the scope of internal stability review.
Source boundary: [Compatibility](../COMPATIBILITY.md) and the
[stability review](../release/stability-review.json) preserve the distinction
between internal assessment and independent external review.

**Before**

> It is important to note that the repository includes an internal stability
> review. It is also important to note that this assessment does not constitute
> independent external review.

**After**

> The repository includes an internal stability review, which does not
> constitute independent external review.

The repeated setup disappears; the review's scope remains. “The repository has
been independently validated” would change the evidence, not improve the prose.

### 5. RU: keep a clear conversational sentence

Context: friendly guidance for an editor considering an optional illustration.
The illustration decision follows the same pipeline boundary as example 2.

**Before**

> Если картинка ничего не объясняет, её можно не добавлять. Режим `auto` это
> допускает.

**After — unchanged**

> Если картинка ничего не объясняет, её можно не добавлять. Режим `auto` это
> допускает.

There is no concrete defect for this audience and register. Replacing “картинка”
with “визуальное сопровождение” would add formality without improving the
meaning. A different brief may require a formal register; that is a task choice,
not a universal correction.

### 6. EN: retain a useful list and a real contrast

Context: explaining the output package to an integration author.
Source boundary: the [pipeline output package](../core/writing-pipeline.md)
separates publication copy from supporting records.

**Before**

> Keep these outputs separate:
>
> - publication text;
> - selected visual assets or briefs;
> - source notes;
> - review findings and revision summary;
> - audit metadata.
>
> Source notes belong in the supporting records, not in the publication text,
> unless the target format requires them there.

**After — unchanged**

Keep the passage. The list maps distinct deliverables, and the contrast explains
a placement rule with its exception. Neither is filler. Turning everything into
one paragraph or deleting the exception would make the instruction less useful.

## Review and stop

Freeze the edited revision and run source, language, human-signals, and editor
reviews, plus applicable format, topic, platform, task, and visual reviews.
Use the [finding fields and severities](../rfcs/RFC-0005-review-contract.md):
identify the location, concrete reason, applicable rule, and smallest useful
correction. Evaluate impact rather than how easy a phrase is to replace.

Map revisions to finding IDs, verify fixed blocker and major findings, and
re-run affected reviewers. Stop when the concrete findings are resolved;
another stylistic variant is not inherently an improvement. Do not label the
artifact publication-ready while a required review is incomplete or a blocker
or major finding remains unresolved.

Return clean edited copy separately from sources, remaining unknowns, review
findings, and the revision summary. Retain the original and edited revision
identifiers, resolved modules, gate decisions, and finding-to-change mapping
in the audit record. If an unsupported claim prevents completion, report the
gap rather than silently presenting a smooth rewrite as checked copy.
