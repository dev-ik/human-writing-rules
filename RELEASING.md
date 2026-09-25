# Releasing Human Writing Rules

This runbook verifies a release source state and defines the boundary for
publishing it. Verification itself does not push, tag, or create a GitHub
release.

## Current stable release

- Distribution: `1.1.1`
- Specification: `1.0.0`
- Channel: `stable`
- Manifest status: `released`
- Release date: `2026-09-25`
- Network requirement for verification: none

The canonical release record is [`release/manifest.json`](release/manifest.json).
The internal assessment and its independence limitation are recorded in
[`release/stability-review.json`](release/stability-review.json).

## Release gates

Run the complete manifest-defined suite:

```sh
npm run release:verify
```

The command executes every gate without a shell, applies a timeout, retains
bounded diagnostics, stops after a failed gate, and returns a JSON summary. It
does not write an approval or modify the manifest.

Individual checks remain available:

```sh
npm run test:conformance
npm run check
npm run check:conformance
npm run test:fixtures
npm run check:registry-index
npm run check:visual-benchmarks
npm run check:reviewed-examples
npm run runner:doctor
npm run check:release
```

## Stable release checklist

- [ ] `VERSION`, `package.json`, and `release/manifest.json` equal the current release.
- [ ] Every normative RFC is `active` at revision `1.0.0`.
- [ ] Every registered runtime object is `active`.
- [ ] The manifest registry source revision matches the generated index.
- [ ] Current configs, benchmarks, and reviewed-example catalogs pin `1.0.0`.
- [ ] Historical draft audit records remain labelled with their original
      revision.
- [ ] Expected counts and every required public repository artifact match.
- [ ] All manifest-defined gates pass on Python `3.9` and `3.12`.
- [ ] Compatibility, migration, governance, support, security, and release
      documentation match the source state.
- [ ] No credential, private source, generated secret, or unauthorized asset is
      included.
- [ ] Release notes distinguish stable specification from implementation
      conformance and external review.

## Publication sequence

1. Verify the exact source state in a clean checkout.
2. Commit it to the default branch.
3. Run CI and confirm every matrix job passes.
4. Set manifest `status` to `released` and `release_date` to the publication
   date in the release commit.
5. Create annotated tag for the current release, for example `v1.1.1`, from the verified commit.
6. Publish release notes from `CHANGELOG.md`.
7. Confirm the archive contains the required artifacts and no secrets.

The tag, release notes, and manifest must describe the same source state.

## Post-release changes

Compatible clarification and additive work targets 1.x. A change that breaks a
normative contract, active identifier, schema, or protocol requires a 2.0
migration path. Independent external review remains welcome and must be
recorded honestly rather than retroactively attributed to the internal
stability review.
