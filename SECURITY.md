# Security policy

## Supported versions

NexCanvas is currently a technical preview.

| Version | Supported |
|---|---|
| `0.1.x` | Yes |
| Unreleased `main` | Best effort |
| Older snapshots | No |

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
severity, coordinate a fix and disclosure timeline, and credit the reporter unless
anonymity is requested.

## Security-sensitive areas

Asset downloads, archive extraction, SVG parsing, file-path resolution, repository
inspection, generated XML, and agent-provided inputs require particular care.
Security fixes may intentionally break compatibility when preserving compatibility
would leave users exposed.
