# Session prompts (copy, paste, go)

Each prompt starts a **fresh session**. Replace `<N>` only if you want a specific ticket; otherwise the agent picks from the frontier. These prompts add nothing to the protocol; they point at it.

## 1. Implementer (one ticket)
```
You are implementing ONE ticket in this repository. Read AGENTS.md, then follow
docs/agents/ticket-runner.md step by step, from step 0 to step 9 (open the PR).
Pick: run `python tools/backlog/backlog.py next` and take the first entry (or issue #<N>).
Rules that override your instincts:
- If the readiness check (step 3) finds anything undecided or unclear, STOP and post the
  decision/question comment in the exact format in docs/agents/decisions-and-questions.md.
  Do not guess and do not implement a "reasonable default".
- Test first with /tdd, at the seams the ticket names. Never mock our own modules.
- Work in a git worktree on branch t-<NN>-<slug>. Commit everything. The last commit ends
  with `Closes #<ticket>`.
- Do NOT review your own work. After committing, stop and tell me the branch name so a
  fresh reviewer session can run docs/agents/review-protocol.md.
End your reply with: ticket id, branch, commits, acceptance criteria checked (with evidence), assumptions made.
```

## 2. Reviewer (fresh session, after the implementer committed)
```
You are the reviewer, a senior engineer. Do not write or change code. Check out branch
<branch> read-only and follow docs/agents/review-protocol.md exactly: run /code-review
against `git diff $(git merge-base origin/main HEAD)...HEAD`, then the senior supplement
and security checklist. Every finding needs a citation (CS-xx rule or an AC id); drop
findings you cannot confirm. Write the findings table to .scratch/review-t<NN>.md in the
format given, with the worst finding per axis. If you were launched as a sub-agent, do not
spawn further sub-agents. Report verdict APPROVE or CHANGES-REQUESTED.
```

## 3. Implementer, fix round (same session as 1, after the review)
```
Read .scratch/review-t<NN>.md. Triage per docs/agents/review-protocol.md section 5: verify
each citation; fix every blocker and major, minor if cheap, ignore nits; one commit per
finding `fix(review): F-<n> ...`; re-run all checks. This is round <k> of at most 2. Then
write the PR body from .github/pull_request_template.md (use /pr), run
`python tools/backlog/backlog.py check-pr --body-file .scratch/pr-body.md` until it prints
`PR body OK`, push, and open the PR as in ticket-runner.md step 9. Then update the issue
(status:in-review, comment with the PR link).
```

## 4. Decision resolver (human in the loop)
```
We are resolving decision ticket <DEC-xx / #N>. Use /grill-with-docs (or /grilling) to
interview me about the question, one question at a time, with your recommendation for each.
Read the ticket, docs/spec/SPEC.md and GLOSSARY.md first. When I have decided: post the
resolution comment in the format in docs/agents/decisions-and-questions.md, edit
docs/spec/SPEC.md so it states the decision (remove the [proposed] marker), update
GLOSSARY.md if terms changed, write an ADR if it clears the three-part bar
(docs/agents/domain.md), and open a docs PR that `Closes #<DEC>`. Do not change code.
```

## 5. Spike runner (AFK)
```
Run spike <SPK-xx / #N>. Follow its Method exactly in a throwaway repo with fake secrets
only. Commit the evidence document named in its Output section (tables, versions, exact
commands, verdicts). No product code. Open a PR that `Closes #<SPK>` following
docs/agents/pr-protocol.md (Review log may say "No findings" if the review finds none).
```

## 6. Retro
```
Run /retro for <RET-xx / #N> over the sessions that built the tickets in its Scope. Propose
changes to CODING_STANDARDS.md, GLOSSARY.md, docs/agents/* and ticket sizing; each rule must
be backed by an observed miss. Guidance changes only; open a PR that `Closes #<RET>`.
```

## 7. Maintainer: "what is the state of the project?"
```
Run `python tools/backlog/backlog.py next`, `gh issue list --label status:in-progress`,
`gh issue list --label status:needs-decision --label needs-info`, and read the ledger
comments on the spec issue. Summarize: what merged, what is in flight, what is waiting on me
(decisions and questions, each with the recommendation), and what can start now.
```
