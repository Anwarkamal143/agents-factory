---
id: RET-03
title: "Retro: after hardening (production-ready gate)"
type: retro
labels: [type:retro, mode:HITL, phase:6]
blocked_by: [T-17, T-18, T-19]
skills: [retro, handoff]
---
## Scope
Review T-17..T-19 results against the risk register in `docs/analysis/` (security findings S-01..S-13 and reliability findings R-01..R-11): for each finding record **test that proves it is closed**, or **accepted risk with an owner**.

## Output
A PR adding `docs/production-readiness.md` (finding-to-evidence table, open accepted risks, soak results link) plus guidance updates. The factory is "production-ready" only when this document has no unexplained gaps.
