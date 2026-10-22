---
id: SPK-02
title: "Spike: structured output, cancel and resume for the chosen harness"
type: spike
labels: [type:spike, wayfinder:research, mode:AFK, phase:0, ready-for-agent]
blocked_by: [DEC-02]
skills: [research]
---
## Question
For the DEC-02 harness: how reliably can it return output that validates against a JSON Schema in non-interactive mode, can a running session be cancelled cleanly (process group kill, partial output behaviour), and can a session be resumed? These facts set the adapter's `capabilities.json` and the repair strategy.

## Method
1. Define the `task-result` schema (SPEC-01 "Contracts") as a file.
2. Run a trivial deterministic task (e.g. "create file X with content Y and report it") **20 times** with the harness's native structured-output flag if it has one, and 20 times with prompt-only JSON. Record the schema-valid rate, the failure modes (prose around JSON, truncated JSON, wrong enum), and whether one automatic repair attempt fixes them.
3. Cancel test: start a long task, send the documented cancel/interrupt, then kill the process group; record leftover child processes, partial files, exit code, time to stop.
4. Resume test: capture the session/resume identifier if one exists; resume after kill; record whether context survives.
5. Record exact CLI flags, versions, environment variables required, and usage/token reporting availability.

## Output
Commit `docs/spikes/SPK-02.md` with the tables above and a **draft `capabilities.json`** for the adapter using the SPEC-01 capability vocabulary. State the recommended `structured_output` mode (`native`/`prompt`) and whether repair-once is sufficient. No engine code.

## Blocks
T-13 (and confirms DEC-02).
