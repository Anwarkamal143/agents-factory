# agents-factory: instructions for coding agents

A vendor-neutral engine that turns a written request into reviewed, verified, integrated changes, with an append-only event log and engine-owned verification, approvals and merges. Status: pre-MVP. The build plan is a ticket graph; read `docs/backlog/README.md` first.

## Agent skills

### Issue tracker
Work is tracked as GitHub issues. Create, read, claim, comment on, label and close them with `gh`. Conventions, label state machine and dependency footers: `docs/agents/issue-tracker.md`.

### Triage labels
Canonical triage vocabulary and our extra status, mode, phase, size and risk labels: `docs/agents/triage-labels.md`.

### Domain docs
Single context. Glossary: `GLOSSARY.md`. Decisions: `docs/adr/`. Rules for when to update them: `docs/agents/domain.md`.

## How to work here (read this whole section)
1. **One ticket per fresh session.** Follow `docs/agents/ticket-runner.md` exactly: pick, readiness check, implement, review, fix, PR, update issues.
2. **Never pick** an issue labelled `type:spec`, `type:decision`, `wayfinder:map` or `type:retro`. Never mark those `ready-for-agent`.
3. **Never decide a design question yourself.** If the ticket, `docs/spec/SPEC.md`, `GLOSSARY.md` and the ADRs do not settle something that affects a contract, state machine, schema, policy matrix, file format, dependency or security posture, stop and escalate using `docs/agents/decisions-and-questions.md`.
4. **Test first, at the seams.** Use `/tdd`. Tests live only at the seams named in the spec and the ticket. Never mock our own modules. Expected values are literals.
5. **Commit before review.** The reviewer sees only committed work (`git diff <merge-base>...HEAD`). The last commit message of a ticket ends with `Closes #<ticket>`; earlier ones use `Refs #<ticket>`.
6. **Review in a fresh session**, never the one that wrote the code: `docs/agents/review-protocol.md`.
7. **Open the PR from the template** and make it say exactly which ticket it closes, which spec it belongs to, what blocked it and what it unblocks: `docs/agents/pr-protocol.md`. CI runs `check-pr`; an incomplete PR body fails.
8. **Stay in scope.** Out-of-scope discoveries become new issues labelled `needs-triage`; do not fix them in this PR.
9. Use the nouns in `GLOSSARY.md`. Follow the rules in `CODING_STANDARDS.md` (findings cite rule ids).
10. Parallel work uses git worktrees, never two sessions in one checkout: `docs/agents/parallel-work.md`.
11. Running out of context mid-ticket: run `/handoff`, leave the branch name and state in an issue comment, keep `status:in-progress`.

Copy-paste prompts for each session type: `docs/agents/session-prompts.md`.

## Review sub-agent guard
If you were launched as a review sub-agent (for example one axis of `/code-review`), **do not launch further sub-agents or run `/code-review` again**. Do your one axis, return findings, stop.

## Skill name clash
Some harnesses ship a built-in `/code-review`. Before relying on it, confirm the output has the two-axis shape described in `docs/agents/review-protocol.md` (Standards and Spec, reported separately). If not, follow that protocol by hand.

## Commands
Lint, type-check and test commands are recorded in `CODING_STANDARDS.md` ("Commands") once DEC-01 is resolved and T-01 lands. Until then the only runnable checks are `python tools/backlog/backlog.py validate` and `python -m unittest discover -s tools/backlog/tests`.
