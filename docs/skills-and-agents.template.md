# Skills & Agents

All available skills and specialized agents for this project. **Project-owned:** extend this file as you add skills and agents. Full instructions live in `.claude/` — this registry routes every AI tool (Claude Code discovers them natively; other tools read the linked files directly).


## Skills

**Job skills** (slash commands for runnable tasks):

| Skill | Purpose |
|-------|---------|
| [`/setup`](../.claude/skills/setup/SKILL.md) | Initial aiDocs setup in a project (interview form) |
| [`/update-aidocs`](../.claude/skills/update-aidocs/SKILL.md) | Pull upstream aiDocs standard updates |
| [`/validate-docs`](../.claude/skills/validate-docs/SKILL.md) | Validate doc structure (forked) |
| [`/maintain`](../.claude/skills/maintain/SKILL.md) | Dispatch maintenance jobs (`change`: diff-scoped pre-PR; `full`: cycle-end) |

**Convention skills** (slash commands + auto-triggered):

| Skill | Purpose |
|-------|---------|
| [`/documentation`](../.claude/skills/documentation/SKILL.md) | Documentation writing rules |

> Add your project's skills here (auto-triggered skills: state the trigger instead of a slash command)


## Agents

Full instructions in `.claude/agents/<name>.md`. Claude Code runs them forked; other tools read and follow the file inline.

| Agent | Purpose | Skill |
|-------|---------|-------|
| [`code-analysis`](../.claude/agents/code-analysis.md) | Interpret the auto-generated code-index analysis report | — |
| [`issue-writer`](../.claude/agents/issue-writer.md) | GitHub issue creation with correct type, labels, project fields | — |
| [`validation-docs`](../.claude/agents/validation-docs.md) | Validate docs quality (judgment half; script does structure) | `/validate-docs` |
| [`validation-llm`](../.claude/agents/validation-llm.md) | Test docs effectiveness via LLM knowledge test | — |

> Add your project's agents here (database, devices, UI patterns, test writers, ...)


## Method Stack

aiDocs documents the project; it prescribes no development workflow. How work is organised, when the human is asked, code review, testing discipline and PR shape belong to the method stack. Its skills are not listed here — the stack routes itself. The one aiDocs gate it must honour is the pre-PR contract in [AGENTS.md](AGENTS.md#before-opening-a-pr).

| Stack | Installed as | Entry point |
|-------|--------------|-------------|
| [e.g. pstack, or "none"] | [e.g. Claude Code plugin, user-level] | [e.g. `/poteto-mode`] |


**Last Updated:** YYYY-MM-DD
