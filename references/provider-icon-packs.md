# Official provider icon packs

NexCanvas stores the exact icons used by a diagram inside that diagram project and embeds them as SVG data in the generated `.drawio`. This avoids remote-image failures after a skill is cloned into GitHub Copilot or another host.

## Microsoft Azure

The Microsoft Azure mapping is pinned in `config/provider-icon-packs.json` to Architecture Icons V24. Review Microsoft's terms, then sync only the services used by the project:

```bash
nexcanvas asset sync <project-dir> azure-functions --provider microsoft-azure-official --accept-terms
nexcanvas asset sync <project-dir> azure-ai-search --provider microsoft-azure-official --accept-terms
nexcanvas asset sync <project-dir> microsoft-foundry-models --provider microsoft-azure-official --accept-terms
```

The resolver downloads the official ZIP, finds the exact mapped SVG filename, validates the SVG, copies it into `assets/icons/microsoft-azure-official/`, records its hash and terms URL, and embeds it during build.

For deterministic or air-gapped use, download the official ZIP once and pass it explicitly:

```bash
nexcanvas asset sync <project-dir> azure-functions --provider microsoft-azure-official --source-archive <Azure-icons.zip> --accept-terms
```

## AWS and Google Cloud

Download the current official icon ZIP from the provider page, then use filename discovery against the local archive:

```bash
nexcanvas asset sync <project-dir> "AWS Lambda" --provider aws-official --source-archive <AWS-icons.zip> --accept-terms
nexcanvas asset sync <project-dir> "Cloud Run" --provider google-cloud-official --source-archive <Google-Cloud-icons.zip> --accept-terms
```

Provider-owned packages change structure over time, so AWS and Google Cloud use archive discovery instead of pretending a stale embedded filename catalog is current. If multiple similar filenames exist, inspect the resolved manifest entry before build.

## Non-negotiable asset rules

- Never redraw, recolor, stretch, crop, rotate, or substitute a provider icon.
- Put the provider's current product name close to the icon.
- Do not use a provider service icon to represent a custom application or a generic concept.
- Use generic native shapes for abstract systems and external actors.
- Keep every resolved SVG local to the project and require `Synced`, `Embedded`, or `RenderVerified` manifest state before delivery.
- Review the provider's current terms yourself; `--accept-terms` records an explicit workflow decision, not legal advice.
