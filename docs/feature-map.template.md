# Feature Map

Routing table for triage. Bug reports speak feature language ("scanning hangs when the gateway is offline"); this file maps it to the code entry point where reading starts. The mapping earns documentation because it is **not derivable from code** in a layer-organized codebase — a feature smears across all layers.

## Rules

- One row per user-facing feature. Skip features whose location is obvious from structure or naming (minimalism Q2, applied per row).
- **No file inventories** — they rot fast and duplicate grep. Agents trace from the entry point.
- Behavior and rationale live on the wiki feature page — link, never restate.
- How to launch and drive a feature lives in the project's verification skill (`.claude/skills/verify-*/`), if one exists — link, never restate. Gotchas here stay code-level: invariants and symptom hints.
- Entry points must be grep-able identifiers; `check-docs.py` fails CI when one no longer resolves in the source tree.

## Features

| Feature | Entry point | Gotchas & failure modes | Behavior |
|---------|-------------|-------------------------|----------|
| [One-line user-facing description] | `[ClassName.method]` | [Non-obvious invariants; symptom hints, e.g. "offline errors surface as timeout, not connection-refused"] | [wiki: features-x] |

**Last Updated:** [date]
