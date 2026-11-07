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
| Owner action | Single select | What the owner has to do, by the time it costs: **Decide** (answer questions, minutes, anywhere), `[Device check]` (a quick manual test), `[Real-world event]` (a test that needs an outing, e.g. a workout — collect several, then organise one); name the test options for the project |

Enable the project workflows **Item closed** (→ Done), **Pull request merged** (→ Done), **Pull request linked to issue** (→ Review), **Item added to project** (→ Backlog) and **Auto-add sub-issues to project**. Changing the Status options gives every option a new ID, and GitHub then switches off each workflow that pointed at an old one: set their targets and enable them again by hand.

### Status columns

| Column               | Means |
|----------------------|-------|
| **Backlog**          | Ideas, future work, unprioritized |
| **Refine**           | Needs refinement or a precondition before it is actionable |
| **Ready**            | Refined; actionable once nothing blocks it |
| **In Progress**      | Being worked on |
| **Waiting on owner** | Stopped on a decision only the owner can make; Owner action is Decide and the issue holds the questions as a numbered list |
| **Review**           | PR open |
| **Test**             | Merged; a manual test is still owed (see [Manual test](#manual-test)) |
| **Done**             | Nothing owed |

An issue moves to **Done** when nothing is owed, to **Test** when its PR leaves a manual test that tests and an emulator cannot replace. Merging closes the issue and the Item-closed workflow sets Done — move it back to Test by hand when a manual test is owed.

### Work waiting for the owner

An issue that needs the owner is in **Waiting on owner** (Owner action Decide) or in **Test** (Owner action names the kind of test). Owner action is cleared when the item leaves those columns. An agent that moves an issue to Waiting on owner @-mentions the owner in the comment with the numbered questions, so the owner is notified; it does not assign the issue. The Owner view groups everything by Owner action: decisions first, real-world events last, so the owner sees when enough have gathered to organise one.

### Focus

A Focus is a scope-bounded batch of work: the epics' issues to finish next, plus everything that turns up while doing them. It has no fixed duration. It is a GitHub **milestone**.

- **One Focus open at a time.** The open milestone is the current Focus
- **Name** — `<short goal>`, e.g. "Ramp test rework, round 2"; the description states the goal and is kept current, so the next session (human or agent) starts from it
- **Plan** — pick issues (not epics) whose blockers are done or in the same Focus; set their milestone and move them to Ready
- **Capture** — a bug, task or follow-up found while working gets the Focus milestone when it must be solved for the goal; otherwise Backlog, outside the Focus
- **Close** — when every issue in it is closed and its manual tests are done (or moved, with a note, to the next Focus). Closing a Focus is the cycle-end event that runs `/maintain full`

### Roadmap

Prerequisite order comes from "blocked by" links between issues; an epic is blocked through its sub-issues. GitHub's Roadmap layout needs dates, so the roadmap is a wiki page instead: `tracker.py roadmap --out <wiki page>` draws open epics and every linked issue as a Mermaid graph, regenerated when a Focus closes. Ready + no open blocker = can be picked up.

### Manual test

An issue in **Test** carries a `## Manual test` section, in its body or a comment:

- The PRs it covers and why no automated test or emulator covers it
- **Owner action** set on the board, so tests needing a real-world event are batched into one
- The device and setup
- Numbered steps, each with its **Expected:** result

### Views

| View    | Layout | Filter | Purpose |
|---------|--------|--------|---------|
| Backlog | Table  | `-status:Done` | Everything open |
| Refine  | Table  | `status:Refine`, grouped by Parent issue | Where questions and uncertainty are; each card ends with its open question |
| Epics   | Table  | `type:Epic -status:Done`, with Sub-issues progress | The big picture |
| Bugs    | Table  | `type:Bug -status:Done`, sorted by Priority | Rank all bugs |
| Ready   | Table  | `status:Ready no:milestone`, sorted by Priority | The pool the next Focus is picked from |
| Focus   | Board  | `has:milestone -status:Done` | What is being done now; a closed Focus leaves nothing open behind, so the filter never needs updating |
| Owner   | Table  | `has:owner-action`, grouped by Owner action | Work waiting for the owner |

### Board script

`python docs/tools/tracker.py <command> --project <owner>/<number>`:

| Command   | Shows |
|-----------|-------|
| `status`  | Work waiting for the owner by Owner action, the current Focus by column, Ready-and-unblocked issues outside it — run at the start of a session |
| `check`   | Rule violations: closed but not Done, open but off the board, Test without a Manual test section, Owner action missing or left set, more than one open Focus, Ready but blocked, issues without an epic |
| `roadmap` | Mermaid dependency graph; `--out <file>` writes it, e.g. to a wiki page |


## IDs

`[Fill in at setup: project ID, field IDs and option IDs for Status, Priority and Owner action — discover with gh api graphql]`
