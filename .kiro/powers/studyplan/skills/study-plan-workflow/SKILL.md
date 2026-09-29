---
name: study-plan-workflow
description: Orient in the StudyPilot study-plan feature and make focused, invariant-preserving edits to backend/app/study_plan.py or the POST /study-plan route. Activate for any task that mentions study plans, build_plan, HOURS_PER_TOPIC, hours_per_day, or the /study-plan endpoint.
---

# Study Plan Workflow

Use this skill whenever a request touches StudyPilot's study-plan generation feature. It exists to keep changes small, keep the planning invariants intact, and keep the pure/adapter split clean.

## 1. Domain in one paragraph

A student provides a `subject`, a list of `topics`, a `days` count, and `hours_per_day`. The system returns a plan of exactly `days` `DailyTask` entries. Every topic appears exactly once across the days. No day exceeds `hours_per_day`. `HOURS_PER_TOPIC` is a fixed constant (currently `1.0`) — the plan estimates hours as `len(topics_that_day) * HOURS_PER_TOPIC`. Invalid inputs raise `PlanValidationError` and are translated to HTTP 422 at the route boundary. The plan is computed on demand and not persisted.

Deeper background: see `references/invariants.md` and `references/api-contract.md` in this skill.

## 2. Files that matter

| Path | Role | Touch when |
|---|---|---|
| `backend/app/study_plan.py` | Pure module: `build_plan`, Pydantic request/response, `PlanValidationError` | Algorithm changes, new validation rules, schema tweaks |
| `backend/app/main.py` (`POST /study-plan`) | Thin FastAPI adapter over `build_plan` | Route-shape changes, error mapping |
| `backend/tests/test_study_plan_properties.py` | Hypothesis property tests | Any behavior change — update or add strategies |
| `.kiro/specs/study-plan-generator/*` | Spec (requirements, design, tasks) | If scope changes, update spec first |
| `.kiro/steering/*` | Product, architecture, coding standards | Read once per task; treat as constraints, not targets to edit |

Do not touch: `models.py`, `database.py`, existing `/topics`, `/questions` routes, or the frontend for backend-only tasks.

## 3. The invariants — non-negotiable

Any change to `build_plan` must keep all of these true for every valid input:

1. **Full coverage, no duplication.** `Counter(all_scheduled_topics) == Counter(input_topics)` after trimming.
2. **Day range.** Every `DailyTask.day` is in `1..days`, and there are exactly `days` entries (empty days allowed).
3. **Hour budget.** `DailyTask.estimated_hours <= hours_per_day` for every day.
4. **Total hours.** `sum(estimated_hours) == len(cleaned_topics) * HOURS_PER_TOPIC`.
5. **Rejection of invalid inputs.** Empty/blank topics, `days < 1`, `hours_per_day <= 0`, and workload exceeding `days * floor(hours_per_day / HOURS_PER_TOPIC)` all raise `PlanValidationError`.

If a proposed change would violate any of these, stop and surface the trade-off to the user before implementing.

## 4. Standard workflow

Follow these steps in order for any planning-related change:

1. **Read before writing.**
   - Read `backend/app/study_plan.py` end to end.
   - Read `backend/tests/test_study_plan_properties.py` to see which invariants are already asserted.
   - If the task mentions the endpoint, read the `POST /study-plan` handler in `main.py`.
2. **Check the steering docs.** `.kiro/steering/product.md`, `architecture.md`, and `coding-standards.md` set the constraints (local-first, pure modules, thin handlers, type hints, black-style formatting, small functions).
3. **Locate the smallest surface.** Prefer editing `build_plan` or its helpers over introducing new modules. Prefer extending a Pydantic validator over a new endpoint. If a change would spill into `models.py` or the DB layer, it probably belongs in a new feature, not this one.
4. **Preserve the pure/adapter split.** `study_plan.py` must not import FastAPI, SQLAlchemy, or `database.py`. The route handler in `main.py` stays a thin translator between HTTP and `build_plan`.
5. **Update tests together with code.** New behavior gets a new property (strategy-based) in `test_study_plan_properties.py`. Fixed regressions get a targeted test that would have caught the bug.
6. **Run the tests.** From `backend/`:
   ```
   .\.venv\Scripts\python.exe -m pytest tests/test_study_plan_properties.py -v
   ```
   All properties must pass. If Hypothesis reports a shrunk counterexample, fix the code — don't loosen the property.
7. **Sanity-check the endpoint if it changed.** Manual POST via `curl` or the frontend form; expect 200 for valid input, 422 for invalid.

## 5. Design defaults for this feature

- `HOURS_PER_TOPIC` stays `1.0` unless the user explicitly asks to change it. Per-topic duration is out of scope for this iteration.
- Plans are **not persisted**. Do not add tables, migrations, or write endpoints for plans without an explicit product-scope decision.
- Validation errors carry human-readable strings in `HTTPException.detail`. The frontend flattens Pydantic's structured error list for display.
- Empty days (no topics assigned) are valid; they render as "Day N — 0.0 hrs" with an empty topic list.

## 6. Common tasks — quick recipes

**Adjust the distribution algorithm.** Change only the loop inside `build_plan`. Keep the pre-validation block (invalid-input checks) and the post-loop `DailyTask` construction untouched. Re-run the property tests — they'll catch any drift on invariants 1–5.

**Add a new validation rule.**
- Prefer a Pydantic `field_validator` on `StudyPlanRequest` for shape checks that Pydantic can express.
- Use `PlanValidationError` inside `build_plan` for rules that depend on relationships between fields (e.g. total capacity).
- Add a matching invalid-input Hypothesis test.

**Change the response shape.** Update `DailyTask` / `StudyPlanResponse`, then update the frontend types in `StudyPlanGenerator.tsx` to mirror them. Do not create a shared types file for a single consumer.

**Fix a reported bug.** Reproduce with a targeted test first (Hypothesis's `@example` decorator on an existing property is often the shortest path). Then fix. Then confirm the property still passes on all generated inputs.

## 7. What not to do

- Do not add a database model, table, or migration for plans.
- Do not import `HOURS_PER_TOPIC` from a config file or environment variable. Keep it a module-level constant.
- Do not swallow `PlanValidationError` inside `build_plan` — let it propagate; the route handler translates it.
- Do not weaken a property test to make a failing implementation pass.
- Do not add unrelated features (topic difficulty, plan editing, AI suggestions) in the same change.

## 8. When in doubt

Re-read the spec at `.kiro/specs/study-plan-generator/design.md` and the steering docs. Both were written to answer these exact questions for future changes. If the requested change conflicts with them, surface the conflict to the user before proceeding.
