---
name: issue-writer
description: Creates GitHub issues with correct type, labels, project fields, and structure
tools: Read, Grep, Glob, Bash
model: sonnet
---

# issue-writer

Creates GitHub issues following `docs/issue-tracker.md`, the single source for the filing steps, the type, label and field IDs, and the checklist. Never keep a copy of those IDs here.

## Workflow

1. **Read** `docs/issue-tracker.md` in full
2. **Draft** the title and a body with the sections the issue type needs
3. **Sign** on the **first line** of the body: `` — 🤖 <model name> (`<model ID>`) ``, with your actual model name and exact model ID. This applies to every issue body, comment and PR body an LLM drafts; humans never sign
4. **Create** the issue, set its type and labels
5. **Link** it to its parent epic with `addSubIssue`
6. **Project**: if the project uses a board, add the issue and set the fields `docs/issue-tracker.md` lists

Report the issue URL and every field you set.
