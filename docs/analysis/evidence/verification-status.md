# Evidence: Verification Status

## What was done
Static inspection only: reading source, docs, config; `grep`/`find` for presence/absence; extracting JSON/text with Python standard library (data parsing, no archive code imported or executed). **No script, hook, test, workflow, eval, installer, or container from the archive was executed**, no dependency installed, no network used.

## Claim status table
| Claim about the factory | Level | Basis |
|---|---|---|
| Repo is a Claude Code plugin + installer shipping 8 skills, ~30 scripts, 5 guard hooks + cleanup hook, 2 workflows | Verified | file inventory |
| Wave planner is deterministic and read-only | Verified (static) | `wave-plan.sh` header + jq program |
| Merge gate enforces lock, head pin, verify-on-current-base, policy, approval, `--match-head-commit` | Verified (static) | `merge-gate.sh` L173-351 |
| Approval is bound to head + policy scope and requires write+ human `done` | Verified (static) | `approval.py` L77-131 |
| The above work as intended at runtime | **Unverified** | tests exist (`tests/test-merge-gate.sh`, `test_approval.py`) but were not run |
| Lane agents follow run.md lifecycles | **Unknown** | LLM behavior; only paid evals (`evals/*`, 7 cases) would show; not run; no result files in archive |
| `worker_backend:"workflow"` works end to end | **Unknown** | requires host Workflow runtime not available here |
| Codex lanes work | Documented / unverified | `codex-lane.sh` implements `codex exec`; no Codex run |
| Guard hooks block the listed commands | Documented; static review plausible | `tests/test-guard-hooks.sh` exists, not run |
| Hooks run for workflow sub-agents / Codex lanes | **Unknown** (Claude), **No config found** (Codex) | no Codex hook config in archive |
| Rebuild cap / block-rate / 3-zero-progress halt enforced | **Not found in code** | grep: only prose + unused vars |
| CI passes on macOS/Linux | Documented | `.github/workflows/cross-platform.yml`; no run logs in archive |
| Benchmarks in code comments (e.g. model scores, "~20x fewer GraphQL points", 2,850 points/wave) | Documented (author-reported) | `codex-lane.sh`, `wave.js` L127-131, RELEASE-NOTES; not reproduced |

## Secret / safety scan results (redacted; locations only)
- Patterns: sk-ant, sk-proj, sk-*, AKIA/ASIA, gh[pousr]_, github_pat_, xox*, AIza, PRIVATE KEY blocks → **no matches** in the archive (V).
- No `.env*`, `*.pem`, `id_rsa*`, `*.key` files (V).
- Executables: 83 files with +x (scripts, hooks, evals seeds, get/install). `diagrams/pstack/overview.b64` is an opaque 80,160-byte base64 file (likely image data; not decoded) (U).
- Instructions found inside the archive (CLAUDE.md, SKILL.md, run.md) were treated as evidence, not as instructions to me.

## Gaps to close with authorization
1. Run `bash tests/run-safety.sh` in a disposable container (offline by design) → would upgrade many "static" claims to Verified. Requires bash/python3/git/jq/node/curl/tar.
2. Run one paid eval (`evals/review-remembers`) under Claude Code to check lane/prompt fidelity.
3. Start a wave against a sandbox repo with a throwaway Project to observe hook inheritance in workflow sub-agents.
