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
7. **Link prerequisites** with GitHub's native "blocked by" relation, never only in prose — "what's next" and the roadmap are built from it
8. **Title format** — imperative verb + concise description. An epic's title names its area ("Backup & Restore"), with no "Epic:" prefix: the Epic type marks it
9. **Link PRs to issues** — `Closes #N` only when the PR leaves nothing owed; when a manual test is still owed it says `Part of #N`, so the issue stays open in Test until the test passes
10. **Branch name** — `<type>/<issue number>-<slug>`, e.g. `feat/123-csv-export`; the first push moves the issue to In Progress
11. **Update wiki** when closing issues that add significant functionality
12. **Sign as an agent** — if you are an AI agent, put your signature on the **first line** of every issue body, issue or PR comment and PR body you draft: `` — 🤖 <model name> (`<model ID>`) ``, with your actual model name and exact model ID. The posting account no longer tells who wrote it; humans never sign


## Board

Built for one developer working with AI agents: no time-boxed sprints, no estimates. Work is grouped by scope (a **Focus**), ordered by dependencies, and the board tells an agent what it may pick up next.

### Fields

| Field     | Type          | Options / purpose |
|-----------|---------------|-------------------|
| Status    | Single select | The built-in field, so GitHub's "Item closed" workflow sets Done. Columns below |
| Priority  | Single select | High, Medium, Low |
| Human action | Single select | What a human has to do, by the time it costs: **Decide** (answer questions, minutes, anywhere), `[Device check]` (a quick manual test), `[Real-world event]` (a test that needs an outing, e.g. a workout — collect several, then organise one); name the test options for the project |

Enable the project workflows **Item closed** (→ Done), **Pull request merged** (→ Done), **Pull request linked to issue** (→ Review), **Item added to project** (→ Backlog), **Auto-close issue** (Done → close) and **Auto-add sub-issues to project**. Rename a Status option in the board's field settings, never through the API: the API replaces every option with a new ID, which clears every item's Status and switches off each workflow that pointed at an old one.

### Status columns

| Column               | Means |
|----------------------|-------|
| **Backlog**          | Ideas, future work, unprioritized |
| **Refine**           | Needs refinement or a precondition before it is actionable |
| **Ready**            | Refined; actionable once nothing blocks it |
| **In Progress**      | Being worked on; set by the first push of the issue's branch |
| **Needs decision**   | Stopped on a decision only a human can make; Human action is Decide and the issue holds the questions as a numbered list |
| **Review**           | PR open |
| **Test**             | Merged; a manual test is still owed (see [Manual test](#manual-test)) |
| **Done**             | Nothing owed |

Who moves an issue:

| Move | By |
|------|----|
| → In Progress | the `tracker-in-progress` workflow, on the first push of `<type>/<N>-<slug>` |
| → Review | the "Pull request linked to issue" workflow |
| → Done | merge of a PR that says `Closes #N` (closes the issue, Item closed sets Done) |
| → Test | the agent, `tracker.py set <N> Test --action <kind>`, with `Part of #N` in the PR |
| Test → Done | the human, by dragging the card; Auto-close closes the issue |
| → Needs decision | the agent, `tracker.py set <N> "Needs decision"`, with the questions in a comment |

Closed always means Done: a closed issue never sits in Test. A card dragged by hand keeps its Human action; `tracker.py check --fix` clears it.

### Work waiting for a human

An issue that needs a human is in **Needs decision** (Human action Decide) or in **Test** (Human action names the kind of test). Human action is cleared when the item leaves those columns. An agent that moves an issue to Needs decision @-mentions the owner in the comment with the numbered questions, so the owner is notified; it does not assign the issue. The Human view groups everything by Human action: decisions first, real-world events last, so the owner sees when enough have gathered to organise one.

### Focus

A Focus is a scope-bounded batch of work: the epics' issues to finish next, plus everything that turns up while doing them. It has no fixed duration. It is a GitHub **milestone**.

- **One Focus open at a time.** The open milestone is the current Focus
- **Name** — `<short goal>`, e.g. "Ramp test rework, round 2"; the description states the goal and is kept current, so the next session (human or agent) starts from it
- **Plan** — pick issues (not epics) whose blockers are done or in the same Focus; set their milestone and move them to Ready
- **Capture** — a bug, task or follow-up found while working gets the Focus milestone when it must be solved for the goal; otherwise Backlog, outside the Focus
- **Close** — when every issue in it is closed and its manual tests are done (or moved, with a note, to the next Focus). Closing a Focus is the cycle-end event that runs `/maintain full`

### Roadmap

Prerequisite order comes from "blocked by" links between issues; an epic is blocked through its sub-issues. Ready + no open blocker = can be picked up. GitHub's Roadmap layout needs dates and draws no dependencies, so `tracker.py roadmap` prints the graph instead: open epics and every linked issue as Mermaid, to paste where it is needed (issues render Mermaid). The wiki describes the product, not its project management.

### Manual test

An issue in **Test** carries a `## Manual test` section, in its body or a comment:

- The PRs it covers and why no automated test or emulator covers it
- **Human action** set on the board, so tests needing a real-world event are batched into one
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
| Human   | Table  | `has:human-action`, grouped by Human action | Work waiting for a human |

### Board script

`python docs/tools/tracker.py <command> --project <owner>/<number>`. Columns and fields are found by name, so no IDs are needed:

| Command   | Shows |
|-----------|-------|
| `status`  | Work waiting for a human by Human action, the current Focus by column, Ready-and-unblocked issues outside it — run at the start of a session |
| `check`   | Rule violations: closed but not Done, open but off the board, Test without a Manual test section, Human action missing or left set, more than one open Focus, Ready but blocked, issues without an epic. `--fix` clears a Human action left set |
| `roadmap` | Mermaid dependency graph; `--out <file>` writes it |
| `set <N> <column> [--action <kind>]` | Moves an issue and sets or clears Human action to match; adds it to the board if missing |
| `start <N>` | Moves an issue to In Progress unless it is already further along |

`docs/tools/tracker-in-progress.yml` runs `start` on every new branch: copy it to `.github/workflows/`, set the repository variable `TRACKER_PROJECT` to `<owner>/<number>`, and store a token that can write the board as the secret `PROJECT_TOKEN`. The built-in `GITHUB_TOKEN` reaches only the repository, and an organization's board is not part of it. A fine-grained token: resource owner = the board's owner, the repository only, Issues read, organization permission Projects read and write.


## IDs

`[Fill in at setup: project ID, field IDs and option IDs for Status, Priority and Human action — discover with gh api graphql]`
