# 06 — Component Lifecycle and Extensibility

Part A = what the existing factory requires today (V from `install.sh`, `readme-sync.py`, `skills-ready.py`, `pages.yml`). Part B = proposed design (recommendation, not observed).

## Part A — Existing factory

### A1. Adding a skill (observed procedure)
| Step | Why | Where | Enforced by |
|---|---|---|---|
| Create `skills/<name>/SKILL.md` with `name`, `description` | host discovery | skills tree | host |
| Add to `PRIMARY_SKILLS` or `SECONDARY_SKILLS` | otherwise not installed | `install.sh` L43-44 (hard-coded list; loop L95) | nothing — silent omission (I: no test seen asserting parity) |
| Add entry to `skills/families.json` (one brief ≤15 words) | README tables | `readme-sync.py` L76-78 | **Yes**: dies on mismatch both ways |
| Regenerate README tables | doc parity | `hooks/pre-commit-readme.sh`, `.claude/settings.json` PostToolUse | yes (dev repo) |
| If lane skill: add label→chain in `REGISTRY` | `skills-ready.py` precondition | code edit | code |
| If it needs scripts: add names to the loop at `install.sh` L148 | installed to `.claude/bin` | hard-coded | none |
| Dependencies on other skills | declared only inside `REGISTRY`/prose | — | existence check only |
| Docs site | `diagrams/skill-map.json`, `pages.yml` | manual | none |
| Tests/evals | `tests/…`, `evals/…`; dev Stop hook requires evals after skill edits | `hooks/dev/gate-skill-evals.py` | yes (dev repo, Claude-only) |
Result: **5–7 touch points, 2 enforced.**

### A2. Modifying a component
- Lane behavior lives in `run.md` prose *and* in `wave.js` prompts *and* in `codex-lane.sh` prompt; a change is a multi-file edit with no single source (V duplication, 03).
- Script contract changes (exit codes) are documented in headers and `run.md`; docs drift was found (merge-gate exit 3, 04/08).
- Compatibility: `VERSION` files per skill plus `upgrade.json`-style notes in RELEASE-NOTES; no semver contract for config. `variant` removal shows an upgrade guard pattern (wave.js/wave-plan.sh refuse with message) — a good precedent.
- Rollback: copy-install overwrites; rollback = reinstall an older release (get.sh supports tag?, U).

### A3. Removing a component
No uninstall command found. `install.sh` `rm -rf` of skill destination dirs on upgrade means removed skills would persist in targets unless manually deleted (I; I did not find removal logic). References are string paths in prompts, so dangling references surface at agent runtime.

### A4. Replacing a component
Replaceable seams that already exist: skill chain per label (REGISTRY + issue `Skills:` override), `worker_backend` (workflow / claude-p; Codex via flag), `verify_commands`, merge policy, hooks (settings snippet). Not replaceable without edits: lane lifecycle, board backend (GitHub hard-wired), model ladders (constants).

### A5. Registry / manifest reality
There is **no manifest** for skills, scripts, hooks or workflows. Inventories exist only as: `install.sh` string lists, `skills/families.json` (README only), `diagrams/skill-map.json` (docs), `REGISTRY` (skill chains). No compatibility metadata, no declared permissions, no per-component version beyond `skills/super-board/VERSION` and plugin version.

## Part B — Proposed lifecycle design (recommendation)

### B1. Component manifest (`component.yaml`, JSON-Schema validated)
```yaml
id: super-review            # unique, lowercase-kebab
kind: skill                 # skill | agent | workflow | hook | tool | adapter | integration
version: 1.3.0              # semver of this component
contract: factory.skill/1   # major contract it implements
entry: SKILL.md
requires:
  capabilities: [fs.read, fs.write, shell, subagent?]     # '?' = optional → graceful degradation
  components: [{id: verify-runner, range: ">=1,<2"}]
  tools: [{name: git, range: ">=2.30"}]
permissions: {fs: [worktree], network: false, secrets: []}
triggers: {stages: [review], labels: [bug]}
inputs: [task-input]
outputs: [task-result, verification-result]
supports: {harnesses: [claude-code, codex, generic-cli], os: [linux, macos]}
tests: [tests/unit, tests/contract]
deprecates: []
```

### B2. Add / modify / remove / replace procedures
| Operation | Procedure | Automatic checks |
|---|---|---|
| Add skill | `factory component new skill <id>` scaffold → edit → `factory component validate` → `factory test <id>` → register in `factory.lock` | manifest schema; id uniqueness; dependency resolution; capability match against each adapter's `capabilities.json`; contract tests; doc generation |
| Modify | bump version; `factory component diff` classifies change as patch/minor/major by contract surface | breaking-change detector on schemas; dependents re-tested |
| Deprecate/Remove | mark `deprecated:` with replacement and sunset version; `factory component remove` refuses if dependents exist unless `--cascade`; removes installed files via lock manifest | orphan scan; stale-reference scan |
| Replace | provide new component implementing same `contract`; `factory component swap old new` runs both against golden fixtures; state migration hook if state schema differs | contract test parity; rollback snapshot |
| Rollback | `factory.lock` pins component hashes; `factory rollback <lock>` | hash verification |

### B3. Registry rules
Single generated registry (`.factory/registry.json`) built from manifests; no hand-edited name lists. Install copies only files listed in the lock (hash + path), so upgrades are 3-way aware (local edits preserved or reported) — fixing the `rm -rf` overwrite hazard recorded in v3.1.x notes.

### B4. Compatibility and lifecycle
Semver for components, major-versioned *contracts*; contracts only change additively within a major. Capability negotiation at install and run time; unsupported optional capability ⇒ degrade with a logged warning, required ⇒ block at install. Deprecation window ≥ 2 minor releases. Security: third-party components must declare permissions; unpinned remote skills are rejected (contrast with current unpinned `mattpocock-skills`/`ponytail` dependencies).
