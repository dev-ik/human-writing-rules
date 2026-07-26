---
id: core.content-model
kind: core
status: active
version: 1.0.0
---

# Content Model

Use independent axes so editorial intent does not become entangled with platform convention.

| Axis | Meaning | Examples |
|---|---|---|
| Language | Native language and locale | `ru`, `en` |
| Format | Shape and reading experience | `article`, `social-post` |
| Topic | Domain evidence and risk rules | `science`, `technology`, `entertainment` |
| Platform | Publishing constraints | `blog`, `habr`, `social`, `telegram` |
| Skill | Job to be done | `news`, `tutorial`, `product-launch` |
| Tone | Delivery choices | `expert`, `friendly`, `personal` |
| Author perspective | Legitimate speaking position | `editorial`, `first-person`, `expert`, `reporter`, `neutral` |
| Visual mode | Whether visuals are produced | `none`, `auto`, `required` |

## Why the axes stay separate

“Write a science article for a blog about a new result” resolves to:

- format: `article`;
- topic: `science`;
- platform: `blog`;
- skill: `news` when timeliness is central;
- perspective: `neutral` or `reporter`;
- visual mode: the user's choice.

Changing the platform to Telegram changes length, pacing, and media placement. It does not change the evidence standard for the scientific claim.

## Format selection

Choose `article` when the reader needs sustained explanation, multiple claims, source context, or a navigable section structure.

Choose `social-post` when one dominant idea can be delivered in a short platform-native artifact. Use a thread or series only when the platform supports it and fragmentation helps the reader.

## Topic selection

Choose the narrowest topic that controls the material claims. Use `general` for mixed, low-risk, or currently unsupported domains. Load a second topic only when it contributes distinct evidence or safety requirements.

Topic selection changes source expectations and review questions. It must not predetermine tone or structure.

## Platform inheritance

Specific platforms inherit a generic foundation:

- Habr and Setka inherit `blog`;
- Telegram and LinkedIn inherit `social`.

Use the generic platform directly for an unlisted blog or social network. Add a new platform module only when it has durable, material constraints.

## Skill selection

Skills describe the requested outcome, not the subject or shape:

- `news`: explain what happened and what remains unknown;
- `tutorial`: help the reader complete and verify a task;
- `product-launch`: describe an available product without invented demand;
- `personal-story`: preserve a real supplied experience;
- `opensource`: explain a repository's problem, state, and limitations.

No skill is better than a misleading skill. A general explanatory article may use only format and topic modules.

## Author perspective

Use first person only when the author supplied real experience, observations, or opinions. Use `expert` only when the author or named source has the relevant standing. `Neutral` does not mean view-from-nowhere: preserve attribution, uncertainty, and editorial choices.

## Fallbacks

- Unknown format: clarify before drafting if length or structure would materially change.
- Unknown topic: load `topic.general.foundation` and record the fallback.
- Unknown platform: use the generic matching platform when format is clear; otherwise clarify.
- Unknown skill: omit the skill.
- Unknown tone: use a direct neutral register appropriate to the language and audience.
- Unknown visual need: use `auto`, which permits a justified decision to produce no image.
