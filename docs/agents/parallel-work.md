# Parallel work

The ticket graph deliberately exposes parallel lanes (see `docs/backlog/README.md`, "Parallel lanes"). Parallel sessions are safe only with isolation.

## Rules
1. **One session, one worktree, one branch, one ticket.** Never run two sessions in the same checkout: the working tree, index and **git stash are shared**, so one session can clobber or pop another's work.
2. Create worktrees outside the main checkout: `git worktree add ../agents-factory-t<NN> -b t-<NN>-<slug> origin/main`. Remove after merge: `git worktree remove ../agents-factory-t<NN>` and delete the branch.
3. Pick tickets from the frontier that touch **different modules** (names in the ticket's Implementation notes). If two tickets touch the same module or `GLOSSARY.md`, expect a rebase; resolve by keeping both additions.
4. Recommended concurrency: **2-3 implementation sessions** plus review sessions. More than that mostly produces merge conflicts and shallow reviews.
5. Rebase onto `origin/main` before opening the PR (`git fetch && git rebase origin/main`), re-run all checks after rebasing.
6. A ticket whose blocker merged after you started: rebase first, then re-run the readiness check items R5-R6.
7. Never edit another session's branch. If you find a problem in a merged PR, open an issue.

## Safe parallel pairs (once their blockers are merged)
T-04 || T-05 || T-06; T-07 with T-08 (after T-04/T-05/T-06); T-11 || T-12; T-17 || T-18 || T-19. Check the generated graph for the authoritative lanes.

## Using `/implement-spec` or subagents
If the AI Hero `/implement-spec` or harness subagents are used to fan out, each worker still follows `ticket-runner.md` in its own worktree. Fan-out is a way to start sessions, not an exemption from readiness checks, review in a fresh session, or one-ticket-per-PR.
