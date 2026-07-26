---
id: core.writing-pipeline
kind: core
status: active
version: 1.0.0
---

# Writing Pipeline

## 1. Task framing
Determine content type, topic, intended outcome, audience, language and locale, platform, author perspective, skill, constraints, source requirements, risk level, and visual mode.

Do not confuse these dimensions. `article` is a format, `science` is a topic, `blog` is a platform, and `news` is a skill.

## 2. Module resolution
Load `core.content-model`, the required foundations, and only the selected format, topic, platform, tone, skill, and reviewer modules. Resolve transitive `requires` relationships through `registry/objects.json`.

Explicit user choices override defaults. Infer a missing choice only when the inference is low-risk and does not materially change the artifact. Otherwise request clarification or record the choice as unknown.

## 3. Context collection
Collect only relevant material. Preserve source identity and date. Separate user-provided facts from retrieved facts.

For current or high-risk claims, record the retrieval or publication date and prefer primary sources. Collect enough context to understand limitations, not only the claim being promoted.

## 4. Evidence map
Classify every material item as verified fact, source claim, opinion, inference, assumption, or unknown.

Maintain a claim ledger for material assertions. A claim may be drafted only when it is supported, explicitly attributed, clearly qualified, or intentionally presented as opinion.

## 5. Context gate
Drafting begins only when:

- the subject and central reader question are understood;
- content type, language, audience, intent, and author perspective are known or safely inferred;
- the appropriate topic and risk rules are loaded;
- unsupported critical claims are removed, qualified, or marked for further research;
- source freshness is adequate for time-sensitive claims;
- real first-person experience exists when the selected perspective requires it;
- material platform or legal constraints are known.

If a missing answer could change the thesis, factual risk, format, or voice, stop and request it. Do not conceal a failed gate with generic prose.

## 6. Content design
Define the reader promise in one sentence. Choose the minimum viable structure and a claim-driven section order. Decide what the reader should understand, feel, or do. Do not force a template.

For an article, use `format.article.foundation`. For a social post, use `format.social-post.foundation`.

## 7. Media decision
Set visual mode to:

- `none`: no visual deliverable;
- `auto`: create a visual only when it explains, orients, or meaningfully frames the content;
- `required`: create the requested visual unless doing so would be misleading or unsupported.

For any selected visual, define purpose, content, evidence basis, placement, format, dimensions or aspect ratio, style constraints, caption, alt text, and disclosure requirements. Load `rule.visual-integrity`.

## 8. Draft
Write for meaning first. Keep factual and rhetorical layers distinguishable.

Write the body before optimizing the title, lead, pull quotes, CTA, or metadata. Attribute uncertainty where the reader encounters the claim.

## 9. Edit
Remove repetition, vague transitions, accidental hype, empty abstractions, unnecessary headings, and symmetry that adds no value.

Check that the title, lead, section order, conclusion, and visual plan still match the actual draft.

## 10. Visual production
When a visual was selected, generate or commission it from the approved visual brief. Do not use the image to add facts that are absent from the evidence map. If the generated result fails factual, editorial, accessibility, rights, or platform checks, revise it or omit it.

## 11. Review
Always run source, language, human-signals, and editor reviewers. Add format, topic, platform, task, and visual reviewers when applicable.

Reviewers return `blocker`, `major`, `minor`, or `note` findings with the affected location, reason, and smallest useful correction.

## 12. Revision
Fix identified issues. Do not rewrite unaffected passages merely to make the process look thorough.

Resolve every blocker and major finding. If one cannot be resolved, preserve the limitation and do not label the artifact publication-ready.

## 13. Output package
Return these parts separately:

1. publication-ready text;
2. visual assets or generation-ready visual briefs, prompts, captions, and alt text;
3. source notes and unresolved unknowns;
4. review findings and revision summary;
5. audit metadata with specification and registry revisions, resolved modules, gate decisions, fallbacks, and deviations.

Keep source and review notes outside the public artifact unless the target format requires them. Preserve generation provenance and required disclosure with visual assets.
