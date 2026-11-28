# Jobs

Runnable tasks for validation. This is the central registry — check here to see what's available. `/maintain` dispatches from this table; add project jobs here with their trigger class, never to the skill.

## Cycle-End Binding

Full maintenance (`/maintain full`) fires on a real project event, never a calendar date:

- **Cycle-end event:** [Focus close (see `issue-tracker.md`) | release milestone close | pre-release]

## Available Jobs

| Job | Command | Trigger class | Runs when |
|-----|---------|---------------|-----------|
| [Check docs (mechanical)](#check-docs) | `python docs/tools/check-docs.py` | per-change | any doc or feature-map change (also runs in CI) |
| [Validate docs (judgment)](#validate-docs) | Invoke `validation-docs` agent | cycle-end | docs/ or wiki changed since last run |
| [Triage evals](#triage-evals) | Invoke `validation-llm` agent (Triage Eval Mode) | cycle-end | feature-map, evals, or routing docs changed since last run |
| [Check tracker](#check-tracker) | `python docs/tools/tracker.py check --project <owner>/<number>` | cycle-end | only with a Projects v2 board; always runs (the board changes outside git) |
| [Check issues](#check-issues) | `python docs/tools/check-issues.py --repo <owner>/<name>` | cycle-end | only with GitHub issues; always runs (issue state is not in any diff) |
| [Issue graph](#issue-graph) | `python docs/tools/issue-graph.py <epic> --repo <owner>/<name> --write` | cycle-end | only with GitHub issues; for each open epic whose sub-issues or blocked-by links changed since the last run |
| [Verification map](#verification-map) | `/maintain-verification-skill` (method stack) | cycle-end | only if the project has a verification skill: app UI or the skill changed since last run |

**Trigger classes:**

- **per-change** — diff-conditional; dispatched by `/maintain change` before each PR (pre-PR contract in `AGENTS.md`)
- **cycle-end** — judgment and eval battery; dispatched by `/maintain full` at the bound event, scoped to changes since the last-run stamp (`docs/.maintain-last-run`)

## Job Details

### Check docs

Mechanical structural checks: link resolution (case-sensitive), orphan pages, index consistency, agent-wrapper bindings, template hygiene, standard-set references, feature-map entry-point resolution.

1. Run `python docs/tools/check-docs.py`
2. Exit code non-zero on errors; warnings don't fail the build

### Validate docs

Judgment checks a script can't do: duplicated knowledge, stale content, wiki structure, file focus.

1. Invoke the `validation-docs` agent (auto-discovered from `.claude/agents/`)
2. The agent's instructions (`.claude/agents/validation-docs.md`) run check-docs.py first, then the judgment checklist
3. Output: report with issues to fix

### Triage evals

Routing-effectiveness test: bug-report-phrased questions from `evals.md` run against a fresh agent, scored on landing at the expected entry point (with/without `feature-map.md`).

1. Invoke the `validation-llm` agent — Triage Eval Mode runs when `tools/evals.md` exists
2. Output: hit-rate report per mode, misses diagnosed with navigation traces

### Check tracker

Board rules from `issue-tracker.md` that a script can verify: closed but not Done, open but off the board, Test without a `## Manual test` section, Human action missing or left set, more than one open Focus, Ready but blocked, issues without an epic. Delete this row and section when the project has no board.

1. Run `python docs/tools/tracker.py check --project <owner>/<number>` (needs a logged-in `gh`)
2. Exit code non-zero on errors; fix each on the board, warnings are judgment calls

### Check issues

The issue hierarchy of `issue-tracker.md` that a script can verify: type and level, feature labels, parents, epics with acceptance criteria, order written in prose instead of native "blocked by", the wiki page of a Feature. Delete this row and section when the project does not track work in GitHub issues.

1. Run `python docs/tools/check-issues.py --repo <owner>/<name>` (needs a logged-in `gh`; repeat `--repo` for each repository of the project)
2. Exit code non-zero on errors; fix each in the issue, warnings are judgment calls (a closed-out epic is proposed to the owner, never closed by the agent)

### Issue graph

Regenerates the Mermaid work graph in an epic's body from its sub-issues and "blocked by" links. Delete this row and section together with Check issues.

1. Find the open epics whose links changed (the Epics view), run `python docs/tools/issue-graph.py <epic> --repo <owner>/<name> --write` for each
2. Output: "written" or "already current"; the graph is never edited by hand

### Verification map

Optional, for projects whose method stack generated a verification skill (pstack's `/create-verification-skill`). Keeps its feature map true to the app: source readers per feature, one live pass that drives every feature, at most one PR of proven corrections. Product defects it finds become issues, never doc edits. Delete this row and section when the project has no verification skill.

1. Invoke `/maintain-verification-skill`
2. Output: outcome `clean`, `changed` (one PR) or `blocked`, with coverage and product defects

