---
id: SPK-03
title: "Spike: GitHub merge and check semantics (only if DEC-04 says yes)"
type: spike
labels: [type:spike, wayfinder:research, mode:AFK, phase:0, post-mvp]
blocked_by: [DEC-04]
skills: [research]
---
## Question
When the engine delivers via GitHub, what exactly happens with a head-pinned merge under branch protection, required status checks, and a merge queue? Specifically: does a merge pinned to the reviewed head fail when the head moves, how do required checks interact, and what error shapes does the CLI/API return for each refusal reason (so the engine can map them to task-level `blocked` instead of a whole-run halt, the defect found in the analyzed tool).

## Method
In a **sandbox** repo you own: enable branch protection with one required check; test merge of a green PR, a PR whose head moved after review, a PR with a failing required check, and (if available) a merge queue. Record command, flags, exit code, and the stderr/JSON for each. If DEC-04 resolved to "no", close this ticket as `wontfix` with a note.

## Output
`docs/spikes/SPK-03.md` with the refusal-reason table and a recommended mapping to engine task states.

## Blocks
T-23.
