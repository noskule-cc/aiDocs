import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from loader import load

tracker = load("tracker.py")
REPO = "acme/app"


def item(number, *, type=None, labels=(), parent=None):
    return {
        "status": {"name": "Backlog"}, "humanAction": None, "priority": None,
        "content": {
            "number": number, "title": f"Issue {number}", "state": "OPEN", "url": f"https://x/{number}", "body": "",
            "repository": {"nameWithOwner": REPO}, "milestone": None,
            "issueType": {"name": type} if type else None,
            "labels": {"nodes": [{"name": name} for name in labels]},
            "parent": {"number": parent} if parent else None,
            "blockedBy": {"nodes": []}, "comments": {"nodes": []},
        },
    }


def check_messages(*items):
    pages = iter([
        {"user": {"projectV2": {"fields": {"nodes": [{"name": "Status"}, {"name": "Priority"},
                                                    {"name": "Human action"}]},
                                "items": {"pageInfo": {"hasNextPage": False, "endCursor": None}, "nodes": list(items)}}}},
        {"repository": {"milestones": {"nodes": []},
                        "issues": {"pageInfo": {"hasNextPage": False, "endCursor": None},
                                   "nodes": [{"number": i["content"]["number"],
                                              "projectItems": {"nodes": [{"project": {"number": 1,
                                                                                      "owner": {"login": "acme"}}}]}}
                                             for i in items]}}},
    ])
    out = io.StringIO()
    with mock.patch.object(tracker, "gh_graphql", side_effect=lambda *a, **k: next(pages)), \
            mock.patch.object(tracker, "owner_kind", return_value="user"), redirect_stdout(out):
        tracker.cmd_check(*tracker.load_board("acme/1", REPO))
    return out.getvalue()


class TypeLabels(unittest.TestCase):
    def test_native_and_label_types_are_read_alike(self):
        self.assertEqual(tracker.single_type("Epic", []), "epic")
        self.assertEqual(tracker.single_type(None, ["ui", "type:Bug"]), "bug")
        self.assertEqual(tracker.single_type("Bug", ["type:bug"]), "bug")
        self.assertIsNone(tracker.single_type("Bug", ["type:task"]))
        self.assertIsNone(tracker.single_type(None, ["ui"]))

    def test_a_label_typed_bug_may_stay_parentless_and_a_label_typed_task_may_not(self):
        text = check_messages(item(1, labels=["type:bug"]), item(2, labels=["type:task"]))
        self.assertNotIn("#1 (Backlog) has no parent epic", text)
        self.assertIn("#2 (Backlog) has no parent epic", text)

    def test_a_label_typed_epic_is_not_warned_about(self):
        text = check_messages(item(1, labels=["type:epic"]))
        self.assertNotIn("no parent epic", text)


if __name__ == "__main__":
    unittest.main()
