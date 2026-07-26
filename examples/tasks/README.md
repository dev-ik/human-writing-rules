# Reference-runner task examples

These JSON files exercise the vendor-neutral pre-draft runner:

- `ru-science-article.json` resolves the starter config and passes the context
  and visual gates.
- `ru-blocked-unsupported-claim.json` is structurally valid but produces a
  blocked run because required sources, freshness assessment, and claim support
  are missing.

Neither fixture asks the runner itself to generate publication copy. The runner
prepares a deterministic module, evidence, gate, media, review, and output
record for a model, tool, or human adapter. The complete adapter-result sequence
is documented in [`../transitions/`](../transitions/README.md).

Run both from the repository root:

```text
python3 tools/hwr.py --json runs plan \
  --config starter-kit/.human-writing-rules/config.json \
  --task examples/tasks/ru-science-article.json

python3 tools/hwr.py --json runs plan \
  --config starter-kit/.human-writing-rules/config.json \
  --task examples/tasks/ru-blocked-unsupported-claim.json
```
