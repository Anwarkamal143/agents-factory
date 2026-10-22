---
id: DEC-06
title: "Decide: verification isolation level"
type: decision
labels: [type:decision, wayfinder:grilling, mode:HITL, phase:0, mvp, risk:security]
blocked_by: []
skills: [grill-with-docs]
---
## Question
Where does the engine run project verification commands, given they execute agent-authored code?

## Options
| Option | Isolation | Cost |
|---|---|---|
| **A. Host, isolated worktree, allow-listed env, timeout** | Filesystem separation by path only; no network or syscall isolation | Zero extra dependencies |
| B. Container (docker/podman) per verification | Strong: no host secrets, optional no-network | Requires a container runtime; slower; platform differences |
| C. OS sandbox profile (e.g. macOS sandbox-exec, Linux namespaces) | Medium-strong | Platform-specific code |

## Recommendation
MVP = **A** with a **policy gate**: autonomy L2 and above require either container isolation (B, implemented in T-17) or an explicit `unsafe_host_verify: true` acknowledgement in project config. B becomes mandatory for L3/L4.

## Default if unanswered
A with the acknowledgement requirement. **Safe to proceed with default: yes**, but T-17 cannot close without B or C implemented or a recorded accepted risk.

## Blocks
T-06 (runner design), T-17. Questions for you: (1) Is a container runtime available where this will run? (2) Do your project tests need network access or secrets?

## Resolution
_Pending._
