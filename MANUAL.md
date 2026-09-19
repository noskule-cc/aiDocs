# Manual

How to use aiDocs day-to-day after installing it in your project. One page; every row links to the doc with the detail. File links point at the `*.template.md` sources in this repo — in your project they are the filled copies without the `.template` suffix.

The core inversion: **your AI assistant runs the framework, you steer at the checkpoints.** You rarely invoke anything yourself — the assistant reads [AGENTS.md](docs/AGENTS.md) and routes itself.


## Once — set up

1. Copy `docs/` and `.claude/` into your project (additive — nothing gets overwritten)
2. Run `/setup` — interview-form: project info, templates, method stack, version stamp

Details: [README Quick Start](README.md#quick-start).


## Daily — work

| You want to...      | You do...                                  | The assistant does...                                                                                                                                    |
|---------------------|--------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|
| Build a feature/fix | Describe the task                          | Works the way your method stack says (aiDocs ships none; [pstack](https://github.com/michael-denyer/pstack-claude) is the recommended one). Before the PR it meets the [pre-PR contract](docs/AGENTS.md): discoveries on the wiki, docs updated, `/maintain change` clean |
| File an issue       | "Create an issue for X"                    | `issue-writer` agent applies your [tracker conventions](docs/issue-tracker.template.md)                                                                    |
| Get docs written    | Nothing — the pre-PR contract requires it  | Applies [DOCUMENTATION_GUIDELINES.md](docs/DOCUMENTATION_GUIDELINES.md) and the [3-question test](docs/INFORMATION_MINIMALISM.md)                          |
| Check code health   | "Analyze the code structure"               | `code-analysis` agent interprets the [code-index](docs/tools/jobs.template.md) report                                                                     |

Slash commands and auto-triggering are Claude Code features; other AI tools (Copilot, Cursor, Codex) reach the same instructions through the [skills-and-agents registry](docs/skills-and-agents.template.md).


## Periodically — maintain

- `/validate-docs` — judgment checks: duplicated knowledge, stale content, wiki structure
- `python docs/tools/check-docs.py` — mechanical structural checks (CI runs this on push)
- `validation-llm` agent — can a fresh LLM navigate your docs and understand the project?
- `/update-aidocs` — pull upstream aiDocs changes; your project files are never touched


## Command index

| Command / agent        | Kind             | Purpose                                                  |
|------------------------|------------------|----------------------------------------------------------|
| `/setup`               | slash command    | Initial project setup (interview form)                   |
| `/update-aidocs`       | slash command    | Pull upstream standard updates                           |
| `/validate-docs`       | slash command    | Validate doc structure and consistency                   |
| `/documentation`       | slash command    | Documentation writing rules (also auto-applies)          |
| `issue-writer`         | agent            | Create issues per tracker conventions                    |
| `code-analysis`        | agent            | Interpret code-index report, recommend improvements      |
| `validation-docs`      | agent            | Judgment checks on docs (run by `/validate-docs`)        |
| `validation-llm`       | agent            | Test docs against a fresh LLM                            |
