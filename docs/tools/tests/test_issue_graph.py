import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from loader import load

ig = load("issue-graph.py")


def node(number, state="OPEN", blocked_by=(), children=None, title=None):
    result = {"number": number, "title": title or f"Issue {number}", "state": state,
              "blockedBy": {"nodes": [{"number": n, "title": f"Outer {n}", "state": s,
                                       "repository": {"nameWithOwner": "acme/app"}} for n, s in blocked_by]}}
    if children is not None:
        result["subIssues"] = {"nodes": children}
    return result


def epic(*children, body="Intro"):
    return {**node(1, children=list(children)), "body": body}


class Render(unittest.TestCase):
    def block(self, *children):
        return ig.render(ig.tree(epic(*children)))

    def test_features_group_their_tasks_and_blocked_by_draws_an_arrow(self):
        text = self.block(node(2, children=[node(3), node(4, blocked_by=[(3, "OPEN")])]),
                          node(5, blocked_by=[(2, "OPEN")]))
        self.assertIn('subgraph i2["#2 Issue 2"]', text)
        self.assertIn('i3["#3 Issue 3"]', text)
        self.assertIn("i3 --> i4", text)
        self.assertIn("i2 --> i5", text)

    def test_blocker_outside_the_epic_is_shown_dashed_and_closed_ones_green(self):
        text = self.block(node(2, state="CLOSED", blocked_by=[(90, "OPEN")]))
        self.assertIn('i90["#90 Outer 90<br>outside this epic"]', text)
        self.assertIn("class i90 outside", text)
        self.assertIn("class i2 closed", text)

    def test_quotes_and_long_titles_are_made_safe(self):
        text = self.block(node(2, title='Say "hi" ' + "x" * 80))
        self.assertIn("Say 'hi'", text)
        self.assertIn("…", text)


class Splice(unittest.TestCase):
    def test_appends_then_replaces_in_place_and_a_rerun_changes_nothing(self):
        first = ig.splice("Intro\n", "GRAPH 1")
        self.assertEqual(first, f"Intro\n\n{ig.START}\nGRAPH 1\n{ig.END}\n")
        second = ig.splice(first + "\nTail\n", "GRAPH 2")
        self.assertEqual(second, f"Intro\n\n{ig.START}\nGRAPH 2\n{ig.END}\n\nTail\n")
        self.assertEqual(ig.splice(second, "GRAPH 2"), second)


class Run(unittest.TestCase):
    def run_main(self, argv, issue):
        out = io.StringIO()
        with mock.patch.object(ig.tracker, "gh_graphql", return_value={"repository": {"issue": issue}}), \
                mock.patch.object(ig.subprocess, "run") as run, \
                mock.patch("sys.argv", ["issue-graph.py", *argv]), redirect_stdout(out):
            run.return_value.returncode = 0
            code = ig.main()
        return code, out.getvalue(), run

    def test_default_prints_and_does_not_edit_the_issue(self):
        code, out, run = self.run_main(["1", "--repo", "acme/app"], epic(node(2)))
        self.assertEqual(code, 0)
        self.assertIn("flowchart LR", out)
        run.assert_not_called()

    def test_write_edits_the_body_once_and_skips_when_current(self):
        _, out, run = self.run_main(["1", "--repo", "acme/app", "--write"], epic(node(2)))
        self.assertIn("written", out)
        body = run.call_args.kwargs["input"]
        self.assertTrue(body.startswith("Intro\n\n" + ig.START))
        _, out, run = self.run_main(["1", "--repo", "acme/app", "--write"], epic(node(2), body=body))
        self.assertIn("already current", out)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
