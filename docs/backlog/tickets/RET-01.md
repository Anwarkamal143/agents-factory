---
id: RET-01
title: "Retro: after the walking skeleton and crash-safe state"
type: retro
labels: [type:retro, mode:HITL, phase:1]
blocked_by: [T-03]
skills: [retro, handoff]
---
## Scope
Run `/retro` over the sessions that built T-01..T-03. Look for: tickets that were too big, specs that were vague, review findings that repeat, rules the agent kept violating, friction in the ticket workflow itself (`docs/agents/ticket-runner.md`).

## Output
A PR containing only improvements to repo guidance: `CODING_STANDARDS.md` rules (each backed by an observed miss), `GLOSSARY.md` terms settled, ADRs that clear the three-part bar, adjustments to `docs/agents/*`, and a list of ticket-sizing changes for later phases. No product code. Update the affected downstream tickets' bodies in the same PR if their scope changes.
