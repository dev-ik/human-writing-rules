# Producing a grounded social post

Use this guide to turn a brief and source set into a platform-native social post
that remains accurate when encountered in a feed, forwarded, quoted, or
separated from a linked article.

This is a how-to guide. Normative authority remains in the
[RFC profile](../rfcs/README.md) and registered runtime modules. Resolve the
format, topic, platform, skill, language, perspective, visual, and reviewer
objects before drafting.

## What you produce

A completed run produces separable artifacts:

1. publication-ready post or explicitly ordered post series;
2. selected media or a generation-ready visual handoff;
3. source notes and claim ledger;
4. review findings and revision summary;
5. audit record with resolved modules, gates, fallbacks, and deviations.

The publication artifact contains only what the reader should see. Keep private
source material, internal review notes, and hidden reasoning outside the post.

## Required modules

Every social-post run starts with:

- `core.writing-pipeline`;
- one language module;
- `format.social-post.foundation`;
- `platform.social.foundation` and a narrower platform module when available;
- `rule.source-integrity`;
- `rule.human-signals.core`;
- the selected topic module;
- source, language, human-signals, format, topic, platform, and editor
  reviewers.

Add a skill only when the post has that job, such as news, product launch,
tutorial, or open-source announcement. Add `rule.visual-integrity` and
`reviewer.visual` whenever visual mode is `auto` or `required`.

## Start a run

For a conversational request, use the
[agent-led intake](agent-led-intake.md) first. The agent asks only questions
that can change the post's goal, audience, evidence boundary, platform,
legitimate perspective, constraints, or visual requirement.

The structured brief below is intended for integrations and already-resolved
tasks. Fill it from known facts and source references:

```text
Follow Human Writing Rules revision 1.0.0.

Language and locale:
Content type: social-post
Topic:
Platform:
Primary post job:
Audience:
Single communication goal:
Desired reader outcome:
Author perspective and its source:
Standalone post, gateway to longer material, or ordered series:
Current platform constraints to verify:
Research cutoff:
Risk level:
Required disclosure or constraints:
Visual mode: none | auto | required
Maximum visual count:

Supplied sources:
- [source identity and location]

Required missing source roles:
- [primary record, current status, independent context, rights record, ...]

Return separately:
1. publication-ready post or series;
2. selected media or generation-ready handoff;
3. source notes and unresolved unknowns;
4. review findings and revision summary;
5. audit record.
```

For a post adapted from an article, also supply the final article revision,
claim ledger, source notes, and any approved visual assets. Do not adapt from an
obsolete draft or from the headline alone.

## Step 1 — Create the post control record

Record:

| Field | Decision |
| --- | --- |
| Subject | Exact event, work, release, claim, question, or idea |
| Communication goal | One primary thing the post should accomplish |
| Reader outcome | What the reader should understand, feel, or do |
| Audience | Knowledge, relationship to the author, and feed context |
| Post job | Announce, explain, report, teach, recommend, evaluate, invite, or comment |
| Artifact form | Standalone post, gateway, response, or ordered series |
| Perspective | Editorial, neutral, reporter, expert, or authorized first-person |
| Topic and risk | Domain rules and required evidence threshold |
| Platform | Current length, formatting, link, media, tagging, and disclosure constraints |
| Evidence boundary | Supported claims, important limitations, and unknowns |
| Freshness | Source and platform cutoff |
| Visual mode | `none`, `auto`, or `required` |
| Required action | Real reader action, if one exists |
| Constraints | Rights, consent, embargo, privacy, brand, legal, and accessibility |

If the subject, platform, or source status changes, invalidate affected copy,
links, preview, visual, metadata, and review.

## Step 2 — Select the post job and form

### Choose one primary job

| Job | Reader value | Typical shape | Main risk |
| --- | --- | --- | --- |
| Announcement | Know what changed and whether it matters | development → relevance → availability or next step → limits | promotion presented as independent fact |
| News update | Know what happened and what remains unknown | verified event → time and source → meaning → unknowns | rumor, stale urgency, missing attribution |
| Explainer | Understand one concept or distinction | question → answer → essential context → implication | compressing away the evidence boundary |
| Tutorial tip | Perform one bounded action | outcome → prerequisite → action → verification | untested instruction |
| Recommendation | Decide whether something fits | audience need → criteria → fit and limits | universal advice from personal taste |
| Evaluation | Understand a bounded judgment | object → observation → criterion → conclusion | adjectives without evidence |
| Commentary | Understand an authorized position | position → reason → evidence or experience → boundary | fabricated authority or consensus |
| Invitation | Decide whether to participate | event or action → relevance → conditions → next step | false urgency or hidden conditions |

A post may have secondary functions, but they cannot compete for the ending or
require independent theses.

### Choose the artifact form

- **Standalone:** the post contains enough evidence and context to fulfill its
  promise without another artifact.
- **Gateway:** the post offers one useful idea and links to depth elsewhere. The
  linked artifact cannot carry every material qualification.
- **Response:** the referenced claim is identifiable and the post remains
  intelligible outside the conversation.
- **Ordered series:** complexity cannot be reduced safely to one unit. Each unit
  has a clear role and retains enough context when separated.

Use an article when the argument needs several independent claims, long source
qualification, procedural depth, or a structure that a social post cannot
preserve.

## Step 3 — Build the evidence boundary

### Create a claim budget

Short length is a reason to make fewer claims, not to weaken support.

List:

- one primary claim or announcement;
- supporting facts required to understand it;
- the most important limitation;
- optional context that can be omitted;
- reader action and the facts needed to justify it.

Every material claim maps to a source, authorized author material, or declared
opinion or inference. Omit an unsupported secondary claim instead of hiding it
inside compressed wording.

### Record source roles

Use the source closest to each claim:

- primary event, release, study, work, or official record;
- current status, version, date, correction, or availability;
- independent context or counterevidence;
- authorized first-person or organization material;
- link destination;
- rights and asset record;
- current platform requirement.

A social preview, search snippet, repost, screenshot without provenance, or
previous generated post is not automatically a verified source.

If the adapter needs an exact local document rather than source metadata, use a
[source snapshot](../reference-runner/README.md#local-source-snapshots). It
pins the supplied UTF-8 bytes and hash but does not establish truth, freshness,
rights, or authority. Snapshot content remains in run records and is sent to
the configured adapter, so do not attach secrets or restricted material.

### Preserve the context floor

The post should remain honest when:

- the reader does not open the link;
- a preview truncates the ending;
- the post is forwarded or quoted;
- an image is viewed without surrounding copy;
- a screenshot omits replies or earlier series units.

Put identity, attribution, status, material limitation, and required disclosure
in the post or asset when their absence would change the claim.

## Step 4 — Pass the context gate

Draft only when:

- the subject and communication goal are stable;
- audience, platform, language, topic, intent, and perspective are known;
- the post job and artifact form are selected;
- the primary claim has adequate support;
- important status, date, version, availability, and uncertainty are known;
- first-person or expert authority is legitimate;
- the post can preserve its context floor;
- current platform constraints are known where material;
- visual mode and rights boundary are explicit.

Block or narrow the post when:

- a requested claim cannot fit without losing a material qualification;
- a linked artifact or source is unavailable, stale, or contradicts the post;
- the identity or status of an event, product, work, or study is unresolved;
- an unsupported reaction, consensus, performance, or impact claim drives the
  post;
- a required visual would create false documentary evidence or violate rights.

Return a blocking question, narrower safe post, or recommendation to use an
article. Do not fill the gap with generic enthusiasm.

## Step 5 — Design the post

### Write the internal reader promise

Use one sentence:

> After reading this post, this audience will understand **X** and can decide or
> do **Y**.

If the sentence needs several unrelated verbs, split the task or choose a longer
format.

### Build content units

Give each unit a function:

- subject or verified development;
- reader relevance;
- essential evidence or explanation;
- limitation or boundary;
- real next step.

Not every post needs every unit. Do not convert this list into a template.

### Plan the opening

The opening should identify the subject, verified change, reader problem, or
concrete observation. It may create curiosity through specificity.

Do not use:

- false universals;
- manufactured suspense;
- an unsupported shock or breakthrough claim;
- a rhetorical question with an obvious answer;
- unexplained numbers;
- a fragment designed only to force expansion;
- a fabricated personal confession.

### Plan the ending

Choose the ending that completes the job:

- bounded conclusion;
- actual next step;
- source or full article;
- current limitation or next signal;
- a genuine question when audience input is needed.

Do not force a CTA, question, request for reactions, or “agree?” ending.

### Design a series

When using an ordered series:

1. define the series promise and unit count;
2. assign one claim or function to each unit;
3. keep identity, attribution, and material qualification recoverable;
4. mark order explicitly;
5. avoid repeating a teaser in every unit;
6. review each unit alone and in sequence.

If the series becomes an article broken at arbitrary character boundaries,
publish an article and use one gateway post.

## Step 6 — Make the media decision

For `auto`, include media only when it explains, verifies, or usefully frames the
post.

| Reader need | Candidate | Boundary |
| --- | --- | --- |
| Recognize a real person, place, work, product, or interface | Verified documentary or approved promotional asset | Preserve source, date, rights, and context |
| Understand a mechanism, sequence, or comparison | Diagram or conceptual illustration | Verify relationships and labels |
| Compare exact values | Constructed data visualization | Use verified data and readable units |
| Identify a theme in the feed | Editorial cover | Generated art cannot imply a real event or official asset |
| Read an exact statement | Text post or verified short quote card | Verify wording, attribution, rights, contrast, and alt text |
| Fill an image slot | No media | Decoration alone is not a reader benefit |

For every selected asset, record:

- purpose, placement, and relationship to the post;
- content it may show and implications it must avoid;
- verified asset source or generation rationale;
- dimensions, aspect ratio, crop, safe area, and first-frame behavior;
- prompt or construction instructions;
- caption, alt text, credit, provenance, rights, and disclosure;
- acceptance criteria and fallback.

Treat the preview and crop as part of the claim. Generated imagery must not
simulate a news photograph, real screenshot, official artwork, evidence, quote,
metric, interface, or event.

## Step 7 — Draft for meaning

### Draft the complete meaning first

Write the primary claim, context floor, limitation, and reader action before
optimizing line breaks, opening, tags, or media copy.

Keep:

- evidence close to the claim;
- attribution where authority matters;
- uncertainty where it changes interpretation;
- one dominant idea;
- paragraph and sentence length driven by thought.

### Compress safely

Remove in this order:

1. duplicate setup;
2. optional background;
3. decorative transition;
4. secondary example;
5. redundant CTA or metadata.

Do not remove identity, date, version, attribution, source status, material
limitation, disclosure, or rights context merely to fit.

When safe compression is impossible, narrow the promise, create a series, or
use an article.

### Add platform elements last

Add links, hashtags, mentions, emojis, tags, and CTA only when each has a real
function. Verify:

- the link destination and relationship;
- the mentioned account and reason;
- the meaning and cultural fit of an emoji;
- the discoverability value of a tag;
- the truth and availability behind the CTA.

## Step 8 — Adapt to the platform

Platform behavior changes. Verify current constraints at the task cutoff rather
than relying on remembered character limits, preview behavior, or media
features.

### Generic social platform

- Assume the reader has no prior context.
- Keep one dominant communication goal.
- Treat truncation, preview, first frame, crop, and quote context as editorial
  decisions.
- Preserve a durable source link for summarized external evidence.
- Ensure the post and media remain accessible outside the original interface.

### Telegram

- Front-load the subject and keep forwarded reading intelligible.
- Use paragraph breaks for comprehension, not line-by-line suspense.
- Give every link a reason to be followed.
- For a series, make order and dependency explicit.
- Check link preview, attachment order, caption relationship, crop, and
  accessible description in the actual publishing workflow.
- Emojis, reactions, hashtags, and closing questions remain optional.

### LinkedIn

- Establish professional relevance through a real problem, decision, result, or
  lesson.
- Preserve definitions, period, baseline, and source for metrics.
- Use personal experience, job history, customer response, and organizational
  claims only from authorized material.
- Keep enough linked-article context in the post.
- Verify mentions, media crop, embedded text, document order, captions, and
  disclosure against current platform behavior.
- Do not manufacture vulnerability, consensus, or engagement.

## Step 9 — Apply the topic profile

### Science social post

Record:

- exact study or evidence object;
- publication status and date;
- population or material;
- method, comparison, and measured outcome;
- central result and uncertainty;
- whether the post concerns one study, wider evidence, or consensus.

Keep association, causation, prediction, mechanism, statistical result, and
practical importance distinct. If the limitation cannot fit, narrow the claim or
link to a longer artifact while retaining the most important boundary in the
post.

Use verified charts or manually reviewed diagrams for exact scientific content.
A generated conceptual visual may frame the question, but cannot depict a
fictional experiment, result, specimen, scan, molecular structure, anatomy, or
causal mechanism as evidence.

### Technology social post

Record:

- exact product, project, standard, incident, or release;
- version, date, release channel, availability, and environment;
- documented, announced, observed, or reproduced status;
- evidence for performance, compatibility, security, or migration claims.

Do not collapse announced, available, enabled, tested, and production-ready.
Metrics keep their workload, baseline, period, and source.

Use verified screenshots for exact interfaces and diagrams for verified
relationships. Generated UI, code, labels, metrics, or command output is
illustrative and cannot be presented as real product evidence.

### Entertainment social post

Record:

- exact work, edition, region, release, and availability;
- news, review, recommendation, or commentary job;
- author access and legitimate first-person basis;
- spoiler boundary and evaluation criteria;
- quotation, promotional asset, character, logo, and likeness rights.

Separate fact, creator statement, marketing, observation, interpretation,
opinion, reception, and consensus. A short reaction cannot fabricate viewing
experience or universal audience response.

Prefer licensed promotional, owned, or public-domain assets. Generated editorial
art must not imitate a living artist, reproduce protected characters or scenes,
use performer likenesses, or imply official affiliation.

## Step 10 — Review, revise, and package

Use [Editing without losing meaning or voice](editing-existing-text.md) for
bounded revisions that preserve the post's conditions, uncertainty, and register.

Freeze one copy and asset revision per review pass.

Review:

1. source support, status, attribution, and freshness;
2. topic evidence and risk;
3. one-goal format fit and context floor;
4. native language and compression;
5. legitimate perspective and human signals;
6. current platform behavior;
7. media truthfulness, crop, accessibility, rights, provenance, and disclosure;
8. overall coherence and readiness.

For human signals in posts, check that compression has not erased the human
reason for speaking. A strong post may use one concrete situation, objection,
turn, or consequence; it must not invent first-person experience, consensus,
emotion, or casual familiarity to sound less generated.

Every finding names severity, location, reason, and smallest useful correction.
Resolve blockers and majors and re-review affected units.

Return:

- publication-ready post or ordered series;
- selected media or complete visual handoff;
- source notes and unresolved unknowns;
- review findings and revision summary;
- audit metadata, including why `auto` produced or omitted media.

## Adapting a finished article

Use the article as a verified source artifact, not as text to truncate.

1. Pin the final article revision and source notes.
2. Choose one idea useful in the feed.
3. Restate its evidence boundary in the post.
4. Keep the most important limitation visible.
5. Rewrite for the selected platform and perspective.
6. Link to the article for depth, not to repair a misleading post.
7. Re-evaluate the visual for feed crop and standalone meaning.
8. Review the post as a new artifact.

One article may produce several posts only when each has a distinct reader
promise. Do not create variants by swapping hooks, emojis, or CTA while keeping
the same meaning.

## Final release checklist

- [ ] The control record, communication goal, and reader promise are current.
- [ ] One primary claim or action controls the artifact.
- [ ] The context gate passed and the context floor survives forwarding and truncation.
- [ ] Material claims have sources or declared non-factual classifications.
- [ ] Identity, date, version, status, attribution, and limitation remain visible where needed.
- [ ] Perspective, experience, reactions, and organizational claims are authorized.
- [ ] Opening and ending serve meaning rather than engagement pressure.
- [ ] Current platform constraints, links, tags, mentions, and disclosure are checked.
- [ ] Visual mode has an explicit decision and selected media passed factual, crop, accessibility, rights, and provenance review.
- [ ] Blocker and major findings are resolved against one frozen revision.
- [ ] Publication copy, media, source notes, review output, and audit metadata remain separable.

If an item fails, return to the affected stage or mark the task blocked. Do not
label the post publication-ready.
