import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from loader import load

ci = load("check-issues.py")
REPO = "acme/app"
EPIC_BODY = "## Acceptance Criteria\n- [ ] done"
NO_AREA = "has no area label (the feature it touches)"


def node(number, *, type=None, labels=("training",), parent=None, body="", state="OPEN", blocked_by=()):
    return {
        "id": f"I_{number}", "number": number, "title": f"Issue {number}", "state": state, "body": body,
        "repository": {"nameWithOwner": REPO},
        "issueType": {"name": type} if type else None,
        "labels": {"nodes": [{"name": name} for name in labels]},
        "parent": {"id": f"I_{parent}"} if parent else None,
        "blockedBy": {"nodes": [{"number": n, "repository": {"nameWithOwner": REPO}} for n in blocked_by]},
    }


def messages(*nodes, **options):
    """[(severity, issue number, message)] for fake issue nodes."""
    return [(severity, issue.number, message) for severity, issue, message in
            ci.check([ci.Issue(n) for n in nodes], **options)]


def for_issue(result, number):
    return [(severity, message) for severity, n, message in result if n == number]


class ValidTree(unittest.TestCase):
    def test_native_types_pass(self):
        self.assertEqual(messages(
            node(1, type="Epic", body=EPIC_BODY),
            node(2, type="Feature", parent=1, body="Wiki: [page](https://x/wiki/page)"),
            node(3, type="Task", parent=2),
        ), [])

    def test_type_labels_pass_where_there_are_no_issue_types(self):
        self.assertEqual(messages(
            node(1, labels=("type:epic", "training"), body=EPIC_BODY),
            node(2, labels=("type:feature", "training"), parent=1, body="- Wiki: x.md"),
            node(3, labels=("type:task", "training"), parent=2),
        ), [])

    def test_bug_may_stay_parentless_and_epic_needs_no_area(self):
        result = messages(node(1, type="Bug"), node(2, type="Epic", labels=(), body="standing epic"))
        self.assertEqual(result, [("warning", 2, NO_AREA), ("warning", 2, "is an epic without sub-issues")])


class Types(unittest.TestCase):
    def test_missing_unknown_and_conflicting_types(self):
        result = messages(node(1), node(2, type="Widget"), node(3, type="Task", labels=("type:bug", "ui")))
        self.assertIn("has no type", for_issue(result, 1)[0][1])
        self.assertIn("unknown type `widget`", for_issue(result, 2)[0][1])
        self.assertIn("conflicting types: bug, task", for_issue(result, 3)[0][1])

    def test_label_and_native_type_that_agree_are_one_type(self):
        self.assertEqual(messages(node(1, type="Bug", labels=("type:bug", "ui"))), [])

    def test_story_counts_as_a_feature(self):
        result = messages(node(1, type="Epic", body=EPIC_BODY), node(2, type="Story", parent=1))
        self.assertEqual(for_issue(result, 2)[0][1][:34], "is a Feature that names no wiki pa")


class Labels(unittest.TestCase):
    def test_task_without_area_label_is_an_error(self):
        result = messages(node(1, type="Epic", body=EPIC_BODY), node(2, type="Task", parent=1, labels=("type:task",)))
        self.assertEqual(for_issue(result, 2), [("error", NO_AREA)])

    def test_github_default_labels_are_not_areas(self):
        result = messages(node(1, type="Epic", body=EPIC_BODY), node(2, type="Task", parent=1, labels=("enhancement",)))
        self.assertEqual(for_issue(result, 2), [("error", NO_AREA)])

    def test_exempt_label_is_not_an_area(self):
        result = messages(node(1, type="Epic", body=EPIC_BODY), node(2, type="Task", parent=1, labels=("SYSTEM",)),
                          exempt_labels=["system"])
        self.assertEqual(for_issue(result, 2), [("error", NO_AREA)])

    def test_three_area_labels_warn(self):
        result = messages(node(1, type="Epic", body=EPIC_BODY),
                          node(2, type="Task", parent=1, labels=("ui", "ble", "hrv")))
        self.assertEqual([severity for severity, _ in for_issue(result, 2)], ["warning"])


class Hierarchy(unittest.TestCase):
    def test_non_bug_without_parent(self):
        self.assertEqual(messages(node(1, type="Task")),
                         [("error", 1, "has no parent epic (only a bug may stay parentless)")])

    def test_epic_with_a_parent(self):
        result = messages(node(1, type="Epic", body=EPIC_BODY), node(2, type="Epic", parent=1, body=EPIC_BODY),
                          node(3, type="Task", parent=2))
        self.assertEqual(for_issue(result, 2), [("error", "is an epic with a parent; an epic is top level")])

    def test_feature_under_a_task(self):
        result = messages(node(1, type="Epic", body=EPIC_BODY), node(2, type="Task", parent=1),
                          node(3, type="Feature", parent=2, body="Wiki: x"))
        self.assertEqual(for_issue(result, 3),
                         [("error", "is a feature under #2, a task; a feature sits under an epic")])

    def test_four_levels_deep(self):
        result = messages(node(1, type="Epic", body=EPIC_BODY), node(2, type="Feature", parent=1, body="Wiki: x"),
                          node(3, type="Task", parent=2), node(4, type="Task", parent=3))
        self.assertEqual(for_issue(result, 4), [("error", "sits 4 levels deep; the standard allows 3")])

    def test_three_levels_with_a_task_under_a_task_is_allowed(self):
        self.assertEqual(messages(node(1, type="Epic", body=EPIC_BODY), node(2, type="Task", parent=1),
                                  node(3, type="Task", parent=2)), [])


class Epics(unittest.TestCase):
    def test_epic_without_acceptance_criteria(self):
        result = messages(node(1, type="Epic", body="Just a bucket"), node(2, type="Task", parent=1))
        self.assertEqual(for_issue(result, 1)[0][1][:32], "is an epic without acceptance cr")

    def test_standing_epic_needs_no_acceptance_criteria(self):
        self.assertEqual(messages(node(1, type="Epic", body="A standing epic."), node(2, type="Task", parent=1)), [])

    def test_all_children_closed_proposes_closing(self):
        result = messages(node(1, type="Epic", body=EPIC_BODY), node(2, type="Task", parent=1, state="CLOSED"))
        self.assertEqual(result, [("warning", 1, "has every sub-issue closed; propose closing it to the owner")])

    def test_closed_epic_with_open_child(self):
        result = messages(node(1, type="Epic", body=EPIC_BODY, state="CLOSED"), node(2, type="Task", parent=1))
        self.assertEqual(result, [("error", 1, "is a closed epic with open sub-issues")])

    def test_closed_issues_are_not_checked(self):
        self.assertEqual(messages(node(1, state="CLOSED", labels=())), [])


class Wiki(unittest.TestCase):
    epic = node(1, type="Epic", body=EPIC_BODY)

    def test_feature_without_wiki_page_warns_or_errors(self):
        feature = node(2, type="Feature", parent=1)
        self.assertEqual([s for s, *_ in messages(self.epic, feature)], ["warning"])
        self.assertEqual([s for s, *_ in messages(self.epic, feature, require_wiki=True)], ["error"])

    def test_wiki_line_or_link_names_a_page(self):
        for body in ("- Wiki: [Page](https://github.com/acme/app/wiki/page)", "see https://github.com/acme/app/wiki/x",
                     "**Wiki page:** training-types.md"):
            self.assertEqual(messages(self.epic, node(2, type="Feature", parent=1, body=body)), [], body)


class ProseOrder(unittest.TestCase):
    epic = node(1, type="Epic", body=EPIC_BODY)

    def test_prose_dependency_without_native_link(self):
        result = messages(self.epic, node(3, type="Task", parent=1),
                          node(2, type="Task", parent=1, body="Depends on #3 and #4."))
        self.assertEqual(for_issue(result, 2), [("error", "writes `depends on #3` in prose; record it as a native blocked-by link"),
                                                ("error", "writes `depends on #4` in prose; record it as a native blocked-by link")])

    def test_native_link_satisfies_the_prose(self):
        self.assertEqual(messages(self.epic, node(3, type="Task", parent=1),
                                  node(2, type="Task", parent=1, body="Blocked by #3", blocked_by=[3])), [])

    def test_blocks_is_satisfied_by_the_other_issues_link(self):
        self.assertEqual(messages(self.epic, node(3, type="Task", parent=1, blocked_by=[2]),
                                  node(2, type="Task", parent=1, body="Blocks #3")), [])

    def test_code_and_comments_do_not_count(self):
        body = "Use `depends on #9` syntax.\n```\nBlocked by #8\n```\n<!-- blocked by #7 -->"
        self.assertEqual(messages(self.epic, node(2, type="Task", parent=1, body=body)), [])


class Run(unittest.TestCase):
    def run_main(self, pages, argv):
        responses = iter(pages)
        out = io.StringIO()
        with mock.patch.object(ci.tracker, "gh_graphql", side_effect=lambda *a, **k: next(responses)), \
                mock.patch("sys.argv", ["check-issues.py", *argv]), redirect_stdout(out):
            code = ci.main()
        return code, out.getvalue()

    def page(self, nodes, more=False):
        return {"repository": {"issues": {"pageInfo": {"hasNextPage": more, "endCursor": "c"}, "nodes": nodes}}}

    def test_pages_are_followed_and_errors_set_exit_code(self):
        code, out = self.run_main([self.page([node(1, type="Epic", body=EPIC_BODY)], more=True),
                                   self.page([node(2, type="Task")])], ["--repo", REPO])
        self.assertEqual(code, 1)
        self.assertIn("acme/app#2 has no parent epic", out)
        self.assertIn("2 open issues checked: 1 errors, 1 warnings", out)

    def test_clean_repos_exit_zero_and_every_repo_is_read(self):
        other = node(1, type="Bug")
        other["repository"] = {"nameWithOwner": "acme/other"}
        code, out = self.run_main([self.page([node(1, type="Bug")]), self.page([other])],
                                  ["--repo", REPO, "--repo", "acme/other"])
        self.assertEqual(code, 0)
        self.assertIn("2 open issues checked: 0 errors, 0 warnings", out)


if __name__ == "__main__":
    unittest.main()
