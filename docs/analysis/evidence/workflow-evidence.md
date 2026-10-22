# Evidence: End-to-End Workflow Trace

Chain format: **trigger → component (file:line) → output/state → failure behavior → level**.
Backend traced: default `worker_backend:"workflow"`. Differences for Codex/legacy are noted.

## S0 Onboard (one-time)
trigger: `/super-board onboard` → `SKILL.md` routing → `references/onboard.md` (9 stages: silent detect, Checks, GitHub, Board, Branch, AGENTS.md, Policies, Bug sources, Review) → `scripts/super-board-setup.py` (deterministic half, 1019 lines) → writes `.claude/super-board/configs/<slug>.json`, `active`, `onboard-answers.json`; merges hooks via `super-board-settings.py`; refreshes managed AGENTS.md block via `super-board-agents-md.py`. Resumable (D: "8-step setup, resumes"). Worker self-check list at `onboard.md` L484-498. Level: D for the question flow (LLM-driven), V for the scripts' existence/roles.

## S1 Intake (outside the loop)
Humans create issues using `references/ticket-format.md` (Problem/Context/Fix/Acceptance Criteria/Risk/Blocked by). `super-collect` finds problems from Sentry/PostHog/PRs/architecture and files "verified" Backlog cards (`skills/super-collect/SKILL.md` "Verify — one fresh verifier per candidate", L123; `super-collect-file.sh`). `/super-board lint` flags vague ACs (D). **Backlog→Ready is a human action** (README: "Add cards to Ready"; run.md: "Backlog is not part of a run") — the principal trust gate (D).
Missing ACs: worker sanity check → Block template ❓ (run.md "Worker contract" step 2, D); planner/preflight `unclear` verdict (script flags no `## Acceptance Criteria` bullets, `super-board-preflight.sh`, V by header; judgement by LLM).

## S2 Preconditions + guards (orchestrator = interactive session, prose)
`run-workflow.md` "Preconditions" 1-7 and wave-loop step 1. Code-backed pieces: `verification-ready.py` (exit 9), `github-read.py --check` (halt file), `node --check` one-liner, atomic wave lock via `set -C` redirect, `super-board-usage.sh check`, `sb_gh_guard_check`. Prose-only: ordering, "replace stale lock only if neither backend active", pgrep legacy detection. Failure: exit 9/79 → halt, preserve state (D+V).

## S3 Planning
`scripts/super-board-wave-plan.sh` (V, read-only): selects in-flight cards in Review→QA order plus Ready cards whose `## Blocked by` closed (via `super-board-deps.sh`), excluding assigned cards; emits `cards, sweep, resume, refreshApproval, flag, stranded`; `max_workers` cap if >0; unreadable dependency line = not free (fail-safe). Refuses `variant != full` (exit 65).
Orchestrator then (prose) moves swept cards, resumes approved ones, returns stranded Building cards to Ready.

## S4 Skill readiness (before any claim)
`python3 .claude/bin/super-board-skills-ready.py --cards - --host claude --hydrate` → exit 10 if any required skill file missing (V, `skills-ready.py` REGISTRY L16-46; `requirements()` L~120). Issue-body `Skills:` line (outside code fences) overrides build chain (`override()` L62-86).

## S5 Claim
`gh issue edit --add-assignee <bot>` then re-read; proceed only if assignees == [bot] (`run-workflow.md` step 3, D). Not atomic: GitHub allows up to 10 assignees. Skipped if `bot_identity` unset (documented accepted risk). Release in Reconcile (step 5).

## S6 Launch
Host `Workflow` tool → `workflows/super-board-wave.js` with `{configPath, cards, tier}` (note: `humanApprovesMerge` documented but unread — V grep). `meta.phases` lists Pre-flight/Classify/Build/QA/Review.

## S7 Pre-flight (wave.js L214-285)
`Promise.all` over batches of 5 Ready build-lane cards → one `agent()` per batch (model sonnet; haiku on `--low`) with `PREFLIGHT_SCHEMA`; agent runs `super-board-preflight.sh` and judges. Verdicts proceed/hold/sequence/skipped/halted. Missing verdict ⇒ `skipped` (card stays Ready) — code-enforced (`preflightExit`, L~278). `sequence` with empty `blockedBy` ⇒ proceed (L270-276). hold/sequence: the *agent* posts Block template and moves card (prose).

## S8 Classify (wave.js L288-310)
Per Ready card `agent()` (haiku; sonnet on `--high`) with `CLASSIFY_SCHEMA` → `{kind, complexity}`; labels win over classifier; classifier may add `feature`/`bug` label to untyped card but never `qa`. Complexity indexes `LADDERS[tier]` (L176-182) → model. Cards past Ready inherit session model.

## S9 Build / QA / Review chain (wave.js L311-348)
`pipeline(cards, classify, chain)`; chain = build → qa → review, each only if previous `status === 'advanced'`; any other status ends that card's chain (next wave re-selects from board). `runLane` (L186-209): returns synthetic `halted` if `halted` flag set; else `agent(lanePrompt, {label, phase, schema:STAGE_SCHEMA, model})`; null result ⇒ `failed`; `halted` result sets global flag stopping all later lanes (V; test `tests/test-workflow-halt.sh` simulates this with stubs). Lane prompt = `SKILLS_CHECK` + `READ_FAILURE` + "follow run.md → <Lane> lifecycle EXACTLY" + BOARD_IO + writing standard (+ REVIEW_MEMORY for review). Everything the lane then does (worktree, branch, PR, comments, board move) is LLM behavior governed by prose (run.md L298-440) and hooks.
Isolation: per-lane git worktree `.claude/worktrees/issue-<N>-{build,qa,review}`; one branch/PR per issue `issue-<N>-<slug>`; hook `guard-worktree-path.py` blocks worktrees elsewhere (V, Claude Code only).
Same-file conflicts across cards: handled by pre-flight overlap judgement + `blocked-by` sequencing + merge-time rebase pass (D).

## S10 Verification and review
Builder: TDD per skill chain; Tester: test plan per AC, test-gap check, evidence + screenshots committed; Reviewer: gate-1 thread scan, own hypotheses first, prior-report memory (`<!-- super-review:report -->` marker), **test rerun**, optional adversarial truth-check (2 sub-agents, ≤50 gh calls each, confidence vs `truth_threshold`), class Over-engineering never blocks. All delegated to LLM + test commands (D). **Executable** verification only in merge gate: `verify_commands` run in scratch worktree of reviewed head merged with current base (V merge-gate L274-290).

## S11 Merge (merge-gate.sh)
L173-194 mkdir lock (+stale reap) → L211-226 read head/state; `--expect-head` mismatch ⇒ exit 6 → L228-262 merge-policy plan + approval check ⇒ exit 7/8 w/ `approval-request:` line → L266-275 scratch worktree at head, merge `origin/<base>` (conflict ⇒ exit 5) → L277-290 `eval` each verify command (fail ⇒ exit 2) → L295-320 migrations (`eval`) → L325-340 approval refresh → L349-351 `gh pr merge --squash --delete-branch --match-head-commit` → post-merge `cleanup-wt.py`. If merge call fails and head unchanged ⇒ `github-read.py --halt` (run halt). Reviewer then (prose) confirms MERGED + `git merge-base --is-ancestor`, closes issue, moves card to Done (run.md L442-510).

## S12 Reconcile / report (prose)
Release assignees; append manifest rows `docs/super-board/runs/<date>-<slug>.md`; `super-board-throttle.sh` lowers `max_workers` (3→2→1) after GitHub limit hit; wave report to user; halt gates (3 zero-progress waves; block-rate; user stop) — **prose-only in workflow backend** (V: no code reads `block_rate_alert_pct`/`rebuild_cap`; `run.sh:80-81` assigns but never uses them).

## S13 Stop / resume / recovery
Stop: `/workflows` stop or `super-board-stop.sh` (comments, release assignees, SIGTERM→SIGKILL, remove locks, keep worktrees). Resume = run again; state is the board (+ `github-halt.json`, wave lock). Crash recovery sweep: strip bot assignee from Review/QA/Ready/Building; stranded Building → Ready. Host `resumeFromRunId` returns cached lane results (D, host feature). Halt-file resume requires explicit `--resume` with re-read check (`github-read.py` main, L347-395).
