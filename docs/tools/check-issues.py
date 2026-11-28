#!/usr/bin/env python3
"""Issue hierarchy checks for the standard in issue-tracker.md.

Reads the issues of one or more repositories through the GitHub API and reports
where they break the hierarchy: type and level, labels, parents, epics, wiki
page of a Feature, order written in prose. Exit 1 on errors, 0 otherwise
(warnings never fail), 2 when the API could not be read.

A type is the native issue type (organizations) or a `type:<name>` label
(personal accounts, which have no issue types). Both are read; if an issue
carries both they must agree.

Stdlib only; talks to GitHub through the `gh` CLI (must be logged in).

Usage:
  python docs/tools/check-issues.py [--repo <owner>/<name> ...] [--require-wiki]
                                    [--exempt-label LABEL ...]
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tracker  # noqa: E402  (shares the gh GraphQL helper with the board script)

# Type name (lower case) -> level: 0 epic, 1 feature, 2 task (issue-tracker.md, Hierarchy).
LEVELS = {
    "epic": 0,
    "feature": 1, "story": 1,
    "task": 2, "bug": 2, "spike": 2, "refactor": 2, "documentation": 2, "idea": 2,
}
EPIC, FEATURE, TASK = 0, 1, 2
MAX_DEPTH = 3
MAX_AREA_LABELS = 2
TYPE_LABEL_PREFIX = "type:"
# GitHub's default labels classify like a type; they are not an area of the product.
DEFAULT_LABELS = {"bug", "duplicate", "enhancement", "good first issue",
                  "help wanted", "invalid", "question", "wontfix"}

ISSUES_QUERY = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    issues(first: 100, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        id number title state body
        repository { nameWithOwner }
        issueType { name }
        labels(first: 30) { nodes { name } }
        parent { id }
        blockedBy(first: 50) { nodes { number repository { nameWithOwner } } }
      }
    }
  }
}
"""

PROSE_DEPENDENCY = re.compile(r"\b(depends on|blocked by|blocks)\s+((?:#\d+(?:\s*(?:,|and|&)\s*)?)+)", re.I)
FENCED_OR_INLINE_CODE = re.compile(r"```.*?```|`[^`\n]*`|<!--.*?-->", re.S)
WIKI_REFERENCE = re.compile(r"(?im)^[\s>*-]*\**wiki( page)?\**\s*:|/wiki/|\bwiki/\S+\.md")
ACCEPTANCE_HEADING = re.compile(r"(?im)^#+\s*acceptance")


class Issue:
    def __init__(self, node):
        labels = [label["name"] for label in node["labels"]["nodes"]]
        self.id = node["id"]
        self.repo = node["repository"]["nameWithOwner"]
        self.number = node["number"]
        self.title = node["title"]
        self.open = node["state"] == "OPEN"
        self.body = node["body"] or ""
        self.labels = labels
        self.native_type = (node.get("issueType") or {}).get("name")
        self.label_types = [name[len(TYPE_LABEL_PREFIX):].strip() for name in labels
                            if name.lower().startswith(TYPE_LABEL_PREFIX)]
        self.parent_id = (node.get("parent") or {}).get("id")
        self.blockers = {b["number"] for b in node["blockedBy"]["nodes"]
                         if b["repository"]["nameWithOwner"] == self.repo}

    @property
    def ref(self):
        return f"{self.repo}#{self.number}"


def load_issues(repo):
    owner, name = repo.split("/")
    issues, cursor = [], None
    while True:
        data = tracker.gh_graphql(ISSUES_QUERY, owner=owner, name=name, cursor=cursor)["repository"]["issues"]
        issues += [Issue(node) for node in data["nodes"]]
        if not data["pageInfo"]["hasNextPage"]:
            return issues
        cursor = data["pageInfo"]["endCursor"]


def resolve_type(issue):
    """Return (type name or None, problem or None). The name is lower case."""
    names = {name.lower() for name in ([issue.native_type] if issue.native_type else []) + issue.label_types}
    if not names:
        return None, "has no type (an issue type or a `type:<name>` label)"
    if len(names) > 1:
        return None, f"has conflicting types: {', '.join(sorted(names))}"
    name = names.pop()
    if name not in LEVELS:
        return None, f"has the unknown type `{name}`"
    return name, None


def area_labels(issue, exempt):
    return [label for label in issue.labels
            if not label.lower().startswith(TYPE_LABEL_PREFIX)
            and label.lower() not in DEFAULT_LABELS | exempt]


def prose_dependencies(body):
    """Yield (relation, number) for each order written in prose, outside code."""
    text = FENCED_OR_INLINE_CODE.sub("", body)
    for match in PROSE_DEPENDENCY.finditer(text):
        for number in re.findall(r"#(\d+)", match.group(2)):
            yield match.group(1).lower(), int(number)


def check(issues, require_wiki=False, exempt_labels=()):
    """Return [(severity, issue, message)] for the open issues; closed ones only take part as parents."""
    exempt = {label.lower() for label in exempt_labels}
    by_id = {issue.id: issue for issue in issues}
    by_ref = {issue.ref: issue for issue in issues}
    children = {}
    for issue in issues:
        children.setdefault(issue.parent_id, []).append(issue)
    types = {issue.id: resolve_type(issue)[0] for issue in issues}
    findings = []

    def add(severity, issue, message):
        findings.append((severity, issue, message))

    def depth(issue):
        seen, count = set(), 0
        while issue and issue.id not in seen:
            seen.add(issue.id)
            count += 1
            issue = by_id.get(issue.parent_id)
        return count

    for issue in issues:
        kind = types[issue.id]
        level = LEVELS.get(kind)
        if issue.open:
            if kind is None:
                add("error", issue, resolve_type(issue)[1])

            labels = area_labels(issue, exempt)
            if not labels:
                add("warning" if level == EPIC else "error", issue,
                    "has no area label (the feature it touches)")
            elif len(labels) > MAX_AREA_LABELS:
                add("warning", issue, f"has {len(labels)} area labels ({', '.join(labels)}); "
                    f"use one, two only when it spans two features equally")

            parent = by_id.get(issue.parent_id)
            if level == EPIC and issue.parent_id:
                add("error", issue, "is an epic with a parent; an epic is top level")
            elif level is not None and level != EPIC and not issue.parent_id and kind != "bug":
                add("error", issue, "has no parent epic (only a bug may stay parentless)")
            elif level == FEATURE and parent and LEVELS.get(types[parent.id]) == TASK:
                add("error", issue, f"is a {kind} under #{parent.number}, a task; a feature sits under an epic")
            if depth(issue) > MAX_DEPTH:
                add("error", issue, f"sits {depth(issue)} levels deep; the standard allows {MAX_DEPTH}")

            if level == FEATURE and not WIKI_REFERENCE.search(issue.body):
                add("error" if require_wiki else "warning", issue,
                    "is a Feature that names no wiki page (a `Wiki: <page>` line)")

            if level == EPIC:
                if not ACCEPTANCE_HEADING.search(issue.body) and "standing" not in issue.body.lower():
                    add("error", issue, "is an epic without acceptance criteria "
                        "(an `## Acceptance Criteria` section, or a note that it is standing)")
                kids = children.get(issue.id, [])
                if not kids:
                    add("warning", issue, "is an epic without sub-issues")
                elif not any(kid.open for kid in kids) and "standing" not in issue.body.lower():
                    add("warning", issue, "has every sub-issue closed; propose closing it to the owner")

            for relation, number in prose_dependencies(issue.body):
                if relation == "blocks":
                    other = by_ref.get(f"{issue.repo}#{number}")
                    if other and issue.number in other.blockers:
                        continue
                elif number in issue.blockers:
                    continue
                add("error", issue, f"writes `{relation} #{number}` in prose; "
                    f"record it as a native blocked-by link")
        elif level == EPIC and any(kid.open for kid in children.get(issue.id, [])):
            add("error", issue, "is a closed epic with open sub-issues")
    return findings


def report(findings, issues):
    ordered = sorted(findings, key=lambda f: (f[1].repo, f[1].number, f[0]))
    for severity, issue, message in ordered:
        print(f"{severity:7} {issue.ref} {message}")
    errors = sum(1 for f in findings if f[0] == "error")
    checked = sum(1 for issue in issues if issue.open)
    print(f"\n{checked} open issues checked: {errors} errors, {len(findings) - errors} warnings")
    return 1 if errors else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repo", action="append", metavar="OWNER/NAME",
                        help="repository to check; repeatable (a project spanning repos); default: the current one")
    parser.add_argument("--require-wiki", action="store_true",
                        help="make a Feature without a wiki page an error instead of a warning")
    parser.add_argument("--exempt-label", action="append", default=[], metavar="LABEL",
                        help="a label that is not a feature area (besides type: labels and GitHub's defaults)")
    args = parser.parse_args()
    issues = []
    for repo in args.repo or [tracker.default_repo()]:
        issues += load_issues(repo)
    return report(check(issues, args.require_wiki, args.exempt_label), issues)


if __name__ == "__main__":
    sys.exit(main())
