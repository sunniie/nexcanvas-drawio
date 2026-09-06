# Brief-first intake

Start with the user's brief and diagram language. Reuse the conversation, repository,
documents and references before asking anything.

## Conversation

- If both brief and language are resolved, proceed immediately. Approval already given
  remains valid; do not request another approval for routine layout decisions.
- If language is missing, ask only which language the diagram should use. Do not infer
  English merely because service names are English.
- If the brief is missing, ask what system or process the user wants to communicate.
  Combine this with the language question when both are missing.
- For a conceptual design, propose reasonable roles and mark them as assumptions.
  For a diagram of an existing system, inspect its sources; do not invent behavior.
- Ask a focused content question only when a missing fact changes meaning or scope
  and cannot be resolved from evidence. Continue independent investigation meanwhile.
- Never present a diagram-type, information-depth, visual-style, canvas, or diagram-count
  questionnaire. Do not show preset samples as a mandatory selection step.
- Honor an explicit format, style, reference, orientation, or request for multiple views.
  Otherwise produce one editable diagram plus an embedded PNG preview, with no title
  or legend chrome unless it aids understanding.
- Treat a visual reference or named visual standard as persistent conversation context.
  Continue using its layout grammar, density, icon treatment, connector language and
  whitespace in later examples and revisions until the user explicitly changes it.
  Removing a style questionnaire must never reset an established visual authority.

Summarize the resolved brief briefly: what the diagram explains, main actors and
responsibilities, key relationships, language, and material assumptions. This is a
decision record, not a mandatory confirmation gate.

## Agent-owned design decisions

Determine the question the diagram answers, infer one dominant semantic intent
(`architecture`, `workflow`, `sequence`, `data-flow`, or `lifecycle`), then select
the internal route and notation beneath it. Never present the five intents as a
mandatory user menu. Read [semantic intents and repository evidence](semantic-intents-and-repository-evidence.md).
Internal profiles and QA presets are implementation details, not user choices.

Inventory entry points, ownership boundaries, active steps, passive resources, outputs,
and failure/feedback behavior relevant to the brief. Distinguish verified products
from generic concepts. Do not invent a target number of zones, nodes or steps.

Compare candidate compositions using the layout brainstorming reference. Choose:
- a short chain for a simple ordered process;
- parallel branches for independent work;
- a hub for actual centralized coordination;
- nested scopes for containment and ownership;
- rows or columns according to reading order, density and connector clearance.

Record why the chosen layout fits the content and why the runner-up is weaker.
Adapt canvas dimensions to readable content. Use official assets only for named
products and native shapes for internal concepts. References guide visual grammar,
never dictate topology.

## Before delivery

Check every important connector as source -> target, meaning, and authority.
Separate request/response and success/retry when both matter. Keep independent
ports and lanes distinct; keep labels clear of shapes and unrelated lines.

Run contract and geometry QA, render, inspect at delivery size and enlarged terminals,
repair any defects, then record visual approval and run postflight. Never claim
visual verification from XML or a successful export alone.

## Example conversations

Brief: "One coordinator and several specialist agents. English."
Action: proceed; infer the agent-orchestration route, choose a composition after
examining delegation and return paths, and mark unspecified roles as assumptions.
Do not ask the user to choose a diagram category or palette.

Brief: "Draw our checkout from this repository, in Vietnamese."
Action: inspect actual checkout code, select relevant interactions and errors,
then build one view. Ask only if the repository leaves a material scope ambiguity.

Brief: "Draw a system."
Action: ask what system/process and which diagram language; there is no meaningful
content to lay out yet.

Brief: "Make the attached diagram monochrome, keep the content, English."
Action: preserve semantics and apply the explicit visual instruction without intake menus.
