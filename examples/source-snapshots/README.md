# Local source snapshot example

This directory demonstrates the complete offline source-ingestion path:

1. `materials/evidence-boundary-note.md` is the supplied UTF-8 source;
2. `snapshots/evidence-boundary-note.snapshot.json` pins its exact bytes;
3. `task.json` attaches the snapshot to `SRC-LOCAL-001`;
4. `runs plan` verifies the path, size, source ID, byte count, and SHA-256
   before placing the content in the run record and adapter packet.

Recreate the snapshot from the repository root:

```sh
python3 tools/hwr.py --json sources snapshot \
  --source-root examples/source-snapshots \
  --input materials/evidence-boundary-note.md \
  --source-id SRC-LOCAL-001 \
  --snapshot-id SNAP-EVIDENCE-BOUNDARY-001 \
  --media-type text/markdown \
  --captured-at 2026-07-26 \
  --rights "Repository example under the project license" \
  --notes "Synthetic local fixture; not external evidence." \
  --out /tmp/evidence-boundary-note.snapshot.json
```

Plan a run with the checked-in snapshot:

```sh
python3 tools/hwr.py --json runs plan \
  --config starter-kit/.human-writing-rules/config.json \
  --task examples/source-snapshots/task.json
```

The default source root is the task file's directory. Use `--source-root` only
when snapshot files intentionally live under another bounded directory.
