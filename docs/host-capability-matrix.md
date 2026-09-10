# Host capability and conformance matrix

Suite: `nexcanvas-core-2026.09`. A `verified` state requires observed execution evidence; fixtures never change host status.

| Host | Published state | Execution | Discovery paths | Verified cases | Limitations |
|---|---|---|---|---|---|
| OpenAI Codex | **not-run** | automated-cli | `.agents/skills/nexcanvas-drawio`<br>`$HOME/.agents/skills/nexcanvas-drawio`<br>`$CODEX_HOME/skills/nexcanvas-drawio`<br>`~/.codex/skills/nexcanvas-drawio` | None | Tool availability and approval policy vary by Codex environment. |
| GitHub Copilot | **not-run** | manual-export | `.github/skills/nexcanvas-drawio`<br>`.agents/skills/nexcanvas-drawio` | None | GitHub, IDE, coding-agent, and CLI surfaces can expose different tools and permissions. |
| Claude Code | **not-run** | automated-cli | `.claude/skills/nexcanvas-drawio` | None | Tool permissions, model selection, and project trust settings affect execution. |
| Compatible Agent Skills host | **not-run** | manual-export | `host-defined skill directory` | None | Discovery, invocation, and tool permissions are host-defined until a dedicated adapter is published. |

Local availability is diagnostic only. It is not proof that a host completed the NexCanvas workflow.
