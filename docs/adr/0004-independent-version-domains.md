# ADR 0004: Version product and schemas independently

- Status: accepted
- Date: 2026-09-09

## Decision

The NexCanvas release uses Semantic Versioning independently of JSON schema,
provider-pack, and generated-artifact versions. Product `0.1.0` may therefore use
contract schema `2.0` and Microsoft icon pack `V24`.

## Consequences

Release automation must update product version files only. Schema-major changes
require explicit migrations and do not automatically dictate the product major.
