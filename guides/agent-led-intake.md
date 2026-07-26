# Agent-led intake

Use agent-led intake when a user asks for an article or social post in ordinary
language instead of supplying a complete task record. The agent turns the
conversation into a grounded brief before research or drafting.

## Desired interaction

The user may begin with:

> Напиши статью про мистику.

The agent should not respond with an article or a long questionnaire. It should
extract the known subject and ask a small first round:

1. Для кого пишем и что читатель должен получить от статьи?
2. Это обзор мистики как культурного явления, анализ приёмов в историях или
   материал о предполагаемых сверхъестественных событиях?
3. Есть ли обязательные источники, или можно самостоятельно провести поиск?
4. Где выйдет статья и какой примерно нужен объём?
5. Иллюстрация обязательна, опциональна или не нужна?

The next round depends on the answers. An entertainment analysis may need the
exact work, edition, spoiler boundary, and evaluation criteria. A claim about a
real event instead needs source identity, dates, competing explanations, and a
clear boundary between evidence and belief.

## Question-selection rules

Ask a question only when its answer can materially change at least one of:

- subject or thesis;
- audience or reader outcome;
- artifact type or platform;
- evidence threshold, freshness, or research scope;
- legitimate author perspective;
- privacy, consent, rights, disclosure, deadline, or other constraint;
- visual requirement or factual boundary.

Do not ask the user to:

- resolve registry objects;
- classify every claim;
- build the evidence map;
- inspect source freshness when the agent can inspect it;
- design the article structure;
- choose reviewers;
- decide whether an optional illustration adds value.

These are agent responsibilities.

## Bounded rounds

Ask at most five questions in one message. Prefer fewer when one answer controls
later questions. Wait for the answers before sending another batch.

Do not repeat a question whose answer is already present in the conversation,
task record, supplied source, or explicit project constraint. When the user
says “выбери сам”, choose a low-risk editorial default and record it as an
authorized assumption. Still ask for facts, authority, consent, or rights that
cannot be inferred safely.

## Completion

After the last answer:

1. summarize the resolved brief compactly;
2. identify any agent-owned research or verification actions;
3. run the context gate;
4. ask another question only if the gate exposes a material user decision;
5. begin drafting only after the gate passes.

Do not request ceremonial confirmation when the user has already answered
clearly and no material choice remains.

## CLI contract

The reference CLI can produce the next bounded question batch:

```sh
python3 tools/hwr.py --json runs questions \
  --config starter-kit/.human-writing-rules/config.json \
  --limit 5
```

Add `--task path/to/partial-task.json` when a partial structured task already
exists. The command returns:

- `question_batch`: questions that require user input;
- `agent_actions`: research, classification, or validation work owned by the
  agent;
- `proposed_defaults`: project-config values not yet confirmed by the task;
- `remaining_question_count`: questions deferred to a later round.

The command emits questions; it does not conduct an interactive terminal
session or write answers back to a task file. A conversational agent or UI
should ask the batch, update the task record from the answers, and run the
command again.

The output conforms to
[`schemas/intake-plan.schema.json`](../schemas/intake-plan.schema.json).
