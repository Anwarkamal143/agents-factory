# 13 — Installation and Developer Experience

**Every command below is a PROPOSED INTERFACE EXAMPLE for the new factory. None exists yet.** For contrast, the existing super-board flow is `curl … get.sh | bash` or `/plugin install`, then `/super-board onboard` (V: `get.sh`, `install.sh`, `references/onboard.md`).

## 1. Adoption lifecycle (18 steps)

| # | Step | Proposed interface | What happens | Safety property |
|---|---|---|---|---|
| 1 | Install | `pipx install software-factory` (or download release + `factory verify-install checksums.txt`) | Installs CLI only; touches no repository | Signed release + checksum (vs S-08) |
| 2 | Inspect repo | `factory init --dry-run` | Read-only scan: language, package manager, framework, test/lint/build commands, CI config, base branch, existing agent files | Writes nothing |
| 3 | Detect conventions | (part of 2) | Reads `package.json`/`pyproject.toml`/`Makefile`/CI yaml/`CONTRIBUTING`; proposes `verify` argv lists with confidence notes | Shows evidence for each guess |
| 4 | Configure | `factory init` | Creates `.factory/project.yaml` from template; asks only for what detection could not decide; rejects trivial verify commands | Atomic write; `.gitignore` entry for `state/` |
| 5 | Select harness | `factory adapter list` / `factory adapter use claude-code` | Lists installed adapters + probed capabilities | Capability probe is read-only |
| 6 | Validate prerequisites | `factory doctor` | Checks binaries, versions, auth presence (not values), permissions, clean tree, verify commands run green on base | Reports degradations (e.g. "no OS sandbox ⇒ max autonomy L1") |
| 7 | Read-only diagnostic run | `factory run --level L0 "Describe how to add X"` | Produces a spec + plan draft, executes nothing | No side effects |
| 8 | Submit request | `factory request "Add rate limiting to the API"` (or `--from-issue 123`) | Creates a run; spec stage starts | Issue text marked untrusted |
| 9 | Review spec | `factory spec show R-…` → `factory approve spec R-…` | Spec with numbered acceptance criteria; edit file or `factory reject --note` | Approval pinned to spec hash |
| 10 | Approve plan | `factory plan show R-…` (DAG, write sets, risk classes) → `factory approve plan R-…` | Overlapping write sets are flagged before approval | Pinned to plan hash |
| 11 | Execute | `factory run R-…` (foreground) or `factory run R-… --detach` | Scheduler runs tasks in worktrees | Budgets enforced by engine |
| 12 | Inspect progress | `factory status R-…`, `factory logs T-… --follow`, `factory artifacts T-…` | Task table, last events, artifact paths | Read-only |
| 13 | Review verification | `factory verify show T-…` | Engine-run commands, exit codes, logs, base/head hashes | Evidence distinguishes engine-run vs agent-reported |
| 14 | Approve integration/delivery | `factory approve delivery R-…` | Diff summary, risk classes, verification, findings; merge/PR performed by engine | Approval pinned to head hash; expires |
| 15 | Resume/recover | `factory resume R-…` | Replays log, reconciles leases, continues; blocked tasks listed with reason | Idempotent |
| 16 | Upgrade | `factory upgrade --plan` then `factory upgrade` | Shows diff of managed files and migrations; applies; keeps `project.yaml`/`overrides/` | Backup + `factory rollback` |
| 17 | Add/replace components | `factory component add ./my-skill` / `factory component swap builder ./my-builder` | Validates manifest, deps, capabilities; updates lock | Contract-parity test before swap |
| 18 | Uninstall/disable | `factory component disable <id>` / `factory uninstall --keep-state` | Removes only files in `factory.lock`; leaves project files | Lists what it will delete first |

## 2. Per-repository configuration and inheritance
Precedence (low → high): factory defaults → policy pack (`policies/`) → organization file (`~/.config/factory/org.yaml`, optional) → `.factory/project.yaml` → CLI flags for one run. Schema-validated at load; `factory config explain <key>` prints the effective value and its source layer. Example:
```yaml
# .factory/project.yaml   (PROJECT-OWNED; proposed)
schema: factory.project/1
base_branch: main
verify:
  - {name: unit, argv: ["pytest","-q"]}
  - {name: lint, argv: ["ruff","check","."]}
adapter: claude-code
autonomy: L2
policy: {risk_classes: {schema: approve, auth: approve, size: {lines_over: 400, action: approve}}}
budgets: {task_attempts: 3, run_tokens: 2000000}
```

## 3. Project-owned vs factory-managed files
| Path | Owner | Editable | Notes |
|---|---|---|---|
| `.factory/project.yaml`, `.factory/overrides/` | project | yes | survive upgrades |
| `.factory/managed/`, `.factory/factory.lock` | factory | no (drift reported by `doctor`) | hashes of every managed file |
| `.factory/state/` | generated | no | gitignored; safe to delete only when no run is active |
| managed block in `AGENTS.md`/`CLAUDE.md` | factory (between markers) | outside markers only | marker-delimited, like super-board's AGENTS.md block (V: `agents-md.py`) but tracked in the lock |

## 4. Discovery, diagnosis, history
- **Discover components:** `factory component list [--kind skill] [--capability shell]`, `factory component show <id>` (manifest, requirements, permissions, dependents).
- **Diagnose a failed run:** `factory explain R-…` walks the event log backwards from the failure: failing transition, cause, verification log excerpt, budget state, whether a policy denied an action; suggests next command (`resume`, `approve`, `edit spec`). `factory doctor --run R-…` re-checks prerequisites that changed.
- **Execution history:** `factory runs`, `factory events R-… [--type task.transitioned]`, `factory export R-… > run.tar` (log + artifacts + redacted config) for sharing a bug report.
- **Disable a malfunctioning component:** `factory component disable <id>` marks it disabled in the lock (workflow validation then fails fast if a stage requires it, or falls back to a declared alternate); `factory component enable`.
- **Upgrade without losing config:** managed/owned split + `factory upgrade --plan` showing file diffs and schema migrations; refuses if a run is active.
- **Safety nets learned from super-board:** installer refuses destructive replacement without a lock manifest; the installer test suite includes "upgrade must not delete unrelated files" (super-board's 2026-08-20 incident, S-11).

## 5. Operating guidance
| Situation | Do |
|---|---|
| First week | stay at L1/L2, read every approval prompt, run `factory doctor` after any toolchain change |
| Flaky verification | mark the check `retries: 1` with a recorded reason; never weaken to exit-code-only |
| Secret-bearing env | list needed variable *names* under a task profile; engine passes only those |
| CI | `factory run --non-interactive --level L2 --approvals-file approvals.yaml` (approvals must be pre-signed by a human channel; unsigned ⇒ run stops `awaiting_approval`) |
| Cost control | `budgets` in project.yaml + `factory status --usage` |

## 6. Developer experience gaps in super-board that this design addresses
Onboarding is an LLM-driven question flow (9 stages) rather than a deterministic detector with a dry-run (V `onboard.md`); config has no explain/validate command (R-07); no uninstall (06 A3); status is a board render, not an event-log explainer (V `status.py`); upgrade is overwrite (S-11).
