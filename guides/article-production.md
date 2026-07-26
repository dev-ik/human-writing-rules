# Producing a grounded article

Use this guide to turn a brief and a source set into a publication-ready
article, with an illustration only when it improves the reader's understanding
or orientation.

This is a how-to guide. Normative authority remains in the
[RFC profile](../rfcs/README.md) and the registered runtime modules. Resolve the
applicable modules before using the topic sections below.

## What you produce

A completed run produces five separable artifacts:

1. publication-ready article;
2. visual asset or generation-ready visual handoff when selected;
3. source notes and claim ledger;
4. review findings and revision summary;
5. audit record with resolved modules, gates, fallbacks, and deviations.

Do not merge internal source or review notes into public copy unless the
publication format requires them.

## Required modules

Every article starts with:

- `core.writing-pipeline`;
- one language module;
- `format.article.foundation`;
- `rule.source-integrity`;
- `rule.human-signals.core`;
- the selected topic module;
- the selected platform module;
- source, language, human-signals, format, topic, platform, and editor
  reviewers.

Add `rule.visual-integrity` and `reviewer.visual` whenever visual mode is `auto`
or `required`. Add a skill only when the article has that specific job, such as
news reporting or a tutorial.

## Start a run

Fill this brief with facts and source references. Do not replace unknown values
with plausible guesses.

```text
Follow Human Writing Rules revision 1.0.0.

Language and locale:
Content type: article
Topic:
Platform:
Primary article job:
Audience:
Central reader question:
Intent and desired reader outcome:
Author perspective and its source:
Approximate length:
Deadline and research cutoff:
Risk level:
Required disclosures or constraints:
Visual mode: none | auto | required
Maximum visual count:

Supplied sources:
- [source identity and location]

Required missing source roles:
- [primary record, independent context, version history, rights record, ...]

Return separately:
1. publication-ready article;
2. visual assets or generation-ready handoff when selected;
3. source notes and unresolved unknowns;
4. review findings and revision summary;
5. audit record.
```

Add the relevant topic block.

### Science brief additions

```text
Scientific object and publication status:
Research question:
Population or material:
Method and comparison:
Measured outcome:
Known uncertainty and limitations:
One study, body of evidence, or consensus:
Required wider-evidence context:
```

### Technology brief additions

```text
Technical object and owner:
Exact version, release channel, and date:
Availability, environment, configuration, and dependencies:
Documented behavior:
Observed or reproduced behavior:
Benchmark or test procedure:
Compatibility, migration, security, and operational limits:
```

### Entertainment brief additions

```text
Work, medium, edition, region, and availability:
Article type: news | review | analysis | interview | recommendation | retrospective
Author access or experience source:
Evaluation criteria:
Spoiler boundary:
Reception or consensus evidence cutoff:
Quotation and visual-asset rights:
```

## Step 1 — Create the article control record

Record these decisions before research or drafting:

| Field | Decision |
| --- | --- |
| Subject | The exact work, event, system, question, or body of evidence |
| Central reader question | The question the finished article must answer |
| Audience | Knowledge, needs, likely misconceptions, and reading context |
| Intent | Explain, analyze, report, teach, review, argue, or narrate |
| Reader promise | What the reader will understand, know, or be able to do |
| Author perspective | Editorial, neutral, reporter, expert, or authorized first-person |
| Topic and risk | Applicable domain module and low, medium, or high risk |
| Platform | Publication constraints, markup, metadata, and likely reading mode |
| Scope | Included and excluded questions |
| Length | Approximate range justified by the material |
| Freshness boundary | Research cutoff and time-sensitive claims |
| Sources | Supplied material and missing source roles |
| Visual mode | `none`, `auto`, or `required` |
| Constraints | Deadline, disclosure, rights, legal, brand, and accessibility needs |

Do not infer first-person experience or expertise from tone. If a missing field
could change the thesis, evidence threshold, speaking position, or artifact
type, stop at the context gate.

### Write the reader promise

Use an internal sentence, not necessarily public copy:

> After reading, this audience will understand **X**, know **Y**, and be able to
> **Z**.

Make it narrow enough to prove. “Understand artificial intelligence” is not a
workable promise. “Understand what this benchmark measures, what changed
between versions, and whether the result applies to their workload” is.

### Define the evidence boundary

Write three short lists:

- **In scope:** claims the article will establish.
- **Out of scope:** adjacent questions the article will not answer.
- **Unknown:** material questions that remain open at the research cutoff.

This prevents background research from silently expanding the thesis.

## Step 2 — Select the article job

Choose the job from reader need and evidence, not from a preferred template.

| Job | Use when | Minimum useful path | Typical failure |
| --- | --- | --- | --- |
| Explainer | The reader needs a concept or mechanism | question → context → mechanism → implications → limits | terminology without a reader problem |
| Analysis | Evidence supports a bounded thesis | thesis → evidence → alternatives → limits → conclusion | opinion disguised as inevitability |
| Reported article | A verified development is the subject | development → significance → context → perspectives → unknowns → next signals | announcement rewritten as reporting |
| Tutorial | The reader needs a reproducible result | result → prerequisites → steps → verification → failure modes | steps that were never tested |
| Review | The reader needs an evidence-based evaluation | object and criteria → observations → strengths and limits → suitable audience → verdict | adjectives without criteria |
| Opinion | A legitimate author position is the value | position → reasons → strongest objection → response → bounded conclusion | personal authority fabricated by tone |
| Narrative | A real sequence or experience carries the meaning | event → relevant detail → tension or change → honest interpretation | invented scenes or forced universal lesson |

Hybrid articles are valid. Name one primary job and record why each secondary
job is necessary. A product announcement with one tutorial section is still
primarily reported or promotional content; the tutorial does not make every
claim independently verified.

## Step 3 — Build the research plan

### Assign source roles

Do not collect links without knowing what they support. Assign roles such as:

- primary record or original artifact;
- methods, specification, or technical reference;
- independent context;
- counterevidence or alternative explanation;
- current status, correction, or version history;
- authorized author material;
- rights or licensing record;
- platform requirement.

One source may fill several roles, but popularity does not turn a secondary
summary into a primary record.

### Record every material source

For each source, retain:

| Field | Purpose |
| --- | --- |
| Source ID | Stable reference used by the claim ledger |
| Title and publisher | Human-identifiable source |
| Author or issuing body | Authority and possible conflict |
| Publication and retrieval dates | Freshness boundary |
| Version, edition, jurisdiction, population, or environment | Applicability |
| Source role | Why the source is present |
| Relevant passage, data, or observation | Exact support boundary |
| Limitations | What the source cannot establish |
| Rights or access restriction | Safe use and publication |

Treat snippets, model memory, previous generated text, and unattributed
summaries as discovery aids, not verified sources.

When the adapter needs the actual local material, create a
[source snapshot](../reference-runner/README.md#local-source-snapshots) and
attach its relative `snapshot_path` to the source record. The snapshot pins
what the adapter saw; it does not upgrade the material's truth, authority,
freshness, rights, or scope. Do not snapshot secrets or restricted material
that may not be stored in the workflow or sent to the selected provider.

### Create the claim ledger

Before outlining, list every thesis-level or decision-relevant claim:

| Claim ID | Planned claim | Classification | Support | Scope or qualification | Disposition |
| --- | --- | --- | --- | --- | --- |
| `C-01` | What you intend to say | verified fact, source claim, opinion, inference, assumption, or unknown | source or authorized material | date, version, population, confidence, or other boundary | use, narrow, attribute, research, omit |

Use these rules:

- A verified fact maps to adequate evidence.
- A source claim names the source when its authority or interpretation matters.
- An opinion has a legitimate speaker and is not converted into consensus.
- An inference exposes the reasoning and does not masquerade as observation.
- An assumption remains internal unless the reader needs it disclosed.
- An unknown cannot become fluent filler.

### Resolve conflicts

When reliable sources disagree:

1. confirm they address the same object, definition, date, version, or
   population;
2. prefer the source with stronger direct access to the relevant claim;
3. preserve material disagreement when it cannot be resolved;
4. narrow the conclusion instead of selecting the most convenient source;
5. record the decision in source notes.

## Step 4 — Pass the context gate

Draft only when all of the following are true:

- the subject and central reader question are stable;
- audience, intent, language, platform, and legitimate perspective are known;
- the article job and reader promise are defined;
- the correct topic and risk modules are loaded;
- every critical claim has support or a declared non-factual classification;
- freshness is adequate for time-sensitive claims;
- conflicts and limitations that could change the thesis are visible;
- required disclosure, rights, privacy, and legal constraints are known;
- visual mode has been selected, even if the decision is `none`.

Block the run when:

- identity, version, date, or source status is material but unknown;
- the supplied sources cannot support the requested conclusion;
- a requested first-person or expert position is unauthorized;
- a high-risk claim lacks the required evidence or specialist review;
- the requested visual would imply facts that cannot be verified.

Return the blocking question or research gap. Do not draft a generic substitute.

## Step 5 — Design the article

### State the working thesis

Write the narrowest conclusion the evidence currently supports. A working
thesis is not a headline and may change during drafting.

### Build section cards

Give each planned section:

- reader question;
- section claim;
- claim IDs;
- evidence and attribution;
- important limitation;
- example or explanation, if needed;
- transition;
- possible visual role.

Remove a section when it does not advance the reader promise. Merge sections
that repeat the same claim. Split a section when it asks the reader to process
several independent ideas at once.

### Check information order

Prefer dependency order:

1. information needed to understand later claims;
2. the main answer or verified development;
3. evidence and mechanism;
4. alternatives, limitations, or disagreement;
5. implications that remain inside the evidence boundary;
6. a conclusion proportionate to the body.

Background does not automatically belong first. Put it where the reader needs
it.

### Plan source presentation

Choose how the platform will expose evidence:

- inline links;
- footnotes or endnotes;
- a source list;
- explicit attribution in prose;
- a separate methodology or data note.

The public article should make material authority and uncertainty legible
without turning every sentence into citation machinery.

## Step 6 — Make the media decision

For `auto`, select a visual only when a concrete reader benefit survives review.

| Need | Best candidate | Generation boundary |
| --- | --- | --- |
| Orient the reader in a feed | Editorial cover | May be generated if it does not imply a real event, product, or endorsement |
| Explain mechanism or sequence | Diagram or conceptual illustration | Relationships and labels require evidence and manual review |
| Compare verified values | Data visualization | Use verified data; generation is not a substitute for chart construction |
| Show exact appearance | Original photo, screenshot, scan, or verified asset | Do not generate a documentary substitute |
| Add decoration only | No visual | An empty template slot is not a reader benefit |

For every selected visual, record:

- purpose and placement;
- reader benefit;
- evidence-backed content it may show;
- content or implication it must avoid;
- asset type and why generation is appropriate;
- composition, hierarchy, dimensions, aspect ratio, and crop;
- prompt and negative constraints;
- caption, alt text, credit, provenance, rights, and disclosure;
- acceptance criteria and fallback.

If exact data, anatomy, code, interface, map, quotation, product appearance, or
historical detail matters, prefer a verified asset or manually constructed and
reviewed graphic.

## Step 7 — Draft in controlled passes

### Pass 1: body for meaning

- Answer the section question directly.
- Put evidence close to the claim.
- Define a term at first useful mention.
- Separate observation, source statement, inference, and opinion.
- Explain material uncertainty where it changes interpretation.
- Use examples to clarify, not to replace evidence.

Do not optimize the title, opening flourish, CTA, or metadata yet.

### Pass 2: argument and proportion

- Confirm that each section advances the working thesis.
- Test the strongest alternative interpretation.
- Move limitations next to the claims they constrain.
- Remove conclusions that extend beyond source scope.
- Preserve meaningful disagreement.

### Pass 3: reader comprehension

- Check assumed knowledge.
- Replace avoidable jargon; explain necessary terms.
- Add an example only where abstraction blocks understanding.
- Shorten setup that delays the answer.
- Preserve enough context to prevent a misleading simplification.

### Pass 4: language and human signals

- Write natively in the selected language.
- Prefer specific nouns and verbs over generic significance.
- Vary rhythm because the thought varies, not to simulate humanness.
- Remove synthetic quotations, fabricated anecdotes, decorative uncertainty,
  and claims of personal experience.
- Do not add errors or awkwardness to evade AI detection.

## Step 8 — Finish article elements

### Title

The title should identify the subject and accurately compress the finished
article. It may create curiosity, but it cannot promise stronger evidence,
certainty, novelty, availability, or consensus than the body supports.

### Deck or standfirst

Use it to add scope, reader value, or a material qualification that the title
cannot carry. Do not repeat the title.

### Lead

Start with the subject, verified development, reader problem, or a concrete
observation. Establish relevance without false urgency, theatrical suspense, or
an unsupported universal claim.

### Conclusion

Answer the reader promise at the same confidence level as the body. A conclusion
may state remaining uncertainty or the next decision signal. It does not need a
CTA, inspirational lesson, or prediction.

### Metadata

Prepare only what the platform needs: excerpt, tags, slug, disclosure, author
note, source note, captions, and social preview. Metadata must make the same
promise as the article.

## Step 9 — Review and revise

Freeze one article and asset revision for each review pass.

Run these reviews:

1. **Source:** support, attribution, claim classification, freshness, conflict.
2. **Topic:** domain-specific evidence, terminology, limitations, and risk.
3. **Format:** reader promise, structure, article elements, and conclusion.
4. **Language:** native phrasing, precision, register, and ambiguity.
5. **Human signals:** legitimate perspective and absence of fabricated texture.
6. **Platform:** markup, length, links, metadata, and media constraints.
7. **Visual:** purpose, factual boundary, rights, accessibility, provenance.
8. **Editor:** coherence, proportion, duplication, and readiness.

Every finding identifies severity, location, reason, and the smallest useful
correction. Fix blockers and majors, re-review the affected content, and avoid
rewriting unaffected passages.

## Step 10 — Package the result

### Publication copy

Return only content intended for the reader.

### Visual handoff

For each selected asset, return the brief, prompt or construction instructions,
dimensions, caption, alt text, credit, provenance, disclosure, and review
status. If `auto` resulted in no asset, preserve the reason in the audit record.

### Source notes

Return claim-to-source mapping, dates, scope limits, conflicts, and unresolved
unknowns. Do not expose private source material.

### Review and audit

Return findings, dispositions, revision summary, specification revision,
resolved modules, gate decisions, fallbacks, and documented `SHOULD`
deviations.

## Science article profile

Load `topic.science.foundation`.

### Establish the research object

Record:

- paper, dataset, protocol, review, replication, correction, or other object;
- publication status and date;
- research question and preregistration when relevant;
- population or material studied;
- sample and comparison;
- method and measured outcome;
- effect estimate and uncertainty;
- author-stated and independently identified limitations;
- funding, conflicts, correction, retraction, or replication context.

Determine whether the article concerns one study, a body of evidence, or a
scientific consensus. Do not generalize from one level to another.

### Translate the claim

Keep these distinctions visible:

- association versus causation;
- statistical result versus practical importance;
- observed outcome versus proposed mechanism;
- model or laboratory result versus real-world effect;
- subgroup result versus general population;
- exploratory finding versus preregistered endpoint;
- preprint versus peer-reviewed or replicated evidence.

The useful article path is often:

1. what researchers asked;
2. what they actually studied;
3. what they observed;
4. how strong and bounded the result is;
5. what it does not establish;
6. how it fits the wider evidence.

### Select science visuals

Use:

- a verified chart for exact values;
- a manually reviewed diagram for a mechanism supported by evidence;
- a conceptual illustration for an abstract research question;
- no visual when only decorative laboratory imagery is available.

Do not generate experimental results, realistic documentary laboratory scenes,
precise molecular structures, anatomy, or causal diagrams without evidence and
manual specialist review.

## Technology article profile

Load `topic.technology.foundation`.

### Establish the technical object

Record:

- product, library, protocol, standard, model, service, incident, or proposal;
- owner or maintainers;
- exact version, release channel, and date;
- environment, configuration, dependencies, and feature flags;
- documented behavior;
- observed or reproduced behavior;
- vendor claims and roadmap statements;
- compatibility, migration, security, and operational boundaries.

Do not collapse “announced,” “documented,” “available,” “enabled,” “tested,” and
“production-ready” into one status.

### Make technical evidence reproducible

For tests and benchmarks, preserve:

- question and success criterion;
- hardware, software, region, and relevant configuration;
- dataset or workload;
- baseline and treatment;
- repetitions, variance, and exclusions;
- raw result or reproducible procedure;
- limits on generalization.

Code examples and procedures should run in the stated environment. If they were
not executed, label them illustrative.

### Select technology visuals

Use:

- a verified screenshot when exact interface state matters;
- a diagram derived from verified components and relationships;
- a constructed benchmark chart from preserved data;
- a conceptual cover that does not imply an existing product interface;
- no visual when the article's code or table already explains the point.

Generated interface images must be labeled illustrative and must not be
presented as screenshots. Generated labels, code, metrics, and component
relationships require manual verification.

## Entertainment article profile

Load `topic.entertainment.foundation`.

### Establish the work and editorial position

Record:

- exact title, medium, edition, cut, translation, episode, platform, and region;
- release and availability date;
- credited creators and material award status;
- whether the article is news, review, analysis, interview, or recommendation;
- author's legitimate viewing, reading, listening, or playing basis;
- spoiler boundary;
- evaluation criteria;
- quotation and asset rights.

Separate:

- verifiable facts about the work;
- creator or distributor statements;
- marketing claims;
- concrete observations from the work;
- interpretation;
- author opinion;
- audience reception;
- critical consensus, when adequately evidenced.

### Build an accountable evaluation

Choose criteria relevant to the form: structure, pacing, performance, mechanics,
visual language, sound, genre use, translation, accessibility, or another
declared dimension.

For each judgment, show the path:

> concrete observation → interpretation → criterion → bounded evaluation

The path supports disagreement without pretending that taste is a verified
fact. Do not invent first-person consumption, emotional response, creator
intent, audience consensus, or private production context.

### Select entertainment visuals

Prefer licensed promotional assets, owned materials, public-domain works, or an
original editorial illustration. Record credit and usage boundaries.

Do not imitate a living artist's signature style or generate unlicensed
characters, logos, actor likenesses, key scenes, or an asset that implies
official affiliation. When rights or identity cannot be resolved, choose no
visual.

## Mixed-topic articles

Load more than one topic module only when each governs material claims. Assign
each claim to its controlling topic.

Examples:

- a story about a medical device may require technology and health;
- an article about a film's box office may require entertainment and business;
- a report on climate-model software may require science and technology.

The stricter applicable evidence or safety rule controls the affected claim.
One topic cannot weaken another topic's requirements.

## Final release checklist

- [ ] The control record and reader promise are current.
- [ ] The context gate passed against the final evidence boundary.
- [ ] Every material claim has a source or declared non-factual classification.
- [ ] Title, lead, body, conclusion, and metadata make compatible promises.
- [ ] Topic-specific identity, version, scope, and uncertainty are visible.
- [ ] First-person and expert positions are authorized.
- [ ] Visual mode has an explicit decision and every selected asset passed its gate.
- [ ] Required captions, alt text, credit, provenance, rights, and disclosure are complete.
- [ ] Review used one frozen revision and all blocker and major findings are resolved.
- [ ] Publication copy, source notes, review output, and audit metadata are separate.

If any item fails, return to the affected stage or mark the task blocked. Do not
label the article publication-ready.
