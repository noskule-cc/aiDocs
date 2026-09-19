# AI Agent Guidelines

**Audience:** AI coding assistants (LLMs) working on this project

Behavioral instructions and workflow for AI assistants. Fixed standard file — do not edit; project-specific skills and agents are listed in [skills-and-agents.md](skills-and-agents.md).


## MANDATORY READING

**You MUST read the following files BEFORE starting any task:**

- This file (AGENTS.md) - workflow and situational references
- [INDEX.md](INDEX.md) - documentation map
- [coding-guidelines.md](coding-guidelines.md) - The Coding workflow you have to follow
- [skills-and-agents.md](skills-and-agents.md) - available skills and specialized agents
- Wiki index (if exists) - see [wiki.md](wiki.md) for location


## Situational References

Read these **when you reach that situation**, not upfront:

| When you're...          | Read...                       |
|-------------------------|-------------------------------|
| Finding platform docs   | `INDEX.md`                   |
| Setting up / installing | `installation.md`            |
| Writing code            | `architecture-rules.md`, `development.md` |
| Triaging a bug / locating a feature | `feature-map.md` (if it exists) |
| Writing tests           | `testing.md`                 |
| Writing documentation   | `DOCUMENTATION_GUIDELINES.md` |
| Validating docs         | `.claude/agents/validation-docs.md` |
| Testing docs for LLMs   | `.claude/agents/validation-llm.md` |
| Starting a task         | `coding-guidelines.md`        |
| Creating skills/agents  | `CREATING_AGENTS.md`          |
| Creating GitHub issues  | `issue-tracker.md`            |
| Running a job           | `tools/jobs.md`               |
| Syncing design ↔ code   | `design-sync.md`              |
| Unsure about approach   | Ask the user                  |

**Project-specific situations** (threat model, special test docs, ...) are listed in [project-index.md](project-index.md), if it exists — never add rows to the table above.

**Don't know which doc?** Check [INDEX.md](INDEX.md) for section headers.

How files are loaded — mandatory reads first (sequential), then situational reads on demand:

```mermaid
flowchart TD
    START([Session Start]) --> M1

    subgraph startup ["Always Read (startup, in order)"]
        M1["1. AGENTS.md"] --> M2["2. INDEX.md"]
        M2 --> M3["3. coding-guidelines.md"]
        M3 --> M4["4. skills-and-agents.md"]
        M4 -.->|if exists| M5["5. Wiki index"]
    end

    M4 --> SIT{{"What situation?"}}

    SIT -->|"Writing code"| CODE["architecture-rules.md<br>development.md"]
    SIT -->|"Triaging a bug"| TRIAGE["feature-map.md"]
    SIT -->|"Writing tests"| TEST["testing.md"]
    SIT -->|"Writing docs"| DOCS["DOCUMENTATION_GUIDELINES.md<br>INFORMATION_MINIMALISM.md"]
    SIT -->|"Setting up"| SETUP["installation.md"]
    SIT -->|"Validating docs"| VDOC[".claude/agents/validation-docs.md"]
    SIT -->|"Creating agents"| AREADME["CREATING_AGENTS.md"]
    SIT -->|"Running a job"| JOBS["tools/jobs.md"]
    SIT -->|"Unsure"| USER(["Ask the user"])

    %% Stroke only - never fill/color. A hardcoded fill is a light-mode
    %% assumption: the renderer's dark theme still supplies a light label
    %% color, and the label washes out. Strokes read in both themes.
    classDef always stroke:#2e7d32,stroke-width:3px
    classDef optional stroke:#f9a825,stroke-width:3px,stroke-dasharray:5 3
    classDef conditional stroke:#1565c0,stroke-width:3px
    classDef decision stroke:#616161,stroke-width:2px

    class M1,M2,M3,M4 always
    class M5 optional
    class CODE,TRIAGE,TEST,DOCS,SETUP,VDOC,AREADME,JOBS conditional
    class SIT decision
```

Green outline = always read | Yellow dashed = read if exists | Blue outline = read when situation occurs


## Before Opening a PR

Whatever workflow or method stack drives the task, these must be true before a PR opens:

- **Discoveries captured** — reusable technical knowledge from the session (API quirks, workarounds, how external systems actually behave) is on the wiki
- **Docs updated** — `changelog.md`, plus docs and wiki per [DOCUMENTATION_GUIDELINES.md](DOCUMENTATION_GUIDELINES.md), with the Information Minimalism test applied
- **Maintenance run** — `/maintain change` ran on the branch diff and its findings are fixed (registry: [tools/jobs.md](tools/jobs.md))

This contract states outcomes only. How the work is organised, reviewed, tested, and how the PR is shaped belongs to the workflow in use.


## Skills and Sub-Agents

Two kinds of specialized instructions:

- **Skills** (`.claude/skills/`) — lightweight, auto-triggered or invoked as slash commands
- **Agents** (`.claude/agents/`) — heavy, self-contained tasks with verbose output; each file carries its complete instructions (Claude Code runs them forked; other tools read and follow the file inline)

**Which skill or agent fits the task?** Check [skills-and-agents.md](skills-and-agents.md) — it lists every available skill and agent with its trigger and routes any AI tool to the instruction files.

> **Setup:** See [CREATING_AGENTS.md](CREATING_AGENTS.md) for how to create and register skills and agents.


**Last Updated:** 2026-09-19
