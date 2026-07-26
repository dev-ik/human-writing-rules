# Reference lifecycle fixtures

These records demonstrate the complete vendor-neutral adapter lifecycle for the
`ru-science-article` task:

1. `ru-science-design.json` freezes the reader promise, thesis, and claim-driven
   structure.
2. `ru-science-draft.json` supplies meaning-complete publication copy.
3. `ru-science-edit.json` creates a new frozen artifact revision and supplies
   the selected visual handoff.
4. `ru-science-review.json` records every required reviewer and a readiness
   candidate.

The records identify fixture adapters but do not imply that the reference
runner called a model. A human, tool, or model integration may produce the same
contract.

`tools/hwr_fixture_adapter.py` reads an adapter packet from stdin and returns
the matching fixture record on stdout. It exists only to test and demonstrate
the transport contract.
