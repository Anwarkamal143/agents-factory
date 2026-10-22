# Labels

Created from `docs/backlog/labels.json` by `tools/backlog/create-labels.sh`. `backlog.py validate` rejects any label a ticket uses that is not listed there.

## Canonical triage vocabulary (AI Hero setup skill)
| Role | Label here |
|---|---|
| Needs a maintainer to evaluate | `needs-triage` |
| Waiting on the reporter or maintainer | `needs-info` |
| Fully specified, an agent can pick it up | `ready-for-agent` |
| Needs a human to do it | `ready-for-human` |
| Will not be actioned | `wontfix` |
| Wayfinder map and ticket kinds | `wayfinder:map`, `wayfinder:grilling`, `wayfinder:research`, `wayfinder:prototype`, `wayfinder:task` |

## Our extra labels
| Group | Labels | Meaning |
|---|---|---|
| type | `type:spec`, `type:build`, `type:decision`, `type:spike`, `type:chore`, `type:retro` | What kind of work. Spec, decision and retro are never agent-pickable. |
| status | `status:in-progress`, `status:in-review`, `status:blocked`, `status:needs-decision` | Live state; set and cleared by the runner and `on-merged`. |
| mode | `mode:AFK`, `mode:HITL` | AFK: can run unattended. HITL: a human must be in the loop. |
| phase | `phase:0` ... `phase:7` | Shaping, Foundation, Engine, Git+review, Real adapter, Lifecycle, Hardening, DX (post-MVP). |
| size | `size:S`, `size:M`, `size:L` | `L` must be split before `ready-for-agent`. |
| risk | `risk:one-way-door`, `risk:security` | Raises review and approval bar; maintainer approval required to merge. |
| scope | `mvp`, `post-mvp` | MVP is T-01..T-16 plus their decisions; hardening T-17..T-19 gates "production-ready". |
