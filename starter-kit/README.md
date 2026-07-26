# Starter Kit

Copy `.human-writing-rules/` into a target repository and adjust `config.json`. Pin the upstream version through a submodule, subtree, or documented release.

The included config is an article example, not a universal default. Override at least:

- `spec_revision` only when intentionally migrating to another normative profile;
- `language` and locale;
- `content_type`;
- `topic`;
- audience and intent;
- platform;
- author perspective;
- source and freshness requirements;
- visual mode.

Use `visuals.mode: auto` when an illustration is optional. `Auto` requires a documented media decision and may correctly produce no visual.

Task-specific instructions may override config defaults, but the final resolved choices must be recorded before drafting.

## Let the agent ask the questions

The user does not need to fill the entire config or article brief manually.
For an ordinary request such as “write an article about mysticism,” instruct
the agent to follow the copied `AGENTS.md`. It will extract known information,
ask at most five material questions, wait for the answers, and continue in
small adaptive rounds.

To inspect the same intake contract through the CLI:

```text
python3 tools/hwr.py --json runs questions \
  --config starter-kit/.human-writing-rules/config.json \
  --limit 5
```

Add `--task path/to/partial-task.json` when some answers already exist in a task
record. The command separates user questions from research, claim-ledger, and
validation actions that belong to the agent.

The included `registry_revision` pins the exact registry contents used by the
reference runner. Update it only as part of an intentional registry migration.
To diagnose a copied repository and plan a task before drafting:

```text
python3 tools/hwr.py --json doctor
python3 tools/hwr.py --json runs questions \
  --config starter-kit/.human-writing-rules/config.json
python3 tools/hwr.py --json runs plan \
  --config starter-kit/.human-writing-rules/config.json \
  --task examples/tasks/ru-science-article.json
```

See the [reference runner guide](../reference-runner/README.md) for the command
contract, gate behavior, and explicit limits.

For local source files that the adapter must read, create bounded
[source snapshots](../reference-runner/README.md#local-source-snapshots) and
reference them from task source records. Snapshot content is stored in run
records and sent to the configured adapter, so keep the source root and
provider boundary explicit.

After connecting a trusted adapter, `workflows run` can execute the guarded
stages and save the separated final package in a new workspace. It stops at
`blocked` or `needs-revision` instead of forcing publication; use
`workflows resume` only after inspecting and resolving the recorded findings.

Use the fillable brief and topic-specific additions in
[Producing a grounded article](../guides/article-production.md#start-a-run) when
the selected content type is `article`.

For `social-post`, use the fillable brief and adaptation workflow in
[Producing a grounded social post](../guides/social-post-production.md#start-a-run).
