## Summary
<!-- The smallest visual that shows the change: a mermaid code block (state, flow or sequence) or a before/after table.
     Pure docs/copy changes may write exactly: Visual: none (reason). Then 2-3 sentences: what changed and why. -->

## Traceability
<!-- Fill every line. One ticket per PR. -->
Closes #<ticket number>
Part of #<spec issue number>
Phase: <n>
Blocked by (merged): <#a (PR #x), #b (PR #y) or none>
Unblocks: <#c, #d or none>
Decisions applied: <DEC-xx, ADR-NNNN or none>

## Evidence
<!-- Real output that proves it: command, exit code, event-log excerpt, before/after. No claims without a command. -->

## Acceptance criteria
<!-- Copy the ticket's checkboxes. Check each one and say where the evidence is (test name or output above). -->
- [ ] <criterion 1> - evidence: <where>

## Merge danger
Door: <one-way or two-way>
Blast radius: <what breaks, for whom, if this is wrong>
Rollback: <revert, or why a revert is not enough>
Residual risks: <none, or list for risk:* tickets>

## Review log
<!-- Final findings table from the fresh-session review, or the words: No findings -->
| id | axis | severity | finding | status |
|----|------|----------|---------|--------|

Findings not addressed (with reasons): <none or list>

## Assumptions and open questions
<!-- Each assumption (non-contractual details only) and each follow-up issue created. -->

## Checklist
- [ ] Lint, type-check and the default test suite pass locally
- [ ] GLOSSARY.md updated for new or changed terms
- [ ] Docs generated from schemas are regenerated (if applicable)
- [ ] ADR added if the decision clears the three-part bar
- [ ] This PR delivers every acceptance criterion of exactly one ticket
