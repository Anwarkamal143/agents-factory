import json, pathlib, sys, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import backlog as b

LABELS = {"type:build", "type:decision", "type:spec", "ready-for-agent", "phase:1", "size:S", "size:L", "needs-info"}

BUILD = """---
id: %(id)s
title: "%(title)s"
type: build
labels: [type:build, ready-for-agent, phase:1, size:S]
blocked_by: [%(deps)s]
door: two-way
---
## Context
c
## What to build
w
## Demo path
d
## Acceptance criteria
- [ ] one
- [ ] two
- [ ] three
## Seams
s
## TDD plan
t
## Implementation notes
n {{%(ref)s}}
## Out of scope
o
## Decisions & questions
none
## Security & failure notes
none
## Definition of done
done
"""


def write(d, name, **kw):
    kw.setdefault("deps", "")
    kw.setdefault("ref", "T-01")
    kw.setdefault("title", "title " + kw["id"])
    (pathlib.Path(d) / name).write_text(BUILD % kw)


class T(unittest.TestCase):
    def mk(self, specs):
        d = tempfile.mkdtemp()
        for i, (tid, deps) in enumerate(specs):
            write(d, "%02d.md" % i, id=tid, deps=deps)
        return b.load_tickets(d)

    def test_parse_and_valid(self):
        ts = self.mk([("T-01", ""), ("T-02", "T-01")])
        self.assertEqual(ts["T-02"].blocked_by, ["T-01"])
        errs, _ = b.validate(ts, LABELS)
        self.assertEqual(errs, [])

    def test_missing_section_and_unknown_label_and_dep(self):
        d = tempfile.mkdtemp()
        txt = BUILD % dict(id="T-01", title="x", deps="T-99", ref="T-01")
        txt = txt.replace("## Seams\ns\n", "").replace("phase:1", "phase:77")
        (pathlib.Path(d) / "a.md").write_text(txt)
        errs, _ = b.validate(b.load_tickets(d), LABELS)
        joined = "\n".join(errs)
        self.assertIn("missing section '## Seams'", joined)
        self.assertIn("unknown label 'phase:77'", joined)
        self.assertIn("unknown id 'T-99'", joined)

    def test_cycle_detected(self):
        ts = self.mk([("T-01", "T-02"), ("T-02", "T-01")])
        errs, _ = b.validate(ts, LABELS)
        self.assertTrue(any("cycle" in e for e in errs))
        with self.assertRaises(ValueError):
            b.topo_order(ts)

    def test_too_few_acceptance_criteria(self):
        d = tempfile.mkdtemp()
        txt = (BUILD % dict(id="T-01", title="x", deps="", ref="T-01")).replace("- [ ] three\n", "")
        (pathlib.Path(d) / "a.md").write_text(txt)
        errs, _ = b.validate(b.load_tickets(d), LABELS)
        self.assertTrue(any(">=3 acceptance" in e for e in errs))

    def test_ready_for_agent_on_decision_rejected(self):
        d = tempfile.mkdtemp()
        (pathlib.Path(d) / "a.md").write_text("""---
id: DEC-01
title: x
type: decision
labels: [type:decision, ready-for-agent]
---
## Question
q
## Options
o
## Recommendation
r
## Default if unanswered
d
## Blocks
b
## Resolution
pending
""")
        errs, _ = b.validate(b.load_tickets(d), LABELS)
        self.assertTrue(any("non-pickable" in e for e in errs))

    def test_order_levels_critical_path(self):
        ts = self.mk([("T-01", ""), ("T-02", "T-01"), ("T-03", "T-01"), ("T-04", "T-02, T-03"), ("T-05", "")])
        order = b.topo_order(ts)
        self.assertEqual(order, ["T-01", "T-02", "T-03", "T-04", "T-05"])  # deterministic: smallest ready id first
        for k, t in ts.items():  # topological property: every blocker precedes its dependent
            for d in t.blocked_by:
                self.assertLess(order.index(d), order.index(k))
        lv = b.levels(ts)
        self.assertEqual((lv["T-01"], lv["T-02"], lv["T-04"], lv["T-05"]), (0, 1, 2, 0))
        self.assertEqual(b.critical_path(ts), ["T-01", "T-03", "T-04"])
        self.assertIn("T_01 --> T_02", b.mermaid(ts))

    def test_create_order_flags_and_rewrite(self):
        ts = self.mk([("T-01", ""), ("T-02", "T-01")])
        ts["T-02"].body = ts["T-02"].body.replace("{{T-01}}", "see {{T-01}}")

        class Fake:
            def __init__(s):
                s.calls, s.n = [], 100

            def run(s, cmd, stdin=None):
                s.calls.append((cmd, stdin))
                if cmd[:3] == ["gh", "issue", "create"]:
                    s.n += 1
                    return "https://github.com/o/r/issues/%d\n" % s.n
                return ""
        f = Fake()
        m = b.create(ts, f, apply=True, native_edges={"parent": False, "blocked_by": True})
        self.assertEqual(m, {"T-01": "#101", "T-02": "#102"})
        creates = [c for c, _ in f.calls if c[2] == "create"]
        self.assertEqual([c[4] for c in creates], ["[T-01] title T-01", "[T-02] title T-02"])  # blockers first
        self.assertIn("--blocked-by", creates[1])
        self.assertEqual(creates[1][creates[1].index("--blocked-by") + 1], "101")
        edits = [(c, s) for c, s in f.calls if c[2] == "edit"]
        self.assertEqual(len(edits), 2)
        t2_body = [s for c, s in edits if c[3] == "102"][0]
        self.assertIn("#101", t2_body)
        self.assertNotIn("{{T-01}}", t2_body)
        self.assertIn("<!-- blocked-by: #101 -->", t2_body)
        t1_body = [s for c, s in edits if c[3] == "101"][0]
        self.assertIn("<!-- blocks: #102 -->", t1_body)

    def test_dry_run_creates_nothing(self):
        ts = self.mk([("T-01", "")])

        class Boom:
            def run(s, *a, **k):
                raise AssertionError("must not run gh in dry-run")
        logs = []
        b.create(ts, Boom(), apply=False, log=logs.append)
        self.assertTrue(all(l.startswith("DRY-RUN") for l in logs))

    def test_frontier(self):
        def issue(n, state, labels, body=""):
            return {"number": n, "title": "t%d" % n, "state": state, "labels": [{"name": x} for x in labels], "body": body}
        issues = [
            issue(1, "CLOSED", ["ready-for-agent", "phase:1"]),
            issue(2, "OPEN", ["ready-for-agent", "phase:1"], "<!-- blocked-by: #1 -->"),
            issue(3, "OPEN", ["ready-for-agent", "phase:1"], "<!-- blocked-by: #2 -->"),
            issue(4, "OPEN", ["ready-for-agent", "type:spec"]),
            issue(5, "OPEN", ["ready-for-agent", "status:in-progress"]),
            issue(6, "OPEN", ["ready-for-agent", "needs-info"]),
        ]
        self.assertEqual([x[1] for x in b.frontier(issues)], [2])


if __name__ == "__main__":
    unittest.main()


GOOD_PR = """## Summary
```mermaid
flowchart LR
  A --> B
```
## Traceability
Closes #12
Part of #1
Phase: 2
Blocked by (merged): #9
Unblocks: #13, #14
Decisions applied: DEC-01
## Evidence
Before: no retry. After: 2 attempts (log excerpt).
## Acceptance criteria
- [x] flaky_then_success ends succeeded with 2 attempts
- [x] always_fails_same_way blocked after 2 attempts
## Merge danger
Door: two-way
Blast radius: task retry behaviour only
## Review log
| id | axis | severity | status |
|---|---|---|---|
| F-1 | spec | major | fixed in abc123 |
"""


class OnMerged(unittest.TestCase):
    def test_closes_unblocks_and_ledger(self):
        issues = {
            12: {"number": 12, "state": "OPEN", "title": "t12", "labels": [{"name": "status:in-review"}],
                 "body": "x\n<!-- blocks: #13,#14 -->"},
            13: {"number": 13, "state": "OPEN", "title": "t13", "labels": [{"name": "status:blocked"}],
                 "body": "x\n<!-- blocked-by: #12 -->"},
            14: {"number": 14, "state": "OPEN", "title": "t14", "labels": [],
                 "body": "x\n<!-- blocked-by: #12,#9 -->"},
            9: {"number": 9, "state": "OPEN", "title": "t9", "labels": [], "body": ""},
        }

        class Fake:
            def __init__(s):
                s.calls = []

            def run(s, cmd, stdin=None):
                s.calls.append(cmd)
                if cmd[:3] == ["gh", "issue", "view"]:
                    return json.dumps(issues[int(cmd[3])])
                if cmd[:3] == ["gh", "issue", "list"]:
                    return json.dumps([{"number": 1}])
                return ""
        f = Fake()
        pr = {"number": 50, "url": "https://x/pr/50", "title": "t", "body": GOOD_PR, "mergedAt": "2026-01-01",
              "mergeCommit": {"oid": "abcdef1234567890"}}
        actions = b.on_merged(pr, f, log=lambda *_: None)
        joined = "\n".join(actions)
        self.assertIn("gh issue edit 12 --remove-label status:in-review", joined)
        self.assertIn("gh issue comment 12 --body Closed by PR #50 (merge commit abcdef1234)", joined)
        self.assertIn("gh issue comment 13 --body Unblocked", joined)
        self.assertIn("gh issue edit 13 --remove-label status:blocked", joined)
        self.assertNotIn("gh issue comment 14", joined)  # still blocked by open #9
        self.assertIn("gh issue comment 1 --body Ledger: PR #50 closed #12; unblocked #13", joined)

    def test_unmerged_pr_is_noop(self):
        class Boom:
            def run(s, *a, **k):
                raise AssertionError("no gh calls for an unmerged PR")
        self.assertEqual(b.on_merged({"number": 1, "body": "Closes #2"}, Boom(), log=lambda *_: None), [])

    def test_closing_keywords(self):
        self.assertEqual(b.closing_issues("fixes #3 and Closes #10, resolved #3"), [3, 10])


class CheckPr(unittest.TestCase):
    def test_good_body_passes(self):
        self.assertEqual(b.check_pr_body(GOOD_PR), [])

    def test_each_requirement_is_enforced(self):
        cases = {
            "Closes #12": GOOD_PR.replace("Closes #12\n", ""),
            "Part of": GOOD_PR.replace("Part of #1\n", ""),
            "Unblocks:": GOOD_PR.replace("Unblocks: #13, #14\n", ""),
            "Mermaid": GOOD_PR.replace("```mermaid\nflowchart LR\n  A --> B\n```\n", ""),
            "Door": GOOD_PR.replace("Door: two-way\n", ""),
            "Blast radius": GOOD_PR.replace("Blast radius: task retry behaviour only\n", ""),
            "unchecked": GOOD_PR.replace("- [x] always", "- [ ] always"),
            "Review log": GOOD_PR.replace("| F-1 | spec | major | fixed in abc123 |\n", ""),
            "Evidence section": GOOD_PR.replace("## Evidence\n", "## Notes\n"),
        }
        for name, body in cases.items():
            self.assertTrue(b.check_pr_body(body), "expected a problem when removing: " + name)

    def test_two_closes_rejected_and_visual_none_allowed(self):
        self.assertTrue(any("exactly one" in e for e in b.check_pr_body(GOOD_PR + "\nCloses #99\n")))
        no_diagram = GOOD_PR.replace("```mermaid\nflowchart LR\n  A --> B\n```\n", "Visual: none (copy-only change)\n")
        self.assertEqual(b.check_pr_body(no_diagram), [])

    def test_no_findings_phrase_accepted(self):
        body = GOOD_PR.replace("| id | axis | severity | status |\n|---|---|---|---|\n| F-1 | spec | major | fixed in abc123 |\n", "No findings.\n")
        self.assertEqual(b.check_pr_body(body), [])


class TemplateIsEnforced(unittest.TestCase):
    """The blank PR template must FAIL check-pr, otherwise an unfilled PR would pass CI."""

    def find_template(self):
        here = pathlib.Path(__file__).resolve()
        for up in (here.parents[2] / "repo-files" / ".github", here.parents[3] / ".github"):
            if (up / "pull_request_template.md").exists():
                return (up / "pull_request_template.md").read_text()
        self.skipTest("template not found in this layout")

    def test_blank_template_fails_with_many_problems(self):
        errs = b.check_pr_body(self.find_template())
        self.assertGreaterEqual(len(errs), 6, errs)
        joined = " | ".join(errs)
        for needle in ("Closes #", "Part of #", "Blocked by (merged):", "Unblocks:", "Door", "Blast radius", "Mermaid"):
            self.assertIn(needle, joined)

    def test_comments_do_not_satisfy_requirements(self):
        body = GOOD_PR.replace("Closes #12", "<!-- Closes #12 -->")
        self.assertTrue(any("Closes #" in e for e in b.check_pr_body(body)))

    def test_placeholder_values_rejected(self):
        body = GOOD_PR.replace("Blast radius: task retry behaviour only", "Blast radius: <fill me>")
        self.assertTrue(any("Blast radius" in e for e in b.check_pr_body(body)))
        body = GOOD_PR.replace("Unblocks: #13, #14", "Unblocks: <list>")
        self.assertTrue(any("Unblocks:" in e for e in b.check_pr_body(body)))


class TableOutput(unittest.TestCase):
    def test_table_lists_blocks_in_both_directions(self):
        d = tempfile.mkdtemp()
        write(d, "a.md", id="T-01")
        write(d, "b.md", id="T-02", deps="T-01")
        out = b.table(b.load_tickets(d))
        rows = {l.split("|")[1].strip(): l for l in out.splitlines()[2:]}
        cols = [c.strip() for c in rows["T-01"].split("|")[1:-1]]
        self.assertEqual((cols[6], cols[7]), ("-", "T-02"))     # T-01 blocked by none, blocks T-02
        cols2 = [c.strip() for c in rows["T-02"].split("|")[1:-1]]
        self.assertEqual((cols2[6], cols2[7]), ("T-01", "-"))


class Linkify(unittest.TestCase):
    def test_ids_become_links_only_when_known_and_not_doubled(self):
        t = b.Ticket("T-02", "x", "build", [], ["T-01"], [], "two-way", "Read T-01 and T-99 and T-1.\n", "p")
        out = b.render_body(t, {"T-01": "#7", "T-02": "#8"}, {})
        self.assertIn("Read T-01 (#7) and T-99 and T-1.", out)      # known linked; unknown and short ids untouched
        again = b.render_body(t, {"T-01": "#7", "T-02": "#8"}, {})
        self.assertEqual(out, again)                                 # idempotent: rendered from the source each time
        self.assertEqual(out.count("(#7)"), 1)


class SkillCatalog(unittest.TestCase):
    def test_unknown_skill_warns_known_does_not(self):
        d = tempfile.mkdtemp()
        txt = BUILD % dict(id="T-01", title="x", deps="", ref="T-01")
        (pathlib.Path(d) / "a.md").write_text(txt.replace("door: two-way", "door: two-way\nskills: [tdd, not-a-skill]"))
        _, warns = b.validate(b.load_tickets(d), LABELS)
        self.assertTrue(any("not-a-skill" in w for w in warns))
        self.assertFalse(any("'tdd'" in w for w in warns))


class IdempotencyAndSync(unittest.TestCase):
    def test_existing_map_reads_footers(self):
        issues = [{"number": 5, "body": "x\n<!-- local-id: T-01 -->"}, {"number": 6, "body": "no footer"},
                  {"number": 7, "body": "<!-- local-id: DEC-02 -->"}]
        self.assertEqual(b.existing_map(issues), {"T-01": "#5", "DEC-02": "#7"})

    def test_sync_updates_every_body_with_current_links_and_no_creates(self):
        d = tempfile.mkdtemp()
        write(d, "a.md", id="T-01")
        write(d, "b.md", id="T-02", deps="T-01")
        ts = b.load_tickets(d)

        class Rec:
            def __init__(s): s.calls = []
            def run(s, cmd, stdin=None):
                s.calls.append((cmd, stdin)); return ""
        r = Rec()
        b.sync(ts, r, {"T-01": "#10", "T-02": "#11"}, apply=True)
        self.assertTrue(all(c[:3] == ["gh", "issue", "edit"] for c, _ in r.calls))   # never creates
        body2 = [s for c, s in r.calls if c[3] == "11"][0]
        self.assertIn("<!-- blocked-by: #10 -->", body2)
        body1 = [s for c, s in r.calls if c[3] == "10"][0]
        self.assertIn("<!-- blocks: #11 -->", body1)

    def test_sync_refuses_when_a_ticket_has_no_issue(self):
        d = tempfile.mkdtemp()
        write(d, "a.md", id="T-01")
        write(d, "b.md", id="T-02", deps="T-01")
        with self.assertRaises(RuntimeError) as cm:
            b.sync(b.load_tickets(d), object(), {"T-01": "#10"}, apply=True)
        self.assertIn("T-02", str(cm.exception))


class LedgerWarning(unittest.TestCase):
    def test_warns_when_no_open_spec_issue(self):
        issues = {3: {"number": 3, "state": "OPEN", "title": "t", "labels": [], "body": ""}}

        class Fake:
            def run(s, cmd, stdin=None):
                if cmd[:3] == ["gh", "issue", "view"]:
                    return json.dumps(issues[int(cmd[3])])
                if cmd[:3] == ["gh", "issue", "list"]:
                    return "[]"
                return ""
        logs = []
        b.on_merged({"number": 9, "url": "u", "body": "Closes #3", "mergedAt": "x", "mergeCommit": {"oid": "abc"}}, Fake(), log=logs.append)
        self.assertTrue(any("no open type:spec" in l for l in logs))
