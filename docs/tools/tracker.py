#!/usr/bin/env python3
"""Board state and board hygiene for the Focus board model (issue-tracker.md).

Reads the GitHub Projects v2 board, and moves issues on it:

  status   what waits on a human (by Human action), what the current Focus
           holds, what can be picked up next
  check    board rules a script can verify; exit 1 on errors; --fix clears
           a Human action left on a card dragged out of its column
  roadmap  Mermaid graph of open epics and issues linked by "blocked by"
  set      move an issue to a column; sets or clears Human action to match
  start    move an issue to In Progress unless it is already further along
           (run by the tracker-in-progress workflow on a branch push)

Stdlib only; talks to GitHub through the `gh` CLI (must be logged in).

Usage:
  python docs/tools/tracker.py status  --project <owner>/<number> [--repo <owner>/<name>]
  python docs/tools/tracker.py check   --project <owner>/<number> [--repo <owner>/<name>] [--fix]
  python docs/tools/tracker.py roadmap --project <owner>/<number> [--repo <owner>/<name>] [--out FILE]
  python docs/tools/tracker.py set <issue> <column> [--action <Human action>] --project <owner>/<number> [--repo <owner>/<name>]
  python docs/tools/tracker.py start <issue> --project <owner>/<number> [--repo <owner>/<name>]
"""

import argparse
import json
import subprocess
import sys

# Column names of the Status field, in board order (issue-tracker.md).
STATUSES = ["Backlog", "Refine", "Ready", "In Progress", "Needs decision",
            "Review", "Test", "Done"]
NEEDS_DECISION = "Needs decision"
EPIC_TYPE = "Epic"
BUG_TYPE = "Bug"
HUMAN_FIELD = "Human action"
DECIDE = "Decide"  # the Human action that pairs with "Needs decision"
HUMAN_STATUSES = (NEEDS_DECISION, "Test")  # the columns that carry a Human action
MANUAL_TEST_HEADING = "## manual test"

ITEM_FIELDS = """
  status: fieldValueByName(name: "Status") {
    ... on ProjectV2ItemFieldSingleSelectValue { name } }
  humanAction: fieldValueByName(name: "Human action") {
    ... on ProjectV2ItemFieldSingleSelectValue { name } }
  priority: fieldValueByName(name: "Priority") {
    ... on ProjectV2ItemFieldSingleSelectValue { name } }
  content {
    ... on Issue {
      number title state url body
      repository { nameWithOwner }
      milestone { title state }
      issueType { name }
      parent { number }
      blockedBy(first: 50) { nodes { number state } }
      comments(last: 30) { nodes { body } }
    }
  }
"""

PROJECT_QUERY = """
query($owner: String!, $number: Int!, $cursor: String) {
  %s(login: $owner) {
    projectV2(number: $number) {
      fields(first: 50) { nodes { ... on ProjectV2FieldCommon { name } } }
      items(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes { %s }
      }
    }
  }
}
"""

REPO_QUERY = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    milestones(first: 50, states: OPEN) {
      nodes { title description url openIssues: issues(states: OPEN) { totalCount } }
    }
    issues(first: 100, after: $cursor, states: OPEN) {
      pageInfo { hasNextPage endCursor }
      nodes { number title projectItems(first: 20) { nodes { project { number owner { ... on Organization { login } ... on User { login } } } } } }
    }
  }
}
"""


def gh_graphql(query, **variables):
    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        if value is None:
            continue
        flag = "-F" if isinstance(value, int) else "-f"
        cmd += [flag, f"{key}={value}"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        sys.exit(f"gh api graphql failed: {result.stderr.strip()}")
    return json.loads(result.stdout)["data"]


def owner_kind(owner):
    result = subprocess.run(["gh", "api", f"users/{owner}", "--jq", ".type"],
                            capture_output=True, text=True)
    return "organization" if result.stdout.strip() == "Organization" else "user"


def default_repo():
    result = subprocess.run(["gh", "repo", "view", "--json", "nameWithOwner",
                             "--jq", ".nameWithOwner"], capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit("No --repo given and `gh repo view` found no repository here")
    return result.stdout.strip()


def single(value):
    return (value or {}).get("name")


def load_board(project, repo):
    owner, number = project.split("/")
    number = int(number)
    kind = owner_kind(owner)
    query = PROJECT_QUERY % (kind, ITEM_FIELDS)
    items, fields, cursor = [], None, None
    while True:
        data = gh_graphql(query, owner=owner, number=number, cursor=cursor)
        board = data[kind]["projectV2"]
        fields = fields or [f.get("name") for f in board["fields"]["nodes"] if f]
        page = board["items"]
        for node in page["nodes"]:
            issue = node.get("content") or {}
            if "number" not in issue or issue["repository"]["nameWithOwner"] != repo:
                continue
            comments = [c["body"] for c in issue["comments"]["nodes"]]
            items.append({
                "number": issue["number"],
                "title": issue["title"],
                "url": issue["url"],
                "open": issue["state"] == "OPEN",
                "status": single(node.get("status")),
                "human_action": single(node.get("humanAction")),
                "priority": single(node.get("priority")),
                "type": (issue.get("issueType") or {}).get("name"),
                "parent": (issue.get("parent") or {}).get("number"),
                "milestone": (issue.get("milestone") or {}).get("title"),
                "blocked_by": [b["number"] for b in issue["blockedBy"]["nodes"]
                               if b["state"] == "OPEN"],
                "has_manual_test": any(MANUAL_TEST_HEADING in (text or "").lower()
                                       for text in [issue["body"], *comments]),
            })
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]

    repo_owner, repo_name = repo.split("/")
    milestones, off_board, cursor = None, [], None
    while True:
        data = gh_graphql(REPO_QUERY, owner=repo_owner, name=repo_name, cursor=cursor)["repository"]
        milestones = milestones or data["milestones"]["nodes"]
        for issue in data["issues"]["nodes"]:
            on_board = any(p["project"]["number"] == number
                           and p["project"]["owner"]["login"] == owner
                           for p in issue["projectItems"]["nodes"])
            if not on_board:
                off_board.append(issue)
        if not data["issues"]["pageInfo"]["hasNextPage"]:
            break
        cursor = data["issues"]["pageInfo"]["endCursor"]
    return fields, items, milestones, off_board


def line(item):
    extra = []
    if item["priority"]:
        extra.append(item["priority"])
    if item["blocked_by"]:
        extra.append("blocked by " + ", ".join(f"#{n}" for n in item["blocked_by"]))
    suffix = f"  ({'; '.join(extra)})" if extra else ""
    return f"  #{item['number']} {item['title']}{suffix}"


PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}


def by_priority(items):
    return sorted(items, key=lambda i: (PRIORITY_ORDER.get(i["priority"], 3), i["number"]))


def cmd_status(fields, items, milestones, off_board):
    def section(title, rows, indent=""):
        print(f"\n{indent}{title} ({len(rows)})")
        for row in rows:
            print(indent + line(row))

    owed = [i for i in items if i["human_action"] or i["status"] in HUMAN_STATUSES]
    actions = sorted({i["human_action"] or "no Human action" for i in owed},
                     key=lambda a: (a != DECIDE, a == "no Human action", a))
    print(f"Waiting for a human ({len(owed)})")
    for action in actions:
        section(action, by_priority([i for i in owed
                                     if (i["human_action"] or "no Human action") == action]), " ")

    open_items = [i for i in items if i["open"] and i["type"] != EPIC_TYPE]
    focus = milestones[0] if len(milestones) == 1 else None
    print()
    if focus:
        print(f"Focus: {focus['title']}  ({focus['openIssues']['totalCount']} open)  {focus['url']}")
        if focus["description"]:
            print("  " + focus["description"].strip().replace("\n", "\n  "))
    elif milestones:
        print("Focus: ambiguous, open milestones: " + ", ".join(m["title"] for m in milestones))
    else:
        print("Focus: none open")
    in_focus = [i for i in open_items if focus and i["milestone"] == focus["title"]]
    for status in ["In Progress", "Review", "Ready", "Refine"]:
        rows = [i for i in in_focus if i["status"] == status]
        if rows:
            section(f"Focus · {status}", by_priority(rows))
    pickable = [i for i in open_items if i["status"] == "Ready" and not i["blocked_by"]
                and i not in in_focus]
    section("Ready outside the Focus, unblocked", by_priority(pickable)[:15])
    return 0


def cmd_check(fields, items, milestones, off_board, fix=None):
    """fix: (project, repo) to clear Human action left on columns that carry none."""
    errors, warnings = [], []
    for name in ["Status", "Priority", HUMAN_FIELD]:
        if name not in fields:
            errors.append(f"board has no '{name}' field")
    if len(milestones) > 1:
        errors.append("more than one open milestone (one Focus at a time): "
                      + ", ".join(m["title"] for m in milestones))
    for issue in off_board:
        errors.append(f"#{issue['number']} is open but not on the board")
    for i in items:
        ref = f"#{i['number']} ({i['status'] or 'no status'})"
        action = i["human_action"]
        if i["status"] == "Test" and action in (None, DECIDE):
            errors.append(f"{ref} is in Test without a test Human action")
        elif i["status"] == NEEDS_DECISION and action != DECIDE:
            errors.append(f"{ref} is {NEEDS_DECISION} without Human action {DECIDE}")
        elif action and i["status"] not in HUMAN_STATUSES:
            # A card dragged on the board keeps its Human action.
            if fix and i["status"] in STATUSES:
                move(*fix, i["number"], i["status"])
            else:
                errors.append(f"{ref} still has Human action {action}; clear it (check --fix)")
        if not i["open"]:
            if i["status"] == "Test":
                # Old state: the PR said "Closes #N" while a test was still owed.
                # Left closed; it clears when the test is done and the item set to Done.
                warnings.append(f"{ref} is closed with a manual test still owed; "
                                "new ones stay open (the PR says 'Part of #N')")
                if not i["has_manual_test"]:
                    errors.append(f"{ref} is in Test without a '## Manual test' section")
            elif i["status"] != "Done":
                errors.append(f"{ref} is closed but not Done")
            continue
        if i["status"] is None:
            errors.append(f"{ref} has no Status")
        elif i["status"] not in STATUSES:
            errors.append(f"{ref} has a Status outside the standard columns")
        if i["status"] == "Done":
            errors.append(f"{ref} is open but Done")
        if i["status"] == "Test":
            if not i["has_manual_test"]:
                errors.append(f"{ref} is in Test without a '## Manual test' section")
        if i["type"] == EPIC_TYPE:
            if i["milestone"]:
                warnings.append(f"{ref} is an epic in a Focus; put its sub-issues there instead")
            continue
        if i["parent"] is None and i["type"] != BUG_TYPE:
            warnings.append(f"{ref} has no parent epic")
        if i["status"] == "Ready" and i["blocked_by"]:
            warnings.append(f"{ref} is Ready but blocked by "
                            + ", ".join(f"#{n}" for n in i["blocked_by"]))
        if i["status"] in ("In Progress", "Review") and not i["milestone"]:
            warnings.append(f"{ref} is being worked on outside a Focus")
    for msg in errors:
        print(f"ERROR   {msg}")
    for msg in warnings:
        print(f"WARNING {msg}")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


def cmd_roadmap(fields, items, milestones, off_board, out=None):
    open_by_number = {i["number"]: i for i in items if i["open"]}
    edges = [(b, i["number"]) for i in open_by_number.values()
             for b in i["blocked_by"] if b in open_by_number]
    shown = {n for edge in edges for n in edge}
    shown |= {n for n, i in open_by_number.items()
              if i["type"] == EPIC_TYPE and i["status"] not in ("Backlog", None)}

    def label(i):
        title = i["title"].replace('"', "'")
        if len(title) > 48:
            title = title[:47] + "…"
        return f'i{i["number"]}["#{i["number"]} {title}<br>{i["status"] or "no status"}"]'

    lines = ["flowchart LR"]
    epics = {n for n in shown if open_by_number[n]["type"] == EPIC_TYPE}
    children = {}
    for n in shown - epics:
        children.setdefault(open_by_number[n]["parent"], []).append(n)
    for epic in sorted(epics):
        lines.append(f'  subgraph e{epic}["Epic #{epic} {open_by_number[epic]["title"].replace(chr(34), chr(39))}"]')
        lines.append("    direction TB")
        lines.append(f"    {label(open_by_number[epic])}")
        for n in sorted(children.pop(epic, [])):
            lines.append(f"    {label(open_by_number[n])}")
        lines.append("  end")
    for parent in sorted(children, key=lambda p: (p is None, p or 0)):
        for n in sorted(children[parent]):
            lines.append(f"  {label(open_by_number[n])}")
    for blocker, blocked in sorted(edges):
        lines.append(f"  i{blocker} --> i{blocked}")
    for status, style in [("Ready", "stroke:#2e7d32,stroke-width:3px"),
                          ("In Progress", "stroke:#1565c0,stroke-width:3px"),
                          (NEEDS_DECISION, "stroke:#f9a825,stroke-width:3px,stroke-dasharray:5 3")]:
        ids = [f"i{n}" for n in shown if open_by_number[n]["status"] == status]
        if ids:
            cls = status.lower().replace(" ", "_")
            lines.append(f"  classDef {cls} {style}")
            lines.append(f"  class {','.join(ids)} {cls}")
    text = "```mermaid\n" + "\n".join(lines) + "\n```\n"
    text += ("\nArrow: blocker → blocked. Green = Ready, blue = In Progress, "
             f"yellow dashed = {NEEDS_DECISION}.\n")
    if out:
        with open(out, "w", encoding="utf-8") as handle:
            handle.write(text)
        print(f"wrote {out}: {len(shown)} items, {len(edges)} dependencies")
    else:
        print(text)
    return 0


FIELDS_QUERY = """
query($owner: String!, $number: Int!) {
  %s(login: $owner) {
    projectV2(number: $number) {
      id
      fields(first: 50) { nodes { ... on ProjectV2SingleSelectField { id name options { id name } } } }
    }
  }
}
"""

ISSUE_ITEM_QUERY = """
query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    issue(number: $number) {
      id
      projectItems(first: 20) {
        nodes {
          id
          project { id }
          status: fieldValueByName(name: "Status") {
            ... on ProjectV2ItemFieldSingleSelectValue { name } }
          humanAction: fieldValueByName(name: "Human action") {
            ... on ProjectV2ItemFieldSingleSelectValue { name } }
        }
      }
    }
  }
}
"""

SET_VALUE = """mutation($p: ID!, $i: ID!, $f: ID!, $o: String!) {
  updateProjectV2ItemFieldValue(input: {projectId: $p, itemId: $i, fieldId: $f,
    value: {singleSelectOptionId: $o}}) { clientMutationId } }"""

CLEAR_VALUE = """mutation($p: ID!, $i: ID!, $f: ID!) {
  clearProjectV2ItemFieldValue(input: {projectId: $p, itemId: $i, fieldId: $f}) {
    clientMutationId } }"""

ADD_ITEM = """mutation($p: ID!, $c: ID!) {
  addProjectV2ItemById(input: {projectId: $p, contentId: $c}) { item { id } } }"""


def option_id(field, name):
    for option in field["options"]:
        if option["name"] == name:
            return option["id"]
    sys.exit(f"'{field['name']}' has no option '{name}'; options: "
             + ", ".join(o["name"] for o in field["options"]))


def human_action_for(status, requested, current, options):
    """The Human action a column requires: Decide, a test kind, or none."""
    if status == NEEDS_DECISION:
        if requested not in (None, DECIDE):
            sys.exit(f"{NEEDS_DECISION} goes with Human action {DECIDE}")
        return DECIDE
    if status == "Test":
        action = requested or (current if current != DECIDE else None)
        if action in (None, DECIDE):
            sys.exit("Test needs --action naming the kind of test: "
                     + ", ".join(o for o in options if o != DECIDE))
        return action
    if requested:
        sys.exit(f"Human action is only set in {' and '.join(HUMAN_STATUSES)}")
    return None


def move(project, repo, number, status, requested=None, only_from=None):
    """Set Status and the matching Human action of one issue; add it to the board if missing.

    only_from: leave the issue alone unless its current Status is one of these.
    """
    if status not in STATUSES:
        sys.exit(f"'{status}' is not a column; columns: " + ", ".join(STATUSES))
    owner, project_number = project.split("/")
    kind = owner_kind(owner)
    board = gh_graphql(FIELDS_QUERY % kind, owner=owner, number=int(project_number))[kind]["projectV2"]
    fields = {f["name"]: f for f in board["fields"]["nodes"] if f}
    for name in ("Status", HUMAN_FIELD):
        if name not in fields:
            sys.exit(f"board has no single-select field '{name}'")
    repo_owner, repo_name = repo.split("/")
    issue = gh_graphql(ISSUE_ITEM_QUERY, owner=repo_owner, name=repo_name,
                       number=number)["repository"]["issue"]
    item = next((i for i in issue["projectItems"]["nodes"]
                 if i["project"]["id"] == board["id"]), None)
    current = single(item.get("status")) if item else None
    current_action = single(item.get("humanAction")) if item else None
    if only_from is not None and current not in only_from:
        print(f"#{number} stays {current}")
        return 0
    action = human_action_for(status, requested, current_action,
                              [o["name"] for o in fields[HUMAN_FIELD]["options"]])
    if item is None:
        item = gh_graphql(ADD_ITEM, p=board["id"], c=issue["id"])["addProjectV2ItemById"]["item"]
    gh_graphql(SET_VALUE, p=board["id"], i=item["id"], f=fields["Status"]["id"],
               o=option_id(fields["Status"], status))
    if action:
        gh_graphql(SET_VALUE, p=board["id"], i=item["id"], f=fields[HUMAN_FIELD]["id"],
                   o=option_id(fields[HUMAN_FIELD], action))
    elif current_action:
        gh_graphql(CLEAR_VALUE, p=board["id"], i=item["id"], f=fields[HUMAN_FIELD]["id"])
    print(f"#{number} {current or 'off the board'} -> {status}" + (f" ({action})" if action else ""))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=["status", "check", "roadmap", "set", "start"])
    parser.add_argument("issue", nargs="?", type=int, help="set/start: the issue number")
    parser.add_argument("column", nargs="?", help="set: the Status column")
    parser.add_argument("--action", help=f"set: the {HUMAN_FIELD} for Test or {NEEDS_DECISION}")
    parser.add_argument("--project", required=True, help="<owner>/<project number>")
    parser.add_argument("--repo", help="<owner>/<name>; default: the current repository")
    parser.add_argument("--out", help="roadmap: write the Mermaid block to this file")
    parser.add_argument("--fix", action="store_true",
                        help="check: clear Human action left on a column that carries none")
    args = parser.parse_args()
    repo = args.repo or default_repo()
    if args.command in ("set", "start"):
        if args.issue is None or (args.command == "set") != bool(args.column):
            parser.error("usage: set <issue> <column> | start <issue>")
        if args.command == "start":
            return move(args.project, repo, args.issue, "In Progress",
                        only_from=(None, "Backlog", "Refine", "Ready"))
        return move(args.project, repo, args.issue, args.column, requested=args.action)
    board = load_board(args.project, repo)
    if args.command == "status":
        return cmd_status(*board)
    if args.command == "check":
        return cmd_check(*board, fix=(args.project, repo) if args.fix else None)
    return cmd_roadmap(*board, out=args.out)


if __name__ == "__main__":
    sys.exit(main())
