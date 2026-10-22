# Decisions and questions

Agents never make design decisions. They surface them in a fixed format, set the right label, and stop. Humans answer in the issue; the agent (or another session) resumes.

## Definitions
- **Decision:** a choice that changes a contract, state machine row, schema field, policy cell, file format, dependency, public command or security posture. Lives in a decision ticket (DEC-xx), resolved once, recorded in SPEC-01 and, if it clears the bar, an ADR.
- **Question:** missing information that is not a design choice (a credential, a convention, a business fact). Asked in the ticket that needs it.
- **Assumption:** a detail that cannot change anything listed above. Allowed, and listed in the PR.

## Templates

### Readiness report (comment on the ticket)
```
**Readiness report for #<N>** (session <time>)
R1 yes - <evidence>
R2 yes - ...
...
R7 NO - SPEC-01 does not say whether <X> is a hard error or a warning
Verdict: NEEDS-DECISION
```

### Decision-needed comment
```
**Decision needed** (blocks #<N>, ticket DEC-<xx> created/linked: #<M>)
Question: <one sentence>
Why it matters: <which AC, seam or contract it changes>
Options:
  A. <option> - for / against
  B. <option> - for / against
Recommendation: <A or B and why>
Safe to proceed with the recommendation? <yes/no, reason>
What I did NOT do: <e.g. no code written for X>
```

### Question comment
```
**Questions for the maintainer** (blocks #<N>)
1. <question> (needed for: <AC or section>)
2. ...
Reply in this thread; I will resume when `needs-info` is removed.
```

### Resolution comment (on the DEC ticket, then close it)
```
**Resolved:** <option chosen, one clause>
Decided by: <name>, <date>
Rationale: <two sentences>
Spec updated: <PR link editing SPEC-01 / ADR path>
Unblocks: #<list>
```

## Who answers and how work resumes
- The maintainer answers by commenting, then removing `needs-info` or `status:needs-decision` (or asking an agent session to do so).
- A decision is only **final** when its ticket is closed **and** the spec text matches (the closing PR edits `docs/spec/SPEC.md`).
- When all blockers of a ticket are closed the `on-merged` workflow comments "Unblocked"; any session may then pick it up.

## Defaults
Decision tickets list a default and say whether proceeding on it is safe. **Agents never apply a default themselves.** The default exists so the maintainer can answer "accept recommendations" in one step. Closing a DEC with "accepted recommendation" is a valid resolution and still requires the resolution comment and the SPEC edit.

## Quick resolution path (maintainer)
Accept every recommendation except DEC-05 (names and license need your explicit input), then run the `README.md` snippet "accept recommended defaults". Answer the questions listed under each decision first if any answer differs from the recommendation.

## Wayfinder map
The map issue (`wayfinder:map`) holds one-line summaries of resolved decisions and the "Not yet specified" fog. When fog becomes a sharp question, create a decision ticket for it (template `decision.md`), add `blocked_by` edges to dependent tickets, and move the line from "Not yet specified" into a ticket link.
