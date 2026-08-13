# Example: EN GitHub Release Notes

## Task framing

- Language: English
- Content type: article
- Topic: technology
- Platform: GitHub
- Audience: maintainers and early adopters checking what changed before upgrading
- Intent: show bounded release notes for an additive specification release
- Author perspective: technical editorial
- Risk: medium
- Visual mode: none
- Sources: `rules/platform/github/foundation.md`, `CHANGELOG.md`, `release/manifest.json`

## Resolved modules

`core.writing-pipeline` -> `format.article.foundation` -> `topic.technology.foundation` -> `platform.blog.foundation` -> `platform.github.foundation` -> `language.en.foundation` -> source, human-signal, format, topic, platform, and editor reviewers.

## Evidence map

- Verified repository rule: GitHub release notes must preserve shipped changes, migration boundaries, verification status, and links that help readers act.
- Verified repository record: release manifests define counts, required artifacts, gates, limitations, and offline verification.
- Verified repository record: changelog entries distinguish added platform and tone behavior from implementation-conformance claims.
- Editorial inference: a concise release note is enough when the change is additive and has no breaking migration path.

## Context gate

The example uses only repository-local release and platform rules. It does not claim download counts, adoption, external review, or production outcomes. The source boundary is sufficient.

## Content design

- Reader promise: understand what the release adds and whether action is required.
- Working thesis: additive platform support should be announced with scope, verification, and limitations.
- Structure: summary -> highlights -> compatibility -> verification -> known limits.

## Final artifact

# Human Writing Rules 1.1.0

This release expands platform-specific guidance while keeping the stable `1.0.0` normative RFC profile intact.

## Added

- GitHub guidance for README files, release notes, issues, pull requests, discussions, and repository announcements.
- New platform modules for vc.ru, DEV Community, and newsletters.
- Reviewed examples that cover each newly registered platform.
- Russian README navigation alongside the existing English README.

## Compatibility

The release is additive. Existing active object IDs and public configuration values keep their meaning. Consumers that pin `spec_revision` and `registry_source_revision` can continue to resolve the exact module set used for earlier runs.

## Verification

The release should be verified with the manifest-defined offline gates:

```sh
npm run release:verify
```

No external review, adoption metric, or comparative quality result is claimed by these notes.

## Media decision

Decision: no visual. GitHub release notes need links, counts, and verification status more than an illustration.

## Source notes

- `rules/platform/github/foundation.md` supports release-note structure, repository links, verification status, and Markdown checks.
- `release/manifest.json` supports the offline gate boundary.
- `CHANGELOG.md` supports the added-change list.
- No external GitHub metric, adoption claim, or user outcome is used.

## Review result

- Reviewed revision: `en-github-release-notes-r1`.
- Source, language, human-signals, format, topic, platform, and editor reviewers: pass.
- GitHub check: release scope, compatibility, verification command, and limitations are explicit.
- Open blocker or major findings: none.
- Readiness: publication-ready as repository release notes.
