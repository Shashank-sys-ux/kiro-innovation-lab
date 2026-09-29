---
name: verify-plan-invariants
description: Run and interpret the property-based test suite for StudyPilot's study-plan generator, and inspect a live plan against the invariants. Activate when a change to build_plan, the /study-plan endpoint, or the planning tests needs verification.
---

# Verify Plan Invariants

Use this skill to confirm a change to the study-plan feature is safe. It covers the pytest + Hypothesis run and quick manual inspection.

## 1. Run the property tests

From `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_study_plan_properties.py -v
```

Expected: all tests pass (currently 10). If a property fails:

1. **Read Hypothesis's shrunk counterexample.** It prints the minimal input that broke the invariant.
2. **Do not weaken the property.** The invariants are the contract. Fix the code in `build_plan`.
3. **Rerun.** Continue until every property passes on fresh examples.

To rerun a single test:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_study_plan_properties.py::test_every_topic_appears_exactly_once -v
```

To increase confidence after a risky change, ask Hypothesis for more examples:

```powershell
$env:HYPOTHESIS_PROFILE = "default"
.\.venv\Scripts\python.exe -m pytest tests/test_study_plan_properties.py -v -p hypothesis --hypothesis-seed=random
```

## 2. Inspect a live plan against the invariants

When the endpoint is reachable, generate a plan and eyeball it against the checklist below.

Request (PowerShell):

```powershell
$body = @{
  subject = "Algorithms"
  topics = @("Binary Search", "DFS", "BFS", "Dijkstra")
  days = 2
  hours_per_day = 2.0
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri http://localhost:8000/study-plan -ContentType application/json -Body $body
```

Manual checklist against the response:

- [ ] `days.length == request.days`.
- [ ] `days[i].day == i + 1` for every index.
- [ ] Every request topic appears exactly once across all `days[*].topics`. No duplicates. No extras.
- [ ] `days[i].estimated_hours <= request.hours_per_day` for every `i`.
- [ ] `sum(days[*].estimated_hours) == request.topics.length * 1.0` (HOURS_PER_TOPIC).

If any item fails, treat it the same as a failing property test — fix `build_plan`, not the checklist.

## 3. Verify error paths

Exercise each rejection case and confirm HTTP 422 with a useful message:

| Input | Expected `detail` |
|---|---|
| `topics: []` | Pydantic message about `topics` min length |
| `topics: [" ", ""]` | `"topics must contain at least one non-blank entry"` or Pydantic equivalent |
| `days: 0` | Pydantic message about `days >= 1` |
| `hours_per_day: 0` | Pydantic message about `hours_per_day > 0` |
| `subject: ""` | Pydantic / validator message about blank subject |
| `topics: 4 items, days: 1, hours_per_day: 1` | `"plan does not fit: ..."` from `PlanValidationError` |

Never return HTTP 500 for a validation issue. If a 500 appears, an exception is escaping the handler — trace it and translate it at the boundary.

## 4. When to add a new property

Add a new property (not a new example test) when:

- You add a new invariant to the algorithm (e.g. "no topic repeats within the same day" — already implied by I1 but could be asserted directly).
- You fix a bug that a strategy failed to generate. Adjust the strategy so the bug's neighborhood is now covered, then add a property that would have caught it.

Prefer strategy tweaks over adding `@example` decorators, unless the failing case is genuinely a corner (e.g. `days=1, hours_per_day=1.0, topics=["x"]`).

## 5. Definition of "done" for a planning change

A change is done only when all of the following are true:

1. All property tests pass.
2. The endpoint returns 200 for a representative valid input and 422 for each invalid case listed above.
3. No unrelated files have been modified.
4. The pure/adapter split is preserved (`study_plan.py` has no FastAPI or DB imports).
5. Any behavior change is reflected in either an existing or new property.
