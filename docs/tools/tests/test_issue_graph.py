import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from loader import load

ig = load("issue-graph.py")


def node(number, state="OPEN", blocked_by=(), children=None, title=None, repo="acme/app", more_blockers=False,
         more_children=False):
    """blocked_by: (number, state) or (number, state, repo)."""
    blockers = [{"number": b[0], "title": f"Outer {b[0]}", "state": b[1],
                 "repository": {"nameWithOwner": b[2] if len(b) > 2 else "acme/app"}} for b in blocked_by]
    result = {"number": number, "title": title or f"Issue {number}", "state": state,
              "repository": {"nameWithOwner": repo},
              "blockedBy": {"pageInfo": {"hasNextPage": more_blockers}, "nodes": blockers}}
    if children is not None:
        result["subIssues"] = {"pageInfo": {"hasNextPage": more_children}, "nodes": children}
    return result


def epic(*children, body="Intro", more_children=False):
    return {**node(1, children=list(children), more_children=more_children), "body": body}


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


class CrossRepository(unittest.TestCase):
    def block(self, *children):
        return ig.render(ig.tree(epic(*children)))

    def test_blocker_from_another_repo_is_not_the_local_issue_of_the_same_number(self):
        text = self.block(node(5, title="local five"), node(7, blocked_by=[(5, "CLOSED", "acme/other")]))
        self.assertIn('i5["#5 local five"]', text)
        self.assertIn('i5_acme_other["acme/other#5 Outer 5<br>outside this epic"]', text)
        self.assertIn("i5_acme_other --> i7", text)
        self.assertNotIn("i5 --> i7", text)
        self.assertIn("class i5_acme_other outside", text)
        self.assertIn("class i5_acme_other closed", text)

    def test_sub_issue_from_another_repo_keeps_its_own_node(self):
        text = self.block(node(5, title="local five"), node(5, repo="acme/other", title="their five"),
                          node(7, blocked_by=[(5, "OPEN", "acme/other")]))
        self.assertIn('i5_acme_other["acme/other#5 their five"]', text)
        self.assertIn("i5_acme_other --> i7", text)
        self.assertNotIn("outside this epic", text)


class Splice(unittest.TestCase):
    def test_appends_then_replaces_in_place_and_a_rerun_changes_nothing(self):
        first = ig.splice("Intro\n", "GRAPH 1")
        self.assertEqual(first, f"Intro\n\n{ig.START}\nGRAPH 1\n{ig.END}\n")
        second = ig.splice(first + "\nTail\n", "GRAPH 2")
        self.assertEqual(second, f"Intro\n\n{ig.START}\nGRAPH 2\n{ig.END}\n\nTail\n")
        self.assertEqual(ig.splice(second, "GRAPH 2"), second)

    def test_start_without_end_is_refused_so_notes_after_it_survive(self):
        body = f"Intro\n{ig.START}\nold graph\n\nMy notes\n"
        with self.assertRaisesRegex(ValueError, "1 start and 0 end"):
            ig.splice(body, "G")

    def test_end_without_start_and_reversed_markers_are_refused(self):
        for body in (f"a\n{ig.END}\n", f"a\n{ig.END}\nmiddle\n{ig.START}\n"):
            with self.assertRaises(ValueError):
                ig.splice(body, "G")

    def test_two_pairs_with_text_between_are_refused(self):
        body = f"{ig.START}\nA\n{ig.END}\nMy notes\n{ig.START}\nB\n{ig.END}\n"
        with self.assertRaisesRegex(ValueError, "2 start and 2 end"):
            ig.splice(body, "G")

    def test_text_after_the_end_marker_survives(self):
        body = f"Intro\n{ig.START}\nold\n{ig.END}\nMy notes\n"
        self.assertEqual(ig.splice(body, "G"), f"Intro\n{ig.START}\nG\n{ig.END}\nMy notes\n")


class Run(unittest.TestCase):
    def run_main(self, argv, issue, out=None):
        out = out or io.StringIO()
        with mock.patch.object(ig.tracker, "gh_graphql", return_value={"repository": {"issue": issue}}), \
                mock.patch.object(ig.subprocess, "run") as run, \
                mock.patch("sys.argv", ["issue-graph.py", *argv]), redirect_stdout(out), \
                redirect_stderr(io.StringIO()) as err:
            run.return_value.returncode = 0
            try:
                code = ig.main()
            finally:
                self.run, self.err = run, err.getvalue()
        return code, getattr(out, "getvalue", str)(), run

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

    def test_write_refuses_broken_markers_and_edits_nothing(self):
        body = f"Intro\n{ig.START}\nold\n\nMy notes\n"
        with self.assertRaisesRegex(SystemExit, "1 start and 0 end"):
            self.run_main(["1", "--repo", "acme/app", "--write"], epic(node(2), body=body))
        self.run.assert_not_called()

    def test_output_survives_a_cp1252_redirect(self):
        raw = io.BytesIO()
        out = io.TextIOWrapper(raw, encoding="cp1252", errors="strict")
        self.run_main(["1", "--repo", "acme/app"], epic(node(2)), out=out)
        out.flush()
        self.assertIn("blocker → blocked".encode("utf-8"), raw.getvalue())

    def test_a_full_page_warns_and_write_refuses(self):
        cut_blockers = epic(node(2, more_blockers=True))
        code, _, run = self.run_main(["1", "--repo", "acme/app"], cut_blockers)
        self.assertEqual(code, 0)
        self.assertIn("acme/app#2", self.err)
        for issue in (cut_blockers, epic(node(2), more_children=True)):
            with self.assertRaisesRegex(SystemExit, "incomplete"):
                self.run_main(["1", "--repo", "acme/app", "--write"], issue)
            self.run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
