# 08 — Security, Reliability and Risk Review

**Scope and limits.** Static review of the inspected files. Nothing was executed; no exploit was attempted. "Bypass" statements are *inferences from code structure* (level **I**) unless marked **V**. Severity = impact × plausibility for an unattended autonomous run on a developer's machine with real GitHub/DB credentials: **Critical / High / Medium / Low**. Finding IDs (S-, R-) are referenced by later reports.

## 10.1 Security findings

| ID | Finding | Evidence | Level | Sev | Mitigation (existing → proposed) |
|---|---|---|---|---|---|
| S-01 | **Merge gate is a convention, not a boundary.** The only `gh pr merge` in code is `merge-gate.sh:349`, but no hook intercepts a bare `gh pr merge`, and `run-workflow.md` (≈L368/381) and `onboard.md` (≈L316) recommend allow-listing `Bash(gh pr merge:*)` for unattended runs. An agent that decides to merge directly skips policy, approval and verify-on-base. | grep of scripts/hooks/workflows; settings snippet | V (facts) / I (bypass) | **High** | Existing: prompt rule "never merge outside the gate". Proposed: engine owns merge (agents have no merge permission); GitHub branch protection / merge queue as server-side backstop |
| S-02 | **Approval ≠ distinct human.** `approval.py` L77-131 requires a `User` with write+ permission, a later unedited `done` comment, matching head+scope, but not approver ≠ requester/bot. Solo onboarding sets `bot_identity` to the user's own login (`onboard.md` ≈L222-224); `second-account.md` has the agent `gh auth switch -u owner`. An agent running under that identity could post the approval. | files cited | V (code) / I (exploitability) | **High** (solo mode) | Existing: anti-staleness only. Proposed: approvals recorded by the engine from an authenticated human channel (CLI prompt/OIDC identity), never via an agent-writable comment, or require a different principal |
| S-03 | **Guardrail hooks are fail-open heuristics, Claude-only.** All five `guard-*.py` allow on exception; `guard-secrets.py` matches regexes against command text (Bash/Read/Grep; no Glob matcher); `guard-delete-outside.py` intentionally allows unknown `$(…)` variables; `guard-protected-push.py` has `SB_ALLOW_PROTECTED_PUSH=1` bypass and is opt-in. No Codex hook configuration found. Whether hooks run for Workflow `agent()` sub-agents is unknown. | `hooks/*.py`, `settings-snippet.json` | V (design) / U (sub-agent coverage) | **High** on Codex, **Medium** on Claude | Proposed: OS-level sandbox/container + engine permission checks; hooks only as defense in depth, fail-closed for destructive classes |
| S-04 | **Codex lane runs with `approval_policy="never"` and network enabled**, filesystem write on repo root + git dirs. | `codex-lane.sh` ≈L140-160 | V | **Medium** | Proposed: network off by default per permission profile; allow-listed hosts |
| S-05 | **Legacy dispatcher bypasses permissions**: `claude -p --dangerously-skip-permissions`. | `skills/super-build/scripts/super-build-dispatch.sh:143` | V | **Medium** (legacy path) | Remove or gate behind explicit `--unsafe` |
| S-06 | **Config-supplied shell executed via `eval` on PR code.** `verify_commands` and migration commands run through `eval "$cmd"` in a scratch worktree of the *PR head*, with the developer's environment (and DB URL for migrations). Anything the branch's test setup runs (package scripts, test files) runs with those credentials. `verification-ready.py` only requires non-blank strings. | `merge-gate.sh:283,307`; `verification-ready.py` | V | **High** (for untrusted PRs) / **Medium** (agent-authored PRs from trusted ticket) | Proposed: run verification in an isolated container with scrubbed env and no prod creds; separate DB credentials for migrations |
| S-07 | **No prompt-injection posture.** Lanes read issue bodies, all comments, PR threads; `super-collect` pulls Sentry/PostHog/PR text into tickets. No instruction to treat such content as untrusted data was found in `skills/ scripts/ hooks/ CLAUDE.md` (only `calibration.py:172` for its own evidence). Human Backlog→Ready promotion is the practical gate (D). | grep (negative, limited to those paths) | V (absence) | **High** | Proposed: untrusted-content boundary markers, capability-reduced agents for ingesting external text, human gate at spec approval |
| S-08 | **Supply chain.** `get.sh` fetches the latest release tarball over HTTPS and runs `install.sh` (`curl … \| bash`); no checksum/signature (grep of `get.sh`, `install.sh`, `publish-release.sh`). Required skills (`mattpocock-skills:*`, `ponytail:*`) are third-party, unpinned, existence-checked only; README admits it "certifies availability, not content". | files cited | V | **Medium** | Proposed: signed releases + checksum file, lock file with hashes, pinned skill versions |
| S-09 | **Issue-body `Skills:` override** lets whoever edits an issue choose the Builder's skill chain, constrained by name regex, an `INTERACTIVE` denylist and must resolve to an installed `SKILL.md`. | `skills-ready.py` L62-86 | V | **Low** | Keep validation; restrict who may set it |
| S-10 | **Secrets handling is ambient.** No secret store; `gh` auth and env tokens inherited; protection relies on `guard-secrets`/`guard-key-literals` heuristics. | hooks | V/I | **Medium** | Proposed: scrubbed env per task; secrets by reference only |
| S-11 | **Installer overwrites whole skill dirs** (`rm -rf dest/*; cp -R`, `install.sh` ≈L135) with no manifest; an incident on 2026-08-20 deleted 190 entries, after which guards were added (author comment). Local edits to installed skills are lost on upgrade. | `install.sh` | V | **Medium** (integrity) | Proposed: hash-manifest install, 3-way merge/report |
| S-12 | **Stale-lock reaping race** in `merge-gate.sh` (two reapers can both `rm -rf` and retry). | `merge-gate.sh` L173-194 | V | **Low** | Lease file with owner PID + heartbeat |
| S-13 | **Distribution of an executable hook set into user repos** with `chmod +x` and merged into `.claude/settings.json` — trust rests entirely on the release channel (see S-08). | `install.sh` L163-200 | V | **Low–Medium** | as S-08 |

Strengths (V): secret-pattern scan of the archive found none; destructive cleanup defaults to dry-run with recovery TSV and never deletes unmerged branches (`cleanup-wt.py`); merge uses `--match-head-commit`.

## 10.2 Reliability findings

| ID | Finding | Evidence | Level | Sev | Proposed fix |
|---|---|---|---|---|---|
| R-01 | **Loop bounds are prose.** `rebuild_cap`, `block_rate_alert_pct`, `root-cause-hash` and "3 consecutive zero-progress waves" are not enforced in inspected code: `super-board-run.sh:80-81` assigns the first two and never uses them; nothing parses `root-cause-hash`; `wave.js` has no retry/round counters (contrast `ui-refine-loop.js`, which caps rounds and fix failures in code). A bounce loop is bounded only if the orchestrating LLM obeys `run-workflow.md` step 7. | grep + file reads | V | **High** | Engine-enforced per-task retry and per-run budgets |
| R-02 | **Merge refusal halts the run** instead of parking the card: `merge-gate.sh` has one `exit 3` ("PR closed"); a failed `gh pr merge` with unchanged head calls `github-read.py --halt` (exit 79) while `run.md` says exit 3 = GitHub refused → Blocked. | `merge-gate.sh` ≈L220, L349+ | V | **Medium** | Classify merge refusal (protection/required checks) as task-level `blocked` |
| R-03 | **Claim is not atomic and docs contradict.** `run.md` describes atomic compare-and-set (422); `run-workflow.md` step 3 says adding an assignee never fails (up to 10) so it verifies after add. Two orchestrators can both add and both back off. | both docs | V | **Medium** | Local lease + remote advisory marker |
| R-04 | **No lane timeout/cancel in the wave workflow code**; failure = null ⇒ `failed`; next wave retries. | `wave.js` `runLane` | V (negative) | **Medium** | Per-task wall budget + cancel in adapter contract |
| R-05 | **State is split, untransactional, unversioned** (GitHub, `.claude/super-board/*`, run manifests, comments). No schema version found for config/run state. | state inventory | V | **Medium** | Single local state store with schema versions |
| R-06 | **GitHub API budget as bottleneck.** Release notes document an incident (≈950 GraphQL pts/card; ≈2,850/3-card wave) and mitigations (cached `card.sh`, `throttle.sh`, `github-read.py` halt). | RELEASE-NOTES; scripts | D/V | **Medium** (mitigated) | Local state removes most reads |
| R-07 | **Config unvalidated.** `config-schema.json` is a reference doc "not parsed at runtime"; docs say configs "validate against" it; each script reads its own keys with defaults (jq/python). `["true"]` would pass `verification-ready.py`. | files cited | V / I | **Medium** | JSON-Schema validation at load; verification quality lint |
| R-08 | **Doc/code drift** (found 6): `humanApprovesMerge` unread; exit 3; rebuild cap; config validation; atomic claim; README "6 guard hooks" vs 5 files. | see 04 | V | **Medium** | Generate docs from manifests/schemas; contract tests |
| R-09 | **Duplicated logic in 3 backends** (wave.js, codex scripts, legacy run.sh); ladders and lane schema copied. | 03 | V | **Medium** | One engine, adapters |
| R-10 | **Disk/worktree hygiene**: handled by `cleanup-wt.py` (good) but triggered by merge or SessionStart only. | hook | V | **Low** | Engine-owned GC |
| R-11 | **Hard-coded persona/model constants** ("Eric" ×26; model names). | grep | V | **Low** | Policy/config |

## 10.3 Approval and autonomy
Action classes found in the factory and what actually gates them:

| Action | Gate | Gate strength |
|---|---|---|
| Move Backlog→Ready | Human (documented) | process only |
| Create issues/PRs/comments | none beyond prompt | none |
| Edit code in worktree | worktree-path hook (Claude) | weak |
| Delete files | `guard-delete-outside` | weak (fail-open) |
| Read secrets | `guard-secrets` | weak |
| `git push` to protected branch | opt-in hook | weak, opt-in |
| Merge | `merge-gate.sh` + policy + approval | **strong if used** (S-01) |
| DB migrations | gate runs from scratch tree; "needs-you" for live DB | medium |
| Install/upgrade | none | n/a |
| Network access | Codex lane enabled; Claude default | none |
Autonomy model: effectively two levels — fully autonomous lanes, human-gated merge for four policy categories. No graded autonomy levels, no per-run permission profile, no revocation of approvals other than head change. Dangerous-action list is implicit.

## 10.4 Testing and observability
Strengths (V): 59 offline suites incl. merge gate, approval, hooks, wave planner, GitHub read shape validation, writing-format contract, workflow halt via stub harness; cross-platform CI (D); 7 paid evals for prompt behavior (not run; no result artifacts in archive). Gaps: no test against a real harness/Workflow runtime (U); no fault-injection of GitHub failures beyond unit stubs; no test of hook coverage under sub-agents; no mutation/contract tests for docs-vs-code parity (the drift in R-08 would be caught by them). Observability: PR comments, run manifest, `status.py` board render; **no structured event log, trace IDs, cost/token accounting or replay** found in the state paths inventoried. Debuggability after a crash depends on reading comments and worktrees.

## Top risks (ranked)
1. S-01/S-02 merge and approval controls rely on agent cooperation.
2. R-01 unbounded retry/bounce loops in autonomous runs.
3. S-06 PR-controlled code executed with ambient credentials.
4. S-07 untrusted text flowing into privileged agents.
5. S-03 fail-open, Claude-only guardrails.
