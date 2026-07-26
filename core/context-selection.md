---
id: core.context-selection
kind: core
status: active
version: 1.0.0
---

# Selective Context Loading

Load the smallest sufficient rule set. Irrelevant modules increase conflicts and weaken priority.

## Always load

- `core.writing-pipeline`
- `core.content-model`
- one language foundation
- `rule.source-integrity`
- `rule.human-signals.core`
- source, language, human-signals, and editor reviewers

## Load by task

- one format foundation when `content_type` is known;
- one topic foundation; use `topic.general.foundation` for an unlisted or mixed topic;
- a generic platform foundation plus its specific child module when a platform is selected;
- one or more skills only when they describe the requested job;
- a tone module only when tone is explicit or safely inferred;
- `rule.visual-integrity` and `reviewer.visual` when visual mode is `auto` or `required`;
- specialist topic, platform, and format reviewers when applicable.

## Resolution order

1. Preserve explicit user selections.
2. Map configured values through the relevant registry index.
3. Add each selected object's transitive `requires` dependencies.
4. Deduplicate by stable object ID.
5. Reject unknown configured IDs; do not silently substitute a similarly named module.
6. Load the resulting files in dependency order.

Do not load every topic module “for safety.” A science article loads the science topic foundation, not science, health, finance, and technology together unless the brief materially spans those domains.
