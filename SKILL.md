---
name: drawio
description: Always use when user asks to create, generate, draw, or design a diagram, flowchart, architecture diagram, ER diagram, sequence diagram, class diagram, network diagram, mockup, wireframe, or UI sketch, or mentions draw.io, drawio, drawoi, .drawio files, or diagram export to PNG/SVG/PDF.
---

# NexCanvas Draw.io Skill

Generate draw.io diagrams as native `.drawio` files. Optionally export to PNG, SVG, or PDF with the diagram XML embedded (so the exported file remains editable in draw.io), or generate a browser URL that opens the diagram directly in the draw.io editor.

## Run collaborative intake before drawing

Do not jump from a new workflow request directly into XML. For any request with material choices about audience, abstraction, scope, or language, run the intake in [references/intake-and-discovery.md](references/intake-and-discovery.md) first.

1. Reuse facts already present in the prompt, repository, attachments, and conversation. Never ask the user to repeat known information.
2. Choose diagram type first. When it is unresolved, show `assets/examples/architecture-overview.png` and `assets/examples/detailed-request-flow.png`, then ask for **Architecture Overview**, **Detailed Request Flow**, or both.
3. Choose visual style second. When it is unresolved, show `assets/examples/architecture-overview.png` as the **Color Visual** sample and `assets/examples/compact-monochrome-system-flow.png` as the **Compact Monochrome** sample, then ask for either style or a supplied reference. Explain that the sample subject and component count are not reusable templates.
4. Use the available local-image tool to display previews. If image display is unavailable, provide clickable paths and one-sentence descriptions. Keep the intake to at most three numbered questions by asking type, style, and language plus audience/use; ask for source material only when it has not already been supplied.
5. Inspect the chosen source before proposing structure. Return a concise diagram brief containing the selected `type × style` profile, real boundaries, proposed zones/tracks, primary events, dependencies, authorities, icon plan, output format, and unresolved assumptions.
6. Pause for confirmation when a new user's choice would materially change the content or composition. If the user explicitly says to decide autonomously or draw immediately, state the inferred brief and proceed without an extra approval round.
7. Derive every boundary, component group, track, and sequence badge from the subject. Never reuse the component count, five-column rhythm, three-track layout, or step count from an example merely because it looks balanced.

## Classify workflow diagrams before drawing

For workflow, architecture, integration, and system-flow requests, choose one mode before planning the canvas:

- Use **Architecture Overview** for README, slide, portfolio, executive explanation, system map, ownership boundary, or high-level dependency requests.
- Use **Detailed Request Flow** for an endpoint, user interaction, state transition, failure analysis, debugging path, or implementation-level request.
- When the user explicitly names a mode, honor it. Otherwise use the collaborative intake previews instead of silently choosing between two materially different artifacts. Infer without pausing only when the user explicitly delegates the choice or the request is already structurally unambiguous.
- When the user requests both modes, produce separate diagrams that share the same palette, component names, icon vocabulary, and source snapshot.

Read [references/workflow-types.md](references/workflow-types.md) and [references/visual-contract.md](references/visual-contract.md) whenever either workflow mode applies. Do not force this taxonomy onto ERDs, class diagrams, sequence diagrams, wireframes, or unrelated diagram types.

## Select visual style after workflow mode

Treat information depth and visual style as separate decisions. Architecture Overview and Detailed Request Flow can both use the default colorful technical-card grammar, a user-supplied reference, or the **Compact Monochrome System Flow** grammar in [references/compact-monochrome-style.md](references/compact-monochrome-style.md).

Read [references/style-catalog.md](references/style-catalog.md) whenever the user must choose a visual style or asks to browse templates. Record the final pair explicitly, such as `Detailed Request Flow × Color Visual`.

- When the user supplies a reference, analyze it before drawing and follow its visual grammar unless doing so would make the content inaccurate or unreadable.
- When the user asks for a monochrome, academic, compact, relationship-led, or labeled system flow, read and apply the compact monochrome reference.
- Ask about style only when no reference or preference is available and the choice would materially change the artifact. Combine it with the artifact question so intake remains short.
- Never infer that a raster reference came from Draw.io. State uncertainty about its authoring tool, then reproduce compatible geometry natively in Draw.io.
- Do not copy the reference's component count, group count, or topology. Transfer visual rules, then derive the actual structure from the source system.

## Local enterprise QA customization

For workflow, architecture, integration, cloud, data-flow, ERD, sequence, or slide-ready diagrams, apply this local QA layer in addition to the upstream draw.io instructions.

Before delivering or exporting a diagram:

### Content-driven structure

Do not begin from a fixed visual template such as four horizontal sections or nine numbered steps. Derive the structure from the subject first:

1. Inventory the actual actors, systems, trust boundaries, data stores, supporting services, and meaningful transformations.
2. Group elements only where the group communicates a real boundary such as ownership, network zone, execution environment, lifecycle phase, or security scope.
3. Derive sequence numbers only after the topology is understood. Number events in the primary end-to-end journey; do not number passive data stores, parallel support services, observability, or decorative callouts unless they are genuine sequential steps.
4. Use as many sections and steps as the content requires. Never add empty sections, merge unrelated systems, or stretch the sequence merely to reach a predetermined count.
5. Before drawing, state the proposed sections and primary sequence in one concise sentence. If the grouping would materially change the meaning and the request is ambiguous, ask the user; otherwise proceed with the best-supported structure.

The quality of the content model takes priority over visual symmetry. A diagram with three meaningful zones and seven real events is better than a visually regular four-zone, nine-step template that distorts the system.

### Reference-led visual planning

After the content model is stable and before writing XML, derive the visual grammar in this order:

1. Treat user-provided reference diagrams as the visual authority. Extract their layer structure, card density, logo scale, line weight, badge style, palette, whitespace, title treatment, and legend placement before drawing.
2. Use official or verified logos for real technologies, cloud services, databases, gateways, frameworks, and observability tools. Use Draw.io-native semantic glyphs or small composed vectors for tasks and internal concepts such as upload, document, OCR, validation, decision, review, transform, scoring, search, queue, notification, and persistence.
3. Keep abstract processing steps compact, but add a task glyph when it materially improves recognition or breaks up a dense text-only rhythm. Do not present a semantic glyph as an official product logo, add an oversized pictogram to every leaf card, or turn a technical workflow into an infographic.
4. Use ImageGen only when no useful visual reference exists and art direction is genuinely missing. Never let an ImageGen composition override a reference supplied by the user.
5. Match information density to the selected mode: an Overview may use nested module cards and small service logos; a Detailed Request may use slim layer rails, logo-led technology cards, consistent event badges, and concise secondary text.
6. Before drawing a Detailed Request, write an interaction ledger. Give every independent HTTP request, local user action, background job, or state transition its own track prefix; never join them merely because they occur during one user session.
7. Audit authority and trust before polishing. Explicitly disclose where values are calculated, where they are only range-checked, which side is authoritative, which data is client-visible, and whether writes are transactional, best-effort, or capable of partial success.

At 100% zoom, the grouping, main route, real technology logos, and hierarchy must be immediately clear without inflating individual components.

### Shared visual contract for both workflow modes

1. Make visual weight follow semantic importance. Keep the primary workflow dominant; do not let a dependency dock, legend, title rail, or metadata panel become the strongest shape on the canvas.
2. Use title, subtitle, legend, source chip, or layer rail only when it strengthens the selected reference grammar. Keep them subordinate to the workflow, but do not remove useful structural chrome merely to maximize content area.
3. For Architecture Overview, avoid a dominant sidebar. For layered Detailed Request diagrams, a slim left title rail is encouraged when it names a real trust boundary or execution layer; keep it normally within 7-10% of canvas width.
4. Give repeated peer stages a visible rhythm through aligned header strips, consistent gutters, and deliberate card proportions. Use official logos for actual resources and technology components; use neutral Draw.io task glyphs for selected internal stages. Text-only cards remain valid when an icon adds no semantic value.
5. Integrate stage numbers into headers for Architecture Overview. For Detailed Request Flow, use identical event badges and separate interaction tracks instead of presenting multiple HTTP requests as one false sequence.
6. Keep return paths short and local. A response connector must use the nearest clear lane and must not frame the canvas unless the detour communicates a real hop.
7. Use restrained, clean technical colors over white or very pale boundary fills: blue for access/request, dark navy for internal processing, green for data/persistence, violet for response/agent routing, orange for telemetry or optional services, and red only for errors. Keep logos vivid and text high-contrast; avoid both gray washout and oversized saturated panels.
8. Preserve both the editable `.drawio` source and the embedded `.drawio.png` preview when the artifact is intended for a repository, README, design review, or technical documentation.
9. In Detailed Request diagrams, keep each track internally complete: named trigger, forward events, local dependencies, local failures, and the response/UI-update lane. Duplicate a shared UI endpoint across tracks when that prevents a false cross-request sequence.

1. Prefer real draw.io library icons or image icons for known platforms/components such as AWS, Azure, GCP, Kubernetes, Docker, Rancher, Grafana, Power BI, Superset, S3, Redis, PostgreSQL, Cosmos DB, SharePoint, or Service Bus.
2. Use plain rounded rectangles only for abstract business concepts, internal custom modules, or unknown proprietary services.
3. Add a compact legend when two or more connector semantics appear. Keep the legend in a thin footer or unobtrusive top area and make its samples exactly match the rendered line colors, dash patterns, widths, and arrowheads.
4. Keep at least 16 px padding inside boundaries and at least 12 px spacing between unrelated blocks.
5. Route connectors through empty gutters. Lines must not pass through text, icons, cards, databases, or container titles.
6. Do not use raw screenshots as the final workflow when the user asks for a clean workflow/architecture diagram. Redraw the flow as `.drawio` and export PNG/SVG if needed.
7. If an official logo cannot be verified or found, use a clean generic icon and clearly treat it as a generic representation. Never invent or substitute a neighboring brand. Task glyphs are semantic illustrations, not placeholders for brand identity.
8. Plan connector-label gutters before placing HLA cards. If a connector segment is shorter than its label, widen the gap, slightly resize the adjacent cards, or wrap the label; never accept clipped or hidden edge text.
9. For short connectors, prefer a standalone transparent text vertex instead of Draw.io's automatic edge label. Place it in a reserved clear pocket beside the route, keep it visually associated with exactly one connector, and use the connector color for the text. Tag it `qa-flow-label:<edge-id>` when the edge is also tagged `qa-labeled-flow`.
10. Keep connector labels close to their line: normally 6-12 px from the nearest segment and never floating more than about 20 px away without a clear reason. Place labels near the longest segment or a clean elbow, not over a component.
10a. Omit a connector label that merely repeats the source tool name, target component name, or an already obvious verb. Reserve labels for payloads, conditions, side effects, protocols, or actions that the two endpoints and arrow direction do not already communicate.
11. Keep at least 6 px clearance between a connector label and every adjacent card or boundary. Labels must not touch borders, overlap icons, or sit on top of another connector.
11a. Never leave an important Draw.io edge label at its automatic centered position. Give the label an explicit perpendicular offset large enough to clear the rendered glyph box, normally at least 14 px on a 1920×1080 canvas. Treat 6-12 px as the visible gap from the text edge to the connector, not the text baseline or center. If the route is too short for that clearance, reserve a wider label lane or use a transparent standalone text vertex.
11b. For paired request/response lines, place the request label outside one lane and the response label outside the opposite lane. Do not stack both labels in the space between the two connectors, and never let either connector touch its own text.
12. When several parallel flows exist, give each connector an independent lane and label position. Do not share vertical or horizontal segments unless the diagram explicitly represents a merge.
13. Verify long titles, repository names, and metadata remain inside their cards. Increase card height, wrap text, or reduce only the metadata font before shrinking normal body text.
14. When repository ownership is shown, put confirmed repo names inside the corresponding component card. Mark unconfirmed ownership as `TBD`; do not infer a repository from the service name alone.
15. Use a consistent corner-radius hierarchy. Make large system boundaries square (`rounded=0`) or nearly square; use only a light radius (`arcSize=3-5`) on their title strips; use a modest radius (`arcSize=6-10`) on component cards. Never combine a mildly rounded header with a heavily rounded content boundary.
16. Render connector annotations as transparent standalone text by default (`fillColor=none;strokeColor=none`). Do not use opaque white label boxes to mask lines. Offset each annotation 6-12 px beside the related segment so the connector does not run through the text.
16a. Use concise verb-led edge labels when the relationship itself matters, such as `Read history`, `Save score`, `Export JSON`, or `Return result`. Put responsibilities inside cards and transported actions or payloads beside connectors. Reserve a label gutter before routing; never place an annotation on a component, group title, arrowhead, or another line.
17. Keep orthogonal connectors straight (`rounded=0`) unless the user explicitly requests curved lines. Preserve at least 25-30 px of straight terminal line between the final 90-degree elbow and each arrowhead; add an explicit final waypoint when automatic routing would place the arrowhead directly on the bend.
18. When a request and response travel both ways, prefer two parallel one-way connectors with separate lanes and labels. Avoid a single bent connector with both `startArrow` and `endArrow` when it makes direction or arrowhead geometry ambiguous.
19. Size cards according to content density rather than making every card equal. Keep short queue/config/note nodes compact, allocate more width or height to dense processing nodes, reduce metadata text before body text, and remove oversized icon or whitespace areas.
19a. For a compact leaf containing one title and one short secondary line, start near 48-56 px high with 12-16 px horizontal padding, then expand only when the rendered text requires it. Measure the badge, title, body, and padding as a single content envelope; do not keep a 68-80 px card merely to preserve a uniform grid.
20. Plan the flow grid before sizing individual cards: reserve explicit connector gutters between major boundaries, give primary services width first, and move compact explanatory notes out of the main processing chain. Do not fix a crowded architecture by shrinking every card locally.
21. Run a visual density pass after routing. Confirm neighboring cards have intentional hierarchy, every title/body/footer stays inside its card, no low-information component consumes more space than a denser adjacent component without a structural reason, and every bent connector has a visible terminal shaft before its arrowhead.
22. Use the shortest valid connector route. If source and target are aligned and the gutter is unobstructed, connect them with one straight segment. A default connector should have no more than two elbows; every additional bend must avoid a real obstacle, cross a meaningful boundary, or encode an explicitly documented detour.
23. Reject micro-elbows and broken-looking arrowheads. Do not create waypoint segments shorter than 24 px merely to satisfy an entry constraint. Move the port, align the cards, or widen the gutter so the final shaft is visually continuous.
24. Align the last waypoint with the target port. For a left/right entry, the terminal segment must be horizontal and meet the component edge perpendicularly. For a top/bottom entry, it must be vertical. The arrowhead must point into the target component, never down or sideways along its border.
25. When routing a return path, use the nearest clear parallel lane. Do not send a connector around the canvas or through multiple boundaries unless the detour communicates a real network hop or avoids an unavoidable obstacle.
26. Right-size every component from its information density. Compact one- or two-line services into small cards; reserve large cards for dense responsibilities, nested replicas, tables, or sub-components. Repack the grid before increasing the canvas size.
27. Keep every numbered step badge visually identical across the diagram: same diameter, fill, stroke, font, and number alignment. Use a different badge color only when the legend explicitly defines a second semantic class; ordinary layer colors must not recolor the sequence badges.
27a. When an agent or capability boundary contains a real ordered internal lifecycle, prefer compact circular badges integrated into the leaf-card title row instead of decorative task glyphs. Reset `1…n` inside a clearly titled agent boundary, or use stable prefixes such as `P1`, `M1`, and `A1` when edges or prose refer across agents. Use `2A/2B` only for genuine parallel branches, and never number passive resources, stores, or optional dependencies.
27b. Before adding badges, prove the internal stages are sequential. A topology-only set of peer capabilities remains unnumbered. Once badges are used, tighten the cards around their actual one- or two-line content and spend the recovered space on wider connector and label gutters.
28. Strengthen scanability with deliberate contrast. Primary titles and step numbers should use dark, high-contrast text; major flow arrows should remain clearly visible at 100% zoom; boundary fills should be subtle without washing out component borders, labels, or logos.
29. Treat icon and logo selection as semantic metadata. Resolve a verified Draw.io library icon or stable embedded image for known technologies, validate that it actually renders, and fall back to a labeled generic symbol instead of leaving an empty image area.
30. During the final visual pass, trace every edge from source to target with a finger or cursor. Confirm the route has a reason, the arrowhead enters the intended component on the intended side, and no shorter equally clear route exists.
31. Validate the source attachment as strictly as the target attachment. The first visible shaft must begin at the component perimeter and travel outward; it must not originate near the center, run through the component interior, or make its first elbow inside the source card. Align the first waypoint with the configured `exitX`/`exitY` port and keep at least 25-30 px of straight line outside the source before the first bend.
32. Make perimeter attachment explicit for constrained connectors. Use `exitPerimeter=1;entryPerimeter=1;sourcePerimeterSpacing=0;targetPerimeterSpacing=0;` unless a documented gap is intentional. At 200% zoom, verify the source line begins exactly on the visible outline and the target arrow tip stops on the visible outline rather than floating short of it or penetrating into the fill. Be especially cautious with hexagons, clouds, cylinders, actors, and other non-rectangular perimeters.
33. Run a zone-utilization pass after card sizing. A semantically populated boundary should not contain large unused left or right fields while its components remain clustered in the middle. After reserving the title rail and connector gutters, distribute the functional groups across the usable width with intentional alignment and balanced side margins.
34. Do not solve unused space by inflating every card. Prefer, in order: moving compact support nodes toward a side margin, widening only a dense nested component, distributing peer cards evenly, introducing a meaningful sub-boundary or callout, and finally reducing the overall boundary/canvas size. Preserve compact cards while improving the composition of the group.
35. Keep document chrome proportional. Title/subtitle should normally stay within 8% of canvas height, a legend within 8%, metadata within 4%, and a Detailed Request layer rail within 10% of width unless the reference clearly requires otherwise.
36. Run a reference-fidelity pass after export. Compare the diagram beside the selected reference at the same apparent scale and check boundary hierarchy, card density, logo prominence, line language, badge signature, and whitespace before judging it complete.
37. Treat source accuracy as part of visual QA. Trace the actual implementation order, distinguish framework terminology that changed across versions, show security/runtime prerequisites that materially enable the path, and reproduce formulas, timeouts, status codes, and fallback ownership exactly.
38. Use an official verified logo only for the service it actually represents. If the exact product has no verified icon, use a neutral technology-family symbol or a clearly labeled generic glyph; never silently substitute a neighboring brand. Embed image data in the `.drawio` source and verify it renders after export rather than leaving a remote URL dependency.
39. Keep presentation body text at a readable size for the target canvas, normally 11-12 px on a 1920×1080 technical diagram. Reduce chrome and unused space before shrinking operational labels.
40. Run a semantic edge audit after geometry QA. For every important connector, verify `source → target`, operational meaning, authority, label, and line class together. A request label must remain on the request-direction edge; a response, callback, acknowledgement, retry, or feedback label must have its own correctly directed connector. Automated crossing and perimeter checks cannot prove this semantic direction.

After writing a `.drawio` file, run the local QA script. Pass the workflow mode when applicable:

Resolve `<DRAWIO_SKILL_DIR>` to the directory containing this `SKILL.md`, then run:

```bash
python <DRAWIO_SKILL_DIR>/scripts/drawio_qa.py DIAGRAM.drawio
python <DRAWIO_SKILL_DIR>/scripts/drawio_qa.py OVERVIEW.drawio --diagram-type overview
python <DRAWIO_SKILL_DIR>/scripts/drawio_qa.py DETAILED.drawio --diagram-type detailed
```

For workflow profiles, add Draw.io cell tags where they help automated QA: `qa-primary`, `qa-support`, `qa-stage`, `qa-title-rail`, `qa-metadata`, `qa-legend`, `qa-primary-flow`, `qa-response-flow`, `qa-data-flow`, `qa-error-flow`, `qa-labeled-flow`, `qa-flow-label:<edge-id>`, and `qa-sequence:<track>`. Use `qa-labeled-flow` when the connector's action or payload is necessary to understand the system; give the edge a concise inline label with explicit clearance, or associate one non-empty transparent text vertex through `qa-flow-label:<edge-id>`. Tag an intentional layered pictogram group with `qa-illustrative` only so overlap QA can distinguish its internal composition. Tag a page-sized export-forcing rectangle as `qa-background` so composition and crossing checks ignore it. Use `qa-layout-exempt` or `qa-density-exempt` only for a reviewed composition where the heuristic is demonstrably misleading, never to hide real whitespace. Tags are QA metadata and must not appear in rendered labels.

Fix every `ERROR` before delivery. Review every `WARNING`, especially warnings about known service/component labels rendered without an icon style.

Do not present an export as review-ready until the matching QA profile has no errors and all actionable warnings are resolved. An explicitly labeled early content draft may be shared when the user is reviewing scope, but it is not a final visual artifact.

The QA script checks XML parseability, overlapping boxes, connector segments crossing unrelated boxes, and likely real service/component labels that are drawn as plain boxes. This automated check does not replace visual review: always open/export and inspect the final PNG/SVG at 100% before sharing, specifically checking corner-radius hierarchy, transparent label placement, text clipping, connector lanes, straight orthogonal elbows, terminal arrow shafts, and component density.

For multi-page diagrams or nested swimlanes, the QA script may not account for page isolation or parent offsets. Validate the target page independently with child coordinates flattened in a temporary QA copy, then visually inspect the original exported page. Never alter the production diagram solely to satisfy a known false positive.

## How to create a diagram

1. **Generate draw.io XML** in mxGraphModel format for the requested diagram
2. **Write the XML** to a `.drawio` file in the current working directory using the Write tool
3. **Handle the requested output format**:
   - `png` / `svg` / `pdf` → locate the draw.io CLI (see [draw.io CLI](#drawio-cli)) and export with `--embed-diagram`. Keep the source `.drawio` when the user requests editable source or the artifact is for a repository, README, design review, or technical documentation; otherwise the embedded export may be delivered alone. If the CLI is not found, keep the `.drawio` file and tell the user they can install the draw.io desktop app to enable export, use `url` mode, or open the `.drawio` file directly
   - `url` → generate a browser URL from the XML and open it (see [Browser URL output](#browser-url-output)). Keep the `.drawio` file as a persistent local copy
   - *(no format)* → no extra step; the `.drawio` file is the output
4. **Open the result** — the exported file if exported, the browser URL if `url`, or the `.drawio` file otherwise. If the open command fails, print the file path (or URL) so the user can open it manually

## Choosing the output format

Check the user's request for a format preference. Examples:

- `/drawio create a flowchart` → `flowchart.drawio`
- `/drawio png flowchart for login` → `login-flow.drawio.png`
- `/drawio svg: ER diagram` → `er-diagram.drawio.svg`
- `/drawio pdf architecture overview` → `architecture-overview.drawio.pdf`
- `/drawio url flowchart for user login` → opens browser at `app.diagrams.net` with the diagram, keeps `login-flow.drawio` locally

If no format is mentioned, just write the `.drawio` file and open it in draw.io. The user can always ask to export later.

### Supported export formats

| Format | Embed XML | Notes |
|--------|-----------|-------|
| `png` | Yes (`-e`) | Viewable everywhere, editable in draw.io |
| `svg` | Yes (`-e`) | Scalable, editable in draw.io |
| `pdf` | Yes (`-e`) | Printable, editable in draw.io |
| `jpg` | No | Lossy, no embedded XML support |

PNG, SVG, and PDF all support `--embed-diagram` — the exported file contains the full diagram XML, so opening it in draw.io recovers the editable diagram.

## Browser URL output

When the user requests `url` format, generate a draw.io URL that opens the diagram directly in the browser editor at `app.diagrams.net` — no draw.io Desktop required.

### How it works

1. The `.drawio` file is written to disk as usual (gives the user a persistent local copy they can re-edit)
2. The XML is compressed with Node.js's built-in `zlib` and base64-encoded
3. The result is embedded in a `https://app.diagrams.net/#create=...` URL
4. The URL is opened in the default browser

This uses only Node.js built-in modules (`zlib`, `child_process`) — no external dependencies.

### URL generation

Run this `node -e` one-liner to read the `.drawio` file and print the URL (replace `DIAGRAM.drawio` with the actual filename):

```bash
URL=$(node -e '
const fs = require("fs");
const zlib = require("zlib");
const xml = fs.readFileSync(process.argv[1], "utf8");
const compressed = zlib.deflateRawSync(encodeURIComponent(xml)).toString("base64");
const payload = encodeURIComponent(JSON.stringify({ type: "xml", compressed: true, data: compressed }));
console.log("https://app.diagrams.net/?grid=0&pv=0&border=10&edit=_blank#create=" + payload);
' DIAGRAM.drawio)
```

The URL format matches the MCP Tool Server. Node.js's `zlib.deflateRawSync` and `pako.deflateRaw` both implement RFC 1951 and produce identical output, so URLs from either source are interchangeable.

### Opening the URL

| Environment | Command |
|-------------|---------|
| macOS | `open "$URL"` |
| Linux (native) | `xdg-open "$URL"` |
| WSL2 | Write a temp `.url` file, open via `cmd.exe` (see below) |
| Windows (native) | Write a temp `.url` file, open via `start` (see below) |

**Why the `.url` workaround on Windows/WSL2?** `cmd.exe`'s `start` command treats `&` as a command separator and strips everything after `#` in URLs. The diagram payload lives in the `#create=...` fragment, so passing the URL directly causes it to be silently lost. A `.url` shortcut file preserves the URL intact.

**macOS / Linux example:**

```bash
open "$URL"      # macOS
xdg-open "$URL"  # Linux
```

**WSL2 example:**

```bash
TMPFILE=$(mktemp --suffix=.url)
printf '[InternetShortcut]\r\nURL=%s\r\n' "$URL" > "$TMPFILE"
cmd.exe /c start "" "$(wslpath -w "$TMPFILE")"
```

**Windows (native) example:**

```cmd
echo [InternetShortcut] > %TEMP%\drawio.url
echo URL=%URL% >> %TEMP%\drawio.url
start "" "%TEMP%\drawio.url"
```

### After opening

Print the URL so the user can copy or share it, and confirm the local file path:

```
Opened in browser: <URL>
Local file: DIAGRAM.drawio
```

The `.drawio` file stays on disk so the user can re-edit it later, attach it elsewhere, or export it to an image format on demand.

### URL length

The URL embeds the full compressed diagram in its hash fragment. Very large diagrams may hit browser URL length limits (typically ~32K–2MB depending on the browser). For complex diagrams that exceed the limit, fall back to writing the `.drawio` file and opening it locally.

## draw.io CLI

The draw.io desktop app includes a command-line interface for exporting.

### Locating the CLI

First, detect the environment, then locate the CLI accordingly:

#### WSL2 (Windows Subsystem for Linux)

WSL2 is detected when `/proc/version` contains `microsoft` or `WSL`:

```bash
grep -qi microsoft /proc/version 2>/dev/null && echo "WSL2"
```

On WSL2, use the Windows draw.io Desktop executable via `/mnt/c/...`:

```bash
DRAWIO_CMD=`/mnt/c/Program Files/draw.io/draw.io.exe`
```

The backtick quoting is required to handle the space in `Program Files` in bash.

If draw.io is installed in a non-default location, check common alternatives:

```bash
# Default install path
`/mnt/c/Program Files/draw.io/draw.io.exe`

# Per-user install (if the above does not exist)
`/mnt/c/Users/$WIN_USER/AppData/Local/Programs/draw.io/draw.io.exe`
```

#### macOS

```bash
/Applications/draw.io.app/Contents/MacOS/draw.io
```

#### Linux (native)

```bash
drawio   # typically on PATH via snap/apt/flatpak
```

#### Windows (native, non-WSL2)

```
"C:\Program Files\draw.io\draw.io.exe"
```

Use `which drawio` (or `where draw.io` on Windows) to check if it's on PATH before falling back to the platform-specific path.

### Export command

```bash
drawio -x -f <format> -e -b 10 -o <output> <input.drawio>
```

**WSL2 example:**

```bash
`/mnt/c/Program Files/draw.io/draw.io.exe` -x -f png -e -b 10 -o diagram.drawio.png diagram.drawio
```

Key flags:
- `-x` / `--export`: export mode
- `-f` / `--format`: output format (png, svg, pdf, jpg)
- `-e` / `--embed-diagram`: embed diagram XML in the output (PNG, SVG, PDF only)
- `-o` / `--output`: output file path
- `-b` / `--border`: border width around diagram (default: 0)
- `-t` / `--transparent`: transparent background (PNG only)
- `-s` / `--scale`: scale the diagram size
- `--width` / `--height`: fit into specified dimensions (preserves aspect ratio)
- `-a` / `--all-pages`: export all pages (PDF only)
- `-p` / `--page-index`: select a specific page (1-based)

### Opening the result

| Environment | Command |
|-------------|---------|
| macOS | `open <file>` |
| Linux (native) | `xdg-open <file>` |
| WSL2 | `cmd.exe /c start "" "$(wslpath -w <file>)"` |
| Windows | `start <file>` |

**WSL2 notes:**
- `wslpath -w <file>` converts a WSL2 path (e.g. `/home/user/diagram.drawio`) to a Windows path (e.g. `C:\Users\...`). This is required because `cmd.exe` cannot resolve `/mnt/c/...` style paths.
- The empty string `""` after `start` is required to prevent `start` from interpreting the filename as a window title.

**WSL2 example:**

```bash
cmd.exe /c start "" "$(wslpath -w diagram.drawio)"
```

## File naming

- Use a descriptive filename based on the diagram content (e.g., `login-flow`, `database-schema`)
- Use lowercase with hyphens for multi-word names
- For export, use double extensions: `name.drawio.png`, `name.drawio.svg`, `name.drawio.pdf` — this signals the file contains embedded diagram XML
- After a successful export, keep the intermediate `.drawio` file for repository/documentation workflows or when editable source was requested; otherwise the exported file may stand alone because it contains the full diagram
- For `url` mode, keep the `.drawio` file (no double extension) — the URL is a view/edit handle and the local file is the persistent copy

## XML format

A `.drawio` file is native mxGraphModel XML. Always generate XML directly — Mermaid and CSV formats require server-side conversion and cannot be saved as native files.

### Basic structure

Every diagram must have this structure:

```xml
<mxGraphModel adaptiveColors="auto">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <!-- Diagram cells go here with parent="1" -->
  </root>
</mxGraphModel>
```

- Cell `id="0"` is the root layer
- Cell `id="1"` is the default parent layer
- All diagram elements use `parent="1"` unless using multiple layers

## XML reference

For the complete draw.io XML reference including common styles, edge routing, containers, layers, tags, metadata, dark mode colors, and XML well-formedness rules, fetch and follow the instructions at:
https://raw.githubusercontent.com/jgraph/drawio-mcp/main/shared/xml-reference.md

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| draw.io CLI not found | Desktop app not installed or not on PATH | Keep the `.drawio` file and tell the user to install the draw.io desktop app, use `url` mode instead, or open the file manually |
| Export produces empty/corrupt file | Invalid XML (e.g. double hyphens in comments, unescaped special characters) | Validate XML well-formedness before writing; see the XML well-formedness section below |
| Diagram opens but looks blank | Missing root cells `id="0"` and `id="1"` | Ensure the basic mxGraphModel structure is complete |
| Edges not rendering | Edge mxCell is self-closing (no child mxGeometry element) | Every edge must have `<mxGeometry relative="1" as="geometry" />` as a child element |
| File won't open after export | Incorrect file path or missing file association | Print the absolute file path so the user can open it manually |
| Browser opens with empty diagram in `url` mode | `cmd.exe` stripped the `#create=...` fragment | Use the `.url` temp-file workaround on Windows/WSL2 (see [Opening the URL](#opening-the-url)) — never pass the URL directly to `cmd.exe /c start` |
| URL is too long for the browser | Very large diagram exceeds browser URL length limit | Fall back to writing the `.drawio` file and opening it locally |

## CRITICAL: XML well-formedness

- **NEVER include ANY XML comments (`<!-- -->`) in the output.** XML comments are strictly forbidden — they waste tokens, can cause parse errors, and serve no purpose in diagram XML.
- Escape special characters in attribute values: `&amp;`, `&lt;`, `&gt;`, `&quot;`
- Always use unique `id` values for each `mxCell`
