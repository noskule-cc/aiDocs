# Jobs

Runnable tasks for validation. This is the central registry — check here to see what's available. `/maintain` dispatches from this table; add project jobs here with their trigger class, never to the skill.

## Cycle-End Binding

Full maintenance (`/maintain full`) fires on a real project event, never a calendar date:

- **Cycle-end event:** [sprint end | milestone close | pre-release]

## Available Jobs

| Job | Command | Trigger class | Runs when |
|-----|---------|---------------|-----------|
| [Check docs (mechanical)](#check-docs) | `python docs/tools/check-docs.py` | per-change | any doc or feature-map change (also runs in CI) |
| [Validate docs (judgment)](#validate-docs) | Invoke `validation-docs` agent | cycle-end | docs/ or wiki changed since last run |
| [Triage evals](#triage-evals) | Invoke `validation-llm` agent (Triage Eval Mode) | cycle-end | feature-map, evals, or routing docs changed since last run |

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
