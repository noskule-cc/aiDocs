# Working on this repository

This repo **is** the aiDocs standard. Everything under `docs/` and the `.claude/` skill/agent templates is **product content** shipped to consuming projects — not instructions for working here.

- Do **not** follow `docs/AGENTS.md`, `docs/DOCUMENTATION_GUIDELINES.md`, etc. as your own workflow. Edit them as deliverables.
- Instructions for working on this repo live only in this file.

## Repo conventions

- **Issues:** plain GitHub issues, no Projects v2 board. Issue types are unavailable (user-owned repo) — classify with labels. Put the estimate in the issue body. AI agents sign posts per rule 11 in `docs/issue-tracker.template.md`.
- **File naming:** see the File Naming rule in `docs/DOCUMENTATION_GUIDELINES.md` — UPPERCASE = fixed standard files, lowercase = project-specific content, `*.template.md` = copy-and-fill templates.
- **Checks before committing docs:** `npx markdownlint-cli2 "**/*.md"` and `python docs/tools/check-docs.py` — CI runs both on every doc-touching push/PR.

## Standard-change checklist

Any change to the standard **set** — adding, renaming, or retiring a doc, template, skill, or agent — must propagate everywhere the set is mirrored. Definition of done:

- [ ] `docs/INDEX.md` — entry added/updated/removed
- [ ] `docs/AGENTS.md` — situational-reference row, if the file answers a situation
- [ ] `.claude/skills/setup/SKILL.md` — instantiation list and interview, if per-project
- [ ] `docs/tools/check-docs.py` — `PER_PROJECT` set and any rule that names files
- [ ] `docs/tools/jobs.template.md` — registry row, if runnable
- [ ] `docs/skills-and-agents.template.md` — registry row, if a skill or agent
- [ ] `README.md` — Project Structure tree and feature lists
- [ ] `/update-aidocs` ownership — casing signals the update contract (UPPERCASE / `*.template.md` = upstream-owned)

`check-docs.py` enforces the mechanical half (every shipped template referenced from `INDEX.md` and the setup skill; skills/agents registered). The rest is this checklist — run through it in the PR description.
