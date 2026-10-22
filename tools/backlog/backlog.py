#!/usr/bin/env python3
"""backlog.py: validate / graph / create / next for the agents-factory ticket set.

Stdlib only. Subcommands:
  validate            check every ticket file (sections, labels, deps, cycles)
  graph               print Mermaid DAG, topological order, levels, critical path
  create [--apply]    create GitHub issues in dependency order (dry-run by default)
  sync [--apply]      re-render issue bodies from ticket files after edits (dry-run by default)
  next [--json FILE]  list tickets an agent may pick now (the frontier)
  on-merged --pr N    after a PR merges: tidy labels, comment, unblock dependents, ledger on the spec
  check-pr            read a PR body on stdin/--body-file; fail if linkage/evidence sections are missing
"""
import argparse, collections, json, pathlib, re, subprocess, sys

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent


def find_root():
    """Locate the backlog root (the directory holding tickets/). Order: $BACKLOG_ROOT,
    script parent (delivery layout), <repo>/docs/backlog (repo layout: tools/backlog/backlog.py)."""
    import os
    cands = []
    if os.environ.get("BACKLOG_ROOT"):
        cands.append(pathlib.Path(os.environ["BACKLOG_ROOT"]))
    cands += [SCRIPT_DIR.parent, SCRIPT_DIR.parent.parent / "docs" / "backlog"]
    for c in cands:
        if (c / "tickets").is_dir():
            return c
    return SCRIPT_DIR.parent


ROOT = find_root()
ALLOWED_TYPES = {"spec", "map", "decision", "spike", "build", "chore", "retro"}
REQUIRED = {
    "build": ["Context", "What to build", "Demo path", "Acceptance criteria", "Seams",
              "TDD plan", "Implementation notes", "Out of scope", "Decisions & questions",
              "Security & failure notes", "Definition of done"],
    "chore": ["Context", "What to build", "Acceptance criteria", "Out of scope", "Definition of done"],
    "decision": ["Question", "Options", "Recommendation", "Default if unanswered", "Blocks", "Resolution"],
    "spike": ["Question", "Method", "Output", "Blocks"],
    "retro": ["Scope", "Output"],
    "map": ["Destination", "Decisions so far", "Not yet specified", "Out of scope"],
    "spec": ["Problem", "Seams", "Implementation decisions", "Testing decisions", "Out of scope"],
}
# Snapshot of the AI Hero skills catalog (27 skills, v1.3, https://www.aihero.dev/skills). Update when it changes.
KNOWN_SKILLS = {"setup-matt-pocock-skills", "ask-matt", "grill-with-docs", "to-spec", "to-tickets", "implement",
                "code-review", "retro", "wayfinder", "prototype", "research", "improve-codebase-architecture",
                "diagnosing-bugs", "triage", "wizard", "implement-spec", "grill-me", "handoff", "to-questionnaire",
                "teach", "wait-what", "writing-for-agents", "pr", "codebase-design", "domain-modeling", "grilling", "tdd"}
NOT_AGENT_PICKABLE = {"type:spec", "type:decision", "wayfinder:map", "type:retro"}
PATH_LINE = re.compile(r"\b[\w./-]+\.(?:py|ts|js|md|yaml|json):\d+\b")


class Ticket:
    def __init__(self, id, title, type, labels, blocked_by, skills, door, body, path):
        self.id, self.title, self.type = id, title, type
        self.labels, self.blocked_by, self.skills = labels, blocked_by, skills
        self.door, self.body, self.path = door, body, path

    def sections(self):
        return [m.group(1).strip() for m in re.finditer(r"^## (.+)$", self.body, re.M)]

    def section_text(self, name):
        m = re.search(r"^## %s\s*\n(.*?)(?=^## |\Z)" % re.escape(name), self.body, re.M | re.S)
        return m.group(1).strip() if m else ""


def parse_list(v):
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        v = v[1:-1]
    return [x.strip() for x in v.split(",") if x.strip()]


def parse_ticket(path):
    text = pathlib.Path(path).read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError("%s: missing front matter" % path)
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith("#"):
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    for req in ("id", "title", "type"):
        if req not in meta:
            raise ValueError("%s: front matter missing '%s'" % (path, req))
    return Ticket(meta["id"], meta["title"].strip('"'), meta["type"], parse_list(meta.get("labels", "")),
                  parse_list(meta.get("blocked_by", "")), parse_list(meta.get("skills", "")),
                  meta.get("door", ""), m.group(2).strip() + "\n", str(path))


def load_tickets(directory=None):
    directory = pathlib.Path(directory or ROOT / "tickets")
    out = {}
    for p in sorted(directory.glob("*.md")):
        t = parse_ticket(p)
        if t.id in out:
            raise ValueError("duplicate id %s (%s, %s)" % (t.id, out[t.id].path, p))
        out[t.id] = t
    return out


def allowed_labels():
    for cand in (ROOT / "labels.json", ROOT / "repo-files" / "labels.json"):
        if cand.exists():
            return {l["name"] for l in json.load(open(cand))}
    raise FileNotFoundError("labels.json not found under %s" % ROOT)


def find_cycle(tickets):
    WHITE, GREY, BLACK = 0, 1, 2
    color = {k: WHITE for k in tickets}
    stack = []

    def visit(n):
        color[n] = GREY
        stack.append(n)
        for d in tickets[n].blocked_by:
            if d not in tickets:
                continue
            if color[d] == GREY:
                return stack[stack.index(d):] + [d]
            if color[d] == WHITE:
                c = visit(d)
                if c:
                    return c
        color[n] = BLACK
        stack.pop()
        return None

    for k in sorted(tickets):
        if color[k] == WHITE:
            c = visit(k)
            if c:
                return c
    return None


def validate(tickets, labels=None):
    errors, warnings = [], []
    labels = labels if labels is not None else allowed_labels()
    for t in tickets.values():
        if t.type not in ALLOWED_TYPES:
            errors.append("%s: unknown type '%s'" % (t.id, t.type))
            continue
        have = t.sections()
        for need in REQUIRED[t.type]:
            if need not in have:
                errors.append("%s: missing section '## %s'" % (t.id, need))
            elif not t.section_text(need):
                errors.append("%s: section '## %s' is empty" % (t.id, need))
        for l in t.labels:
            if l not in labels:
                errors.append("%s: unknown label '%s'" % (t.id, l))
        for d in t.blocked_by:
            if d not in tickets:
                errors.append("%s: blocked_by unknown id '%s'" % (t.id, d))
            if d == t.id:
                errors.append("%s: blocks itself" % t.id)
        if t.type == "build":
            ac = re.findall(r"^- \[ \] ", t.section_text("Acceptance criteria"), re.M)
            if len(ac) < 3:
                errors.append("%s: needs >=3 acceptance criteria checkboxes (has %d)" % (t.id, len(ac)))
            if "size:L" in t.labels and "ready-for-agent" in t.labels:
                errors.append("%s: size:L must be split before ready-for-agent" % t.id)
            if not t.door:
                errors.append("%s: front matter 'door' (one-way|two-way) required" % t.id)
        if set(t.labels) & NOT_AGENT_PICKABLE and "ready-for-agent" in t.labels:
            errors.append("%s: ready-for-agent on a non-pickable type" % t.id)
        if t.type in ("build", "chore") and "ready-for-agent" not in t.labels and "ready-for-human" not in t.labels:
            warnings.append("%s: no ready-for-agent/ready-for-human label" % t.id)
        for sk in t.skills:
            if sk not in KNOWN_SKILLS:
                warnings.append("%s: skill '%s' is not in the AI Hero catalog snapshot (typo, or update KNOWN_SKILLS)" % (t.id, sk))
        if PATH_LINE.search(t.body):
            warnings.append("%s: body contains file:line reference (tickets should name behaviour/modules)" % t.id)
    cyc = find_cycle(tickets)
    if cyc:
        errors.append("dependency cycle: " + " -> ".join(cyc))
    return errors, warnings


def topo_order(tickets):
    indeg = {k: len([d for d in v.blocked_by if d in tickets]) for k, v in tickets.items()}
    dependents = collections.defaultdict(list)
    for k, v in tickets.items():
        for d in v.blocked_by:
            if d in tickets:
                dependents[d].append(k)
    ready = sorted(k for k, n in indeg.items() if n == 0)
    order = []
    while ready:
        n = ready.pop(0)
        order.append(n)
        for m in sorted(dependents[n]):
            indeg[m] -= 1
            if indeg[m] == 0:
                ready.append(m)
                ready.sort()
    if len(order) != len(tickets):
        raise ValueError("cycle detected; cannot order")
    return order


def levels(tickets):
    lvl = {}
    for n in topo_order(tickets):
        deps = [d for d in tickets[n].blocked_by if d in tickets]
        lvl[n] = 0 if not deps else 1 + max(lvl[d] for d in deps)
    return lvl


def critical_path(tickets):
    best, prev = {}, {}
    for n in topo_order(tickets):
        deps = [d for d in tickets[n].blocked_by if d in tickets]
        if deps:
            p = max(deps, key=lambda d: (best[d], d))
            best[n], prev[n] = best[p] + 1, p
        else:
            best[n] = 1
    end = max(best, key=lambda k: (best[k], k))
    path = [end]
    while path[-1] in prev:
        path.append(prev[path[-1]])
    return list(reversed(path))


def mermaid(tickets):
    lines = ["flowchart TD"]
    style = {"decision": "fill:#fff3cd,stroke:#b58900", "spike": "fill:#e1ecf7,stroke:#1d76db",
             "retro": "fill:#ece4f7,stroke:#5319e7", "chore": "fill:#e6f0f0,stroke:#5f8a8b",
             "build": "fill:#e6f4ea,stroke:#0e8a16", "map": "fill:#ece4f7,stroke:#5319e7",
             "spec": "fill:#ece4f7,stroke:#5319e7"}
    for k in topo_order(tickets):
        t = tickets[k]
        title = t.title.replace('"', "'")
        title = title if len(title) <= 46 else title[:43] + "..."
        lines.append('  %s["%s<br/>%s"]' % (k.replace("-", "_"), k, title))
    for k in topo_order(tickets):
        for d in tickets[k].blocked_by:
            if d in tickets:
                lines.append("  %s --> %s" % (d.replace("-", "_"), k.replace("-", "_")))
    for k in tickets:
        lines.append("  style %s %s" % (k.replace("-", "_"), style[tickets[k].type]))
    return "\n".join(lines)


# ---------- create ----------
class GhRunner:
    def run(self, cmd, stdin=None):
        return subprocess.run(cmd, input=stdin, capture_output=True, text=True, check=True).stdout


def render_body(t, mapping, blocks):
    body = t.body

    def sub(m):
        return mapping.get(m.group(1), "{{%s}}" % m.group(1))
    body = re.sub(r"\{\{([A-Z]+-\d+)\}\}", sub, body)
    # make bare ticket ids clickable once their issue number is known: "T-05" -> "T-05 (#42)"
    body = re.sub(r"\b((?:T|DEC|SPK|MAP|SPEC|RET)-\d+)\b(?! \(#)",
                  lambda m: "%s (%s)" % (m.group(1), mapping[m.group(1)]) if m.group(1) in mapping else m.group(1), body)
    foot = ["", "---", "<!-- local-id: %s -->" % t.id]
    bb = [mapping[d] for d in t.blocked_by if d in mapping]
    if bb:
        foot.append("<!-- blocked-by: %s -->" % ",".join(bb))
    bl = [mapping[b] for b in blocks.get(t.id, []) if b in mapping]
    if bl:
        foot.append("<!-- blocks: %s -->" % ",".join(bl))
    return body.rstrip() + "\n" + "\n".join(foot) + "\n"


def create(tickets, runner, apply=False, repo=None, native_edges=None, log=print):
    """Create issues blockers-first. Returns mapping local-id -> '#N'."""
    order = topo_order(tickets)
    blocks = collections.defaultdict(list)
    for k, v in tickets.items():
        for d in v.blocked_by:
            blocks[d].append(k)
    if native_edges is None:
        native_edges = {"parent": False, "blocked_by": False}
    spec_id = next((k for k, v in tickets.items() if v.type == "spec"), None)
    mapping = {}
    repo_args = ["--repo", repo] if repo else []
    counter = 0
    for k in order:
        t = tickets[k]
        cmd = ["gh", "issue", "create", "--title", "[%s] %s" % (t.id, t.title), "--body-file", "-"] + repo_args
        for l in t.labels:
            cmd += ["--label", l]
        if native_edges["parent"] and spec_id and k != spec_id and spec_id in mapping:
            cmd += ["--parent", mapping[spec_id].lstrip("#")]
        bb = [mapping[d].lstrip("#") for d in t.blocked_by if d in mapping]
        if native_edges["blocked_by"] and bb:
            cmd += ["--blocked-by", ",".join(bb)]
        body = render_body(t, mapping, blocks)
        if apply:
            out = runner.run(cmd, stdin=body)
            m = re.search(r"/issues/(\d+)", out)
            if not m:
                raise RuntimeError("could not parse issue number for %s from: %r" % (k, out))
            mapping[k] = "#" + m.group(1)
        else:
            counter += 1
            mapping[k] = "#%d" % counter
            log("DRY-RUN %s" % " ".join(cmd))
    # second pass: all numbers known, rewrite bodies (placeholders + blocks footers)
    for k in order:
        t = tickets[k]
        body = render_body(t, mapping, blocks)
        cmd = ["gh", "issue", "edit", mapping[k].lstrip("#"), "--body-file", "-"] + repo_args
        if apply:
            runner.run(cmd, stdin=body)
        else:
            log("DRY-RUN %s" % " ".join(cmd))
    return mapping


def existing_map(issues):
    """Map local ids to '#N' from issues that already carry a '<!-- local-id: X -->' footer."""
    out = {}
    for i in issues:
        m = re.search(r"<!-- local-id: ([A-Z]+-\d+) -->", i.get("body") or "")
        if m:
            out[m.group(1)] = "#%d" % i["number"]
    return out


def sync(tickets, runner, existing, apply=False, repo=None, log=print):
    """Re-render and update the body of every already-created issue from its ticket file.
    Refuses if any ticket has no issue yet (create those first)."""
    missing = sorted(set(tickets) - set(existing))
    if missing:
        raise RuntimeError("tickets without an issue: %s (run `create` for a fresh repo, or file them by hand)" % ", ".join(missing))
    blocks = collections.defaultdict(list)
    for k, v in tickets.items():
        for d in v.blocked_by:
            blocks[d].append(k)
    repo_args = ["--repo", repo] if repo else []
    for k in topo_order(tickets):
        cmd = ["gh", "issue", "edit", existing[k].lstrip("#"), "--body-file", "-"] + repo_args
        body = render_body(tickets[k], existing, blocks)
        if apply:
            runner.run(cmd, stdin=body)
        else:
            log("DRY-RUN %s" % " ".join(cmd))
    return existing


# ---------- next (frontier) ----------
def frontier(issues):
    by_num = {i["number"]: i for i in issues}
    out = []
    for i in issues:
        names = {l["name"] if isinstance(l, dict) else l for l in i.get("labels", [])}
        if i.get("state", "").upper() != "OPEN" or "ready-for-agent" not in names:
            continue
        if names & NOT_AGENT_PICKABLE or names & {"status:in-progress", "status:in-review", "status:blocked",
                                                  "status:needs-decision", "needs-info"}:
            continue
        m = re.search(r"<!-- blocked-by: ([#\d,]+) -->", i.get("body", "") or "")
        blockers = [int(x) for x in re.findall(r"\d+", m.group(1))] if m else []
        if all(by_num.get(b, {}).get("state", "").upper() == "CLOSED" for b in blockers):
            phase = next((n for n in sorted(names) if n.startswith("phase:")), "phase:9")
            out.append((phase, i["number"], i["title"]))
    return sorted(out)


def table(tickets):
    """Markdown table of every ticket with its dependencies (generated; never hand-edited)."""
    blocks = collections.defaultdict(list)
    for k, v in tickets.items():
        for d in v.blocked_by:
            blocks[d].append(k)

    def pick(t, prefix):
        return next((l.split(":", 1)[1] for l in t.labels if l.startswith(prefix)), "-")
    rows = ["| ID | Type | Phase | Mode | Size | Title | Blocked by | Blocks | Skills |",
            "|---|---|---|---|---|---|---|---|---|"]
    for k in topo_order(tickets):
        t = tickets[k]
        rows.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            k, t.type, pick(t, "phase:"), pick(t, "mode:"), pick(t, "size:"), t.title.replace("|", "/"),
            ", ".join(t.blocked_by) or "-", ", ".join(sorted(blocks[k])) or "-", ", ".join(t.skills) or "-"))
    return "\n".join(rows)


# ---------- on-merged (close the loop after a PR merges) ----------
CLOSE_RE = re.compile(r"(?i)\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)")
FOOTER_RE = lambda name: re.compile(r"<!-- %s: ([#\d,]+) -->" % name)


def closing_issues(body):
    return sorted({int(n) for n in CLOSE_RE.findall(body or "")})


def _nums(body, name):
    m = FOOTER_RE(name).search(body or "")
    return [int(x) for x in re.findall(r"\d+", m.group(1))] if m else []


def on_merged(pr, runner, log=print):
    """After a merged PR: tidy status labels, comment on each closed issue, unblock dependents,
    and add a ledger comment on the spec issue. `pr` = {number,url,title,body,mergeCommit:{oid}}."""
    if not pr.get("mergedAt") and not pr.get("merged"):
        log("PR not merged; nothing to do")
        return []
    sha = (pr.get("mergeCommit") or {}).get("oid", "")[:10]
    closes = closing_issues(pr.get("body"))
    actions = []

    def run(cmd):
        actions.append(" ".join(cmd))
        return runner.run(cmd)

    def view(n):
        return json.loads(runner.run(["gh", "issue", "view", str(n), "--json", "number,state,body,labels,title"]))

    unblocked = []
    for n in closes:
        issue = view(n)
        names = {l["name"] if isinstance(l, dict) else l for l in issue.get("labels", [])}
        for lab in ("status:in-progress", "status:in-review", "status:blocked"):
            if lab in names:
                run(["gh", "issue", "edit", str(n), "--remove-label", lab])
        run(["gh", "issue", "comment", str(n), "--body",
             "Closed by PR #%s (merge commit %s): %s" % (pr["number"], sha or "n/a", pr.get("url", ""))])
        for d in _nums(issue.get("body"), "blocks"):
            dep = view(d)
            if dep["state"].upper() == "CLOSED":
                continue
            blockers = _nums(dep.get("body"), "blocked-by")
            states = {b: ("CLOSED" if b in closes else view(b)["state"].upper()) for b in blockers}
            if all(v == "CLOSED" for v in states.values()):
                run(["gh", "issue", "comment", str(d), "--body",
                     "Unblocked: all blockers are closed (last: #%d via PR #%s). Eligible for pickup." % (n, pr["number"])])
                dep_names = {l["name"] if isinstance(l, dict) else l for l in dep.get("labels", [])}
                if "status:blocked" in dep_names:
                    run(["gh", "issue", "edit", str(d), "--remove-label", "status:blocked"])
                unblocked.append(d)
    spec = json.loads(runner.run(["gh", "issue", "list", "--label", "type:spec", "--state", "open",
                                  "--json", "number", "--limit", "1"]) or "[]")
    if not spec and closes:
        log("WARNING: no open type:spec issue found; ledger line skipped (keep the spec issue open until the project ends)")
    if spec and closes:
        run(["gh", "issue", "comment", str(spec[0]["number"]), "--body",
             "Ledger: PR #%s closed %s%s." % (pr["number"], ", ".join("#%d" % n for n in closes),
                                              ("; unblocked " + ", ".join("#%d" % d for d in unblocked)) if unblocked else "")])
    return actions


# ---------- check-pr (PR body linkage and completeness) ----------
PR_SECTIONS = ["Summary", "Traceability", "Evidence", "Acceptance criteria", "Merge danger", "Review log"]


def check_pr_body(body):
    body = re.sub(r"<!--.*?-->", "", body or "", flags=re.S)  # comments and placeholders never count as content
    errs = []
    for sec in PR_SECTIONS:
        if not re.search(r"^## %s\s*$" % re.escape(sec), body or "", re.M | re.I):
            errs.append("missing section '## %s'" % sec)
    if not CLOSE_RE.search(body or ""):
        errs.append("Traceability must contain 'Closes #<ticket>' (one ticket per PR)")
    if len(set(CLOSE_RE.findall(body or ""))) > 1:
        errs.append("a PR closes exactly one ticket (found several 'Closes #')")
    if not re.search(r"(?im)^\s*Part of:?\s+#\d+", body or ""):
        errs.append("Traceability must contain 'Part of #<spec issue>'")
    for field in ("Blocked by (merged):", "Unblocks:"):
        if not re.search(r"(?im)^\s*%s\s*(none\b|#\d+)" % re.escape(field), body):
            errs.append("Traceability needs '%s #<n>[, #<m>]' or 'none'" % field)
    if "```mermaid" not in (body or "") and "visual: none" not in (body or "").lower():
        errs.append("Summary needs a Mermaid diagram, or an explicit 'Visual: none (<reason>)'")
    if not re.search(r"(?im)^\s*Door:\s*(one-way|two-way)", body or ""):
        errs.append("Merge danger must state 'Door: one-way' or 'Door: two-way'")
    if not re.search(r"(?im)^\s*Blast radius:\s*[^<\s]", body or ""):
        errs.append("Merge danger must state 'Blast radius: ...'")
    ac = re.search(r"^## Acceptance criteria\s*\n(.*?)(?=^## |\Z)", body or "", re.M | re.S | re.I)
    if ac and "- [" not in ac.group(1):
        errs.append("Acceptance criteria section needs checkbox items copied from the ticket")
    if ac and "- [ ]" in ac.group(1):
        errs.append("unchecked acceptance criteria remain; check each with evidence or do not open the PR")
    rl = re.search(r"^## Review log\s*\n(.*?)(?=^## |\Z)", body or "", re.M | re.S | re.I)
    if rl and not re.search(r"\|\s*F-\d+|no findings", rl.group(1), re.I):
        errs.append("Review log needs a findings table (rows 'F-1 ...') or the words 'No findings'")
    return errs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate")
    sub.add_parser("graph")
    sub.add_parser("table")
    c = sub.add_parser("create")
    c.add_argument("--apply", action="store_true", help="actually create issues (default: dry-run)")
    c.add_argument("--repo", help="owner/name (default: current repo)")
    n = sub.add_parser("next")
    n.add_argument("--json", help="issues JSON file (default: gh issue list)")
    sy = sub.add_parser("sync")
    sy.add_argument("--apply", action="store_true", help="actually update issue bodies (default: dry-run)")
    sy.add_argument("--repo", help="owner/name (default: current repo)")
    om = sub.add_parser("on-merged")
    om.add_argument("--pr", required=True, help="PR number")
    cp = sub.add_parser("check-pr")
    cp.add_argument("--body-file", help="file with the PR body (default: read from stdin)")
    a = ap.parse_args(argv)
    if a.cmd == "check-pr":
        body = open(a.body_file).read() if a.body_file else sys.stdin.read()
        errs = check_pr_body(body)
        for e in errs:
            print("ERROR", e)
        print("PR body OK" if not errs else "%d problem(s)" % len(errs))
        return 1 if errs else 0
    if a.cmd == "sync":
        errs, _ = validate(tickets)
        if errs:
            print("validation failed; run `backlog.py validate`", file=sys.stderr)
            return 1
        runner = GhRunner()
        existing = existing_map(json.loads(runner.run(["gh", "issue", "list", "--state", "all", "--limit", "1000",
                                                       "--json", "number,body"] + (["--repo", a.repo] if a.repo else []))))
        try:
            sync(tickets, runner, existing, apply=a.apply, repo=a.repo)
        except RuntimeError as e:
            print(str(e), file=sys.stderr)
            return 1
        print("synced %d issue bodies" % len(existing) if a.apply else "dry-run complete (no issues changed)")
        return 0
    if a.cmd == "on-merged":
        runner = GhRunner()
        pr = json.loads(runner.run(["gh", "pr", "view", a.pr, "--json", "number,url,title,body,mergeCommit,mergedAt"]))
        for line in on_merged(pr, runner):
            print("DONE", line)
        return 0
    tickets = load_tickets()
    if a.cmd == "validate":
        errs, warns = validate(tickets)
        for w in warns:
            print("WARN ", w)
        for e in errs:
            print("ERROR", e)
        print("%d tickets, %d errors, %d warnings" % (len(tickets), len(errs), len(warns)))
        return 1 if errs else 0
    if a.cmd == "table":
        print(table(tickets))
        return 0
    if a.cmd == "graph":
        errs, _ = validate(tickets)
        if errs:
            print("fix validation errors first", file=sys.stderr)
            return 1
        lv = levels(tickets)
        print(mermaid(tickets))
        print("\n# order:", " ".join(topo_order(tickets)))
        print("# critical path (%d):" % len(critical_path(tickets)), " -> ".join(critical_path(tickets)))
        for L in sorted(set(lv.values())):
            print("# level %d: %s" % (L, " ".join(sorted(k for k, v in lv.items() if v == L))))
        return 0
    if a.cmd == "create":
        errs, _ = validate(tickets)
        if errs:
            print("validation failed; run `backlog.py validate`", file=sys.stderr)
            return 1
        runner = GhRunner()
        native = {"parent": False, "blocked_by": False}
        if a.apply:
            found = existing_map(json.loads(runner.run(["gh", "issue", "list", "--state", "all", "--limit", "1000",
                                                        "--json", "number,body"] + (["--repo", a.repo] if a.repo else []))))
            if found:
                print("refusing to create: %d issue(s) already carry a local-id footer (e.g. %s). "
                      "Use `sync` to update bodies instead." % (len(found), ", ".join(sorted(found)[:3])), file=sys.stderr)
                return 1
            help_txt = runner.run(["gh", "issue", "create", "--help"])
            native = {"parent": "--parent" in help_txt, "blocked_by": "--blocked-by" in help_txt}
            print("gh native support:", native)
        mapping = create(tickets, runner, apply=a.apply, repo=a.repo, native_edges=native)
        pathlib.Path(ROOT / ".backlog-map.json").write_text(json.dumps(mapping, indent=1))
        print("mapping written to .backlog-map.json" if a.apply else "dry-run complete (no issues created)")
        return 0
    if a.cmd == "next":
        if a.json:
            issues = json.load(open(a.json))
        else:
            issues = json.loads(GhRunner().run(["gh", "issue", "list", "--state", "all", "--limit", "500",
                                                "--json", "number,title,labels,state,body"]))
        for phase, num, title in frontier(issues):
            print("#%d  %s  %s" % (num, phase, title))
        return 0


if __name__ == "__main__":
    sys.exit(main())
