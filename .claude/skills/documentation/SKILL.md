---
name: documentation
description: Documentation writing following Information Minimalism. Use when creating or updating docs.
argument-hint: ""
---

Follow these rules when writing or updating documentation.

## Before Writing

Run the 3-question Information Minimalism test (`docs/INFORMATION_MINIMALISM.md`):

1. Would a skilled developer need this? (No → don't write it)
2. Is it obvious from structure, code or naming? (Yes → don't write it)
3. Does it duplicate existing content? (Yes → reference, don't duplicate)

## Placement Rules

| Content type | Location |
|-------------|----------|
| Intent, rationale, edge cases | Code comments / docstrings |
| Developer operations, platform guides | `docs/` |
| How software functions, domain concepts | Wiki |

## When Writing New Docs

1. Apply the 3-question test
2. Determine correct location using placement rules
3. Write the content
4. Update the relevant index (INDEX.md, [platform]-index.md, or wiki sidebar)
5. Add `**Last Updated:** YYYY-MM-DD` at the bottom

## When Updating Existing Docs

1. Read existing content first
2. Make targeted changes — don't rewrite surrounding text
3. Update the Last Updated date
4. Check if index entries still match

## Wiki Pages

A wiki page describes the feature for any platform (`docs/DOCUMENTATION_GUIDELINES.md`, "Structure: Behavior, Rationale, Components"):

1. Sections in the standard order: What It Does, Why It Matters, How It Works, On Screen / After the Session, Caveats, Open Questions, Implementation, Related
2. No per-OS sections, no class or API names in the behaviour sections; `## Implementation` names **roles** and what only each role knows; a platform quirk goes inline, marked `PLATFORM:`
3. Diagram what prose makes hard to hold: a state diagram for a lifecycle with more than three states, a flowchart for a decision loop, a flow diagram for data across more than two roles; Mermaid with strokes only, never fills
4. State current behaviour; history goes to the changelog and the issues, with one linked sentence on why a decision changed
5. Numbers and limits carry their reason; evidence lives on one page and is linked from the others

## Sentence Style

These rules decide **whether** and **where** to write. Sentence-level style is not theirs: if a writing skill is installed (e.g. `technical-writing`, `unslop`), apply it to the prose.

## Full reference

`docs/DOCUMENTATION_GUIDELINES.md`
