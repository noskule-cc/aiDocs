# Issue Tracker

Project management using GitHub Issues and Projects v2.

## Conventions

Types, labels, and project fields are discoverable via the GitHub API. These rules aren't:

1. **Use issue types** for classification — not labels
2. **Use labels** for the feature area the issue touches
3. **Label the feature, not the data.** Most issues need one label
4. **Use the sub-issue feature** to link children to epics
5. **Add every issue to the project**
6. **Set Status** to Backlog unless otherwise stated
7. **Link prerequisites** with GitHub's native "blocked by" relation, never only in prose — the roadmap and "what's next" are built from it
8. **Title format** — imperative verb + concise description
9. **Update wiki** when closing issues that add significant functionality
10. **Sign as an agent** — if you are an AI agent, put your signature on the **first line** of every issue body, issue or PR comment and PR body you draft: `` — 🤖 <model name> (`<model ID>`) ``, with your actual model name and exact model ID. The posting account no longer tells who wrote it; humans never sign


## Board

Built for one developer working with AI agents: no time-boxed sprints, no estimates. Work is grouped by scope (a **Focus**), ordered by dependencies, and the board tells an agent what it may pick up next.

### Fields

| Field     | Type          | Options / purpose |
|-----------|---------------|-------------------|
| Status    | Single select | The built-in field, so GitHub's "Item closed" workflow sets Done. Columns below |
| Priority  | Single select | High, Medium, Low |
| Test kind | Single select | What a manual test needs, e.g. `[Device]` (a quick check, any time) and `[Real use]` (a real session of the product, e.g. a workout); name the options for the project |

Enable the project workflows **Item closed** (→ Done), **Item added to project** and **Auto-add sub-issues to project**.

### Status columns

| Column               | Means |
|----------------------|-------|
| **Backlog**          | Ideas, future work, unprioritized |
| **Refine**           | Needs refinement or a precondition before it is actionable |
| **Ready**            | Refined; actionable once nothing blocks it |
| **In Progress**      | Being worked on |
| **Waiting on owner** | Stopped on a decision only the owner can make; the issue holds the question as a numbered list |
| **Review**           | PR open |
| **Test**             | Merged; a manual test is still owed (see [Manual test](#manual-test)) |
| **Done**             | Nothing owed |

An issue moves to **Done** when nothing is owed, to **Test** when its PR leaves a manual test that tests and an emulator cannot replace. Merging closes the issue and the Item-closed workflow sets Done — move it back to Test by hand when a manual test is owed.

### Focus

A Focus is a scope-bounded batch of work: the epics' issues to finish next, plus everything that turns up while doing them. It has no fixed duration. It is a GitHub **milestone**.

- **One Focus open at a time.** The open milestone is the current Focus
- **Name** — `<short goal>`, e.g. "Ramp test rework, round 2"; the description states the goal and is kept current, so the next session (human or agent) starts from it
- **Plan** — pick issues (not epics) whose blockers are done or in the same Focus; set their milestone and move them to Ready
- **Capture** — a bug, task or follow-up found while working gets the Focus milestone when it must be solved for the goal; otherwise Backlog, outside the Focus
- **Close** — when every issue in it is closed and its manual tests are done (or moved, with a note, to the next Focus). Closing a Focus is the cycle-end event that runs `/maintain full`

### Roadmap

Prerequisite order comes from "blocked by" links between issues; an epic is blocked through its sub-issues. `tracker.py roadmap` draws open epics and every linked issue as a Mermaid graph. Ready + no open blocker = can be picked up.

### Manual test

An issue in **Test** carries a `## Manual test` section, in its body or a comment:

- The PRs it covers and why no automated test or emulator covers it
- **Test kind** set on the board, so tests needing a real session are batched into one
- The device and setup
- Numbered steps, each with its **Expected:** result

### Views

| View             | Layout | Filter |
|------------------|--------|--------|
| Focus            | Board  | `milestone:"<current Focus>" -status:Done` (update when a Focus closes) |
| Next up          | Table  | `status:Ready no:milestone`, sorted by Priority |
| Waiting on owner | Table  | `status:"Waiting on owner"` |
| Manual test      | Table  | `status:Test`, grouped by Test kind |
| Epics            | Table  | `type:Epic -status:Done` |
| Bugs             | Table  | `type:Bug -status:Done` |
| Backlog          | Table  | `status:Backlog,Refine` |

### Board script

`python docs/tools/tracker.py <command> --project <owner>/<number>`:

| Command   | Shows |
|-----------|-------|
| `status`  | Current Focus by column, Ready-and-unblocked issues outside it, Waiting on owner, manual tests by kind — run at the start of a session |
| `check`   | Rule violations: closed but not Done, open but off the board, Test without a Manual test section, more than one open Focus, Ready but blocked, issues without an epic |
| `roadmap` | Mermaid dependency graph; `--out <file>` writes it, e.g. to a wiki page |


## IDs

`[Fill in at setup: project ID, field IDs and option IDs for Status, Priority and Test kind — discover with gh api graphql]`
