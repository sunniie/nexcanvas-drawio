# Asset and logo policy

## Resolution order

1. Exact official provider-pack SVG for a concrete cloud service.
2. Exact user-supplied SVG with confirmed usage rights.
3. Exact catalog entry pinned to a provider/version.
4. Exact installed Draw.io library shape when deterministic across the target runtime.
5. Clearly generic native semantic glyph with a text label.
6. `NeedsManual` and a transparent delivery limitation.

Never substitute a related brand, redraw a logo from memory, scrape arbitrary image-search results, or leave a remote image URL in the final `.drawio`.

## Catalog workflow

Search:

```bash
nexcanvas asset search "<technology or alias>"
```

Review the returned title, provider, slug, aliases, and intended product. Sync only after confirming it matches the modeled resource:

```bash
nexcanvas asset sync <project-dir> <catalog-key>
```

Simple Icons entries are pinned by version and downloaded from the configured immutable package URL. The manifest stores source URL, local path, SHA-256, license, and trademark notice.

For Azure, AWS, and Google Cloud services, use the official provider workflow in [provider-icon-packs.md](provider-icon-packs.md). Do not use Simple Icons or a generic cloud logo when an official service icon exists.

For a user-provided SVG:

```bash
nexcanvas asset sync <project-dir> <key> --user-svg <path> --title "<product>"
```

The validator rejects script/foreignObject content, event handler attributes, remote SVG references, invalid XML, and oversized files.

## Embedding and verification

The builder embeds file-backed SVG as a percent-encoded data URI so the diagram survives cloning, offline use, and host changes. It advances the manifest to `Embedded`. Only a successful render plus approved visual review may advance the asset to `RenderVerified` during postflight.

Native generic glyphs remain `Resolved` because there is no external file to sync. Their label must make the concept explicit.

## Trademark and clarity

Use a mark only for the product/service it represents and keep its geometry intact. A PostgreSQL mark cannot represent “any database”; an OpenAI mark cannot represent “any LLM”; an AWS service icon cannot represent a similarly named Azure/GCP service. When provider neutrality matters, prefer generic model/database/cloud glyphs.

Logos should support scanning, not dominate the architecture. Use consistent icon size, preserve contrast, and always retain the product name in text.
