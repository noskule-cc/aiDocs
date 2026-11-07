#!/usr/bin/env python3
"""Board state and board hygiene for the Focus board model (issue-tracker.md).

One query of the GitHub Projects v2 board, three views of it:

  status   what waits on the owner (by Owner action), what the current Focus
           holds, what can be picked up next
  check    board rules a script can verify; exit 1 on errors
  roadmap  Mermaid graph of open epics and issues linked by "blocked by"

Stdlib only; talks to GitHub through the `gh` CLI (must be logged in).

Usage:
  python docs/tools/tracker.py status  --project <owner>/<number> [--repo <owner>/<name>]
  python docs/tools/tracker.py check   --project <owner>/<number> [--repo <owner>/<name>]
  python docs/tools/tracker.py roadmap --project <owner>/<number> [--repo <owner>/<name>] [--out FILE]
"""

import argparse
import json
import subprocess
import sys

# Column names of the Status field, in board order (issue-tracker.md).
STATUSES = ["Backlog", "Refine", "Ready", "In Progress", "Waiting on owner",
            "Review", "Test", "Done"]
EPIC_TYPE = "Epic"
BUG_TYPE = "Bug"
OWNER_FIELD = "Owner action"
DECIDE = "Decide"  # the Owner action that pairs with "Waiting on owner"
MANUAL_TEST_HEADING = "## manual test"

ITEM_FIELDS = """
  status: fieldValueByName(name: "Status") {
    ... on ProjectV2ItemFieldSingleSelectValue { name } }
  ownerAction: fieldValueByName(name: "Owner action") {
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
                "owner_action": single(node.get("ownerAction")),
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

    owed = [i for i in items if i["owner_action"]
            or i["status"] == "Waiting on owner" or (i["status"] == "Test")]
    actions = sorted({i["owner_action"] or "no Owner action" for i in owed},
                     key=lambda a: (a != DECIDE, a == "no Owner action", a))
    print(f"Waiting for the owner ({len(owed)})")
    for action in actions:
        section(action, by_priority([i for i in owed
                                     if (i["owner_action"] or "no Owner action") == action]), " ")

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


def cmd_check(fields, items, milestones, off_board):
    errors, warnings = [], []
    for name in ["Status", "Priority", OWNER_FIELD]:
        if name not in fields:
            errors.append(f"board has no '{name}' field")
    if len(milestones) > 1:
        errors.append("more than one open milestone (one Focus at a time): "
                      + ", ".join(m["title"] for m in milestones))
    for issue in off_board:
        errors.append(f"#{issue['number']} is open but not on the board")
    for i in items:
        ref = f"#{i['number']} ({i['status'] or 'no status'})"
        action = i["owner_action"]
        if i["status"] == "Test" and action in (None, DECIDE):
            errors.append(f"{ref} is in Test without a test Owner action")
        elif i["status"] == "Waiting on owner" and action != DECIDE:
            errors.append(f"{ref} is Waiting on owner without Owner action {DECIDE}")
        elif action and i["status"] not in ("Test", "Waiting on owner"):
            errors.append(f"{ref} still has Owner action {action}; clear it")
        if not i["open"]:
            if i["status"] not in ("Done", "Test"):
                errors.append(f"{ref} is closed but not Done")
            elif i["status"] == "Test" and not i["has_manual_test"]:
                errors.append(f"{ref} is in Test without a '## Manual test' section")
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
                          ("Waiting on owner", "stroke:#f9a825,stroke-width:3px,stroke-dasharray:5 3")]:
        ids = [f"i{n}" for n in shown if open_by_number[n]["status"] == status]
        if ids:
            cls = status.lower().replace(" ", "_")
            lines.append(f"  classDef {cls} {style}")
            lines.append(f"  class {','.join(ids)} {cls}")
    text = "```mermaid\n" + "\n".join(lines) + "\n```\n"
    text += ("\nArrow: blocker → blocked. Green = Ready, blue = In Progress, "
             "yellow dashed = Waiting on owner.\n")
    if out:
        with open(out, "w", encoding="utf-8") as handle:
            handle.write(text)
        print(f"wrote {out}: {len(shown)} items, {len(edges)} dependencies")
    else:
        print(text)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=["status", "check", "roadmap"])
    parser.add_argument("--project", required=True, help="<owner>/<project number>")
    parser.add_argument("--repo", help="<owner>/<name>; default: the current repository")
    parser.add_argument("--out", help="roadmap: write the Mermaid block to this file")
    args = parser.parse_args()
    board = load_board(args.project, args.repo or default_repo())
    if args.command == "status":
        return cmd_status(*board)
    if args.command == "check":
        return cmd_check(*board)
    return cmd_roadmap(*board, out=args.out)


if __name__ == "__main__":
    sys.exit(main())
