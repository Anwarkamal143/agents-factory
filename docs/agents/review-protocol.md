# Review protocol: the senior-engineer pass

Review runs in a **fresh session** that did not write the code, on **committed** work only. It produces findings; it does not edit code.

## 1. Setup
```
git fetch origin
BASE=$(git merge-base origin/main HEAD)
git diff --stat $BASE...HEAD          # confirm the diff is what you expect and everything is committed
git status --short                    # must be empty; if not, stop and tell the author to commit
```
Read: the ticket, `docs/spec/SPEC.md` sections it cites, `CODING_STANDARDS.md`, `GLOSSARY.md`. Do **not** read the author's reasoning or PR draft before forming your own view.

## 2. Run `/code-review` (two axes, separate)
`/code-review` runs two sub-agents and reports them separately: **Standards** (does the diff follow `CODING_STANDARDS.md` and good engineering practice) and **Spec** (does it do what the ticket and spec ask; it finds the ticket via `Closes #N` in commit messages). Keep the axes separate. Every finding must carry a **citation**: a standards rule id (`CS-xx`), a named smell with the hunk, or an acceptance criterion. Treat each finding as a **hypothesis**: open the cited rule or hunk and confirm it before it is accepted. A finding you cannot confirm is dropped.

## 3. Senior supplement (you, not the skill)
Add findings only where the checklist below is violated and cite the rule or criterion.
- **Correctness vs ticket:** each acceptance criterion has a test that failed first; negative and boundary cases exist; the demo path works as written.
- **Tests:** at seams only; no mocks of own modules; literal expectations; no tautologies; no sleeps; fault paths covered (CS-20..27).
- **Invariants:** state-machine rows match SPEC-01 exactly; `succeeded` rule intact; transitions idempotent.
- **Durability:** crash between any two writes recoverable; fsync/atomic rename where specified; no authoritative derived state.
- **Security checklist** (always for tickets labelled `risk:security`, and any change touching policy, approvals, adapters, git, files, processes or config): default-deny preserved; no shell strings; env scrubbed and secrets by name; untrusted inputs bounded and validated; symlinks not followed; no path built from agent output without normalization; approvals only from the human channel; config pinned at run start; no new network access.
- **Contracts:** schemas versioned, fixtures good/bad, docs generated not hand-edited.
- **Scope:** nothing beyond the ticket; out-of-scope items filed as issues; no speculative generality (CS-42); new dependency justified (CS-43).
- **Naming and docs:** GLOSSARY nouns used; GLOSSARY/ADR updated where required; public docstrings state contracts.
- **Observability:** the events needed to explain a failure are emitted.
- **Door:** one-way changes (on-disk formats, public CLI, lock formats) flagged and justified.

## 4. Output format (`.scratch/review-t<NN>.md`)
```
# Review of t-<NN> at <short sha>  (round <k>)
Verdict: APPROVE | CHANGES-REQUESTED
Worst finding per axis: standards=<id|none> spec=<id|none> security=<id|none>

| id | axis | severity | location | finding | citation | status |
|----|------|----------|----------|---------|----------|--------|
| F-1 | spec | blocker | <module/test> | AC-3 has no failing-first test | AC-3, CS-24 | open |
```
Severity: **blocker** (wrong behaviour, security hole, missing AC, data loss, breaks invariant), **major** (likely bug, missing fault-path test, contract drift), **minor** (maintainability), **nit** (taste). Do not combine axes into one score.

## 5. Triage (author session)
- Verify the citation exists. A finding with no valid citation is rejected with a one-line reason.
- Fix all `blocker` and `major`. Fix `minor` if cheap. Ignore `nit`.
- If you disagree, say why in the findings file (status `wontfix: <reason>`); a disagreement on a `blocker` is escalated to the maintainer, not decided by the author.
- One commit per finding: `fix(review): F-<n> <summary>`.

## 6. Rounds
**Maximum two rounds.** Round 2 is a **targeted re-review of changed hunks** plus the previous findings and their status. Do not loop until the review is "clean"; AI reviewers produce fresh nits every pass. After round 2, remaining items go in the PR's "Findings not addressed" with reasons, or become follow-up issues.

## 7. Guards
- If you are a sub-agent of a review, do not spawn more sub-agents or re-run `/code-review` (see `AGENTS.md`).
- The review session never edits code, never pushes, never opens PRs.
- Review of a decision, spike or retro PR checks the evidence and the SPEC edit instead of tests.
