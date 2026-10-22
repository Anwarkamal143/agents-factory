# PR protocol

## Rules
1. **One ticket per PR, 1:1.** The PR body contains exactly one `Closes #<ticket>`. Never `Closes` the spec, map or another ticket. (A decision ticket is closed by its own docs PR.)
2. **Title:** `[T-<NN>] <ticket title>` (or the DEC/SPK/RET id).
3. **Branch:** `t-<nn>-<slug>`. **Commits:** `<type>: <summary>` with `Refs #<N>`; the last commit ends with `Closes #<N>`.
4. The body is filled from `.github/pull_request_template.md`. CI runs `check-pr` and fails when a section or linkage line is missing.
5. A PR never partially delivers a ticket. If you discover the ticket is too big, stop, split it (new issues with correct `blocked_by`), and PR only a slice that satisfies **every** criterion of a ticket.
6. Keep the body current. If scope changes, rewrite it.

## Template fields (what each must say)
- **Summary:** the smallest visual that shows the change (Mermaid state/flow/sequence, or a before/after table) plus 2-3 sentences. Use `Visual: none (<reason>)` only for pure docs or copy changes.
- **Traceability** (this is the "which PR closes which ticket" record):
  - `Closes #<ticket>`
  - `Part of #<spec issue>`
  - `Phase: <n>`
  - `Blocked by (merged): #a (PR #x), #b (PR #y)` or `none`
  - `Unblocks: #c, #d` or `none` (from the ticket's `blocks` footer)
  - `Decisions applied: DEC-xx, ADR-NNNN` or `none`
- **Evidence:** before/after behaviour with real output (command, exit code, event excerpt). No claims without a command that produced them.
- **Acceptance criteria:** the ticket's checkboxes copied, each **checked** with a pointer to evidence or a test name. Unchecked boxes mean the PR is not ready.
- **Merge danger:** `Door: one-way|two-way`, `Blast radius: <what breaks and for whom>`, rollback (revert, or why not), and for `risk:*` tickets the residual risks.
- **Review log:** the findings table from the review (final statuses) or `No findings`; "Findings not addressed" with reasons.
- **Assumptions and open questions:** each assumption (see `decisions-and-questions.md`), each follow-up issue created.
- **Checklist:** lint, types, tests, GLOSSARY updated, docs generated, ADR if needed.

## Repo settings the maintainer applies (agents cannot)
Confirm each and comment on T-01 when done:
- Default branch `main`; require a PR; **require status checks**: CI, `backlog-ci`, `pr-lint`; require branches up to date; require linear history; block force pushes and deletion.
- Require at least 1 human approval for PRs labelled `risk:security` or `risk:one-way-door` (CODEOWNERS or a branch ruleset).
- Auto-delete head branches after merge; enable sub-issues and issue dependencies if the plan allows.
- Issues: enable issue templates; Actions permissions: read and write for issues only (workflows declare minimal scopes).
- Dependabot or equivalent for dependency updates once dependencies exist; secret scanning enabled.
- Do **not** give agent sessions tokens with admin or secrets scope. Use a fine-grained token limited to this repo (contents, issues, pull requests).

## Closing the loop
Merging triggers `on-pr-merged` (see `ticket-runner.md` step 12). Verify afterwards that: the ticket is closed, its `status:*` labels are gone, dependents got an "Unblocked" comment, the spec issue has a ledger line. If any is missing, run `python tools/backlog/backlog.py on-merged --pr <n>`.
