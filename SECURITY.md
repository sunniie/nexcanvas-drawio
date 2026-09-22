# Security policy

## Supported versions

| Version | Supported |
|---|---|
| Latest `1.x` minor | Security and correctness fixes |
| Previous `1.x` minor | Security fixes for 90 days after the next minor release |
| `0.x` technical previews | No |
| Unreleased `main` | Best effort |
| Other snapshots | No |

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub's private
[security advisory form](https://github.com/sunniie/nexcanvas-drawio/security/advisories/new)
and include:

- affected version or commit;
- impact and realistic attack path;
- reproduction steps or a minimal proof of concept;
- suggested mitigation when known;
- whether public disclosure has already occurred.

The maintainer will acknowledge a complete report as soon as practical, assess
severity, coordinate a private fix and disclosure timeline, and credit the
reporter unless anonymity is requested. A security release may shorten the normal
deprecation window when compatibility would preserve the vulnerability. Release
notes will identify affected versions, mitigation, the fixed version, and any
required migration without disclosing exploit details prematurely.

## Security-sensitive areas

Asset downloads, archive extraction, SVG parsing, file-path resolution, repository
inspection, generated XML, and agent-provided inputs require particular care.
Security fixes may intentionally break compatibility when preserving compatibility
would leave users exposed.
