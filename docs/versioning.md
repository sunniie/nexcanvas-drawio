# Versioning and releases

## Independent versions

NexCanvas uses separate version domains:

| Domain | Example | Meaning |
|---|---|---|
| Product | `0.1.0` | Skill, CLI, compiler, documentation, and QA behavior |
| Contract schema | `2.0` | Persisted JSON structure and validation rules |
| Provider pack | `V24` | Upstream icon-pack identity |
| Generated artifact | hashes | Exact inputs and outputs for one project build |

A schema version must never be used as the product release version.

## Product releases

Product releases follow Semantic Versioning:

- patch: backward-compatible fixes;
- minor: backward-compatible capabilities;
- major: incompatible public-contract changes.

Versions below `1.0.0` are technical previews. Breaking changes still require
clear release notes and migration support for persisted user projects.

Pre-releases use `alpha`, `beta`, and `rc`, for example `0.5.0-alpha.1`.

## Release process

1. Merge conventional feature and fix pull requests into an always-releasable
   `main` branch.
2. Release Please maintains a reviewed release pull request and changelog.
3. Merge the release pull request only after the required CI gate passes.
4. Automation creates an immutable `vX.Y.Z` tag and GitHub Release.
5. Attach a repository bundle and `SHA256SUMS.txt`.
6. Verify tag, release notes, assets, and checksums from GitHub.

For fully automatic validation of Release Please pull requests, configure the
repository secret `RELEASE_PLEASE_TOKEN` with a narrowly scoped fine-grained token
or GitHub App token that can write contents, pull requests, and issues. Pull requests
created with the fallback `GITHUB_TOKEN` may not trigger another workflow run. In
that case, a maintainer must run the `CI` workflow manually against the release
branch before merge; the required quality gate is never bypassed.

The initial `v0.1.0` release is a technical-preview baseline. `version.txt`, the
Python `__version__`, the release manifest, tag, and GitHub Release must agree.

## Commit and pull-request titles

Use Conventional Commit form for squash-merge titles:

```text
feat(sync): add semantic repository diff
fix(routing): separate independent fan-in lanes
docs(contributing): document visual regression evidence
feat(schema)!: introduce semantic model V3
```

Documentation, CI, test, and chore changes do not need to force a release unless
they materially change the distributed skill behavior.

## Release gates

A release is blocked until:

- the stable CI quality gate passes;
- skill and contract validation pass;
- reference projects pass postflight;
- user-visible behavior and known limitations are documented;
- migrations exist for changed persisted contracts;
- packaged artifacts and their checksums are produced.
