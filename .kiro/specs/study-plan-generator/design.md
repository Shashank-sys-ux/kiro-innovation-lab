# Study Plan Generator — Design

## Architecture
Stateless feature bolted onto the existing FastAPI app and React frontend. No database schema changes; the plan is computed on request and returned as JSON.

```
React form ──POST /study-plan──▶ FastAPI route
                                     │
                                     ▼
                              Pydantic validation
                                     │
                                     ▼
                           plan_generator.build_plan()
                                     │
                                     ▼
                           JSON response (days[])
```

## Backend

### New module: `backend/app/study_plan.py`
Pure function, no DB dependency.

```python
HOURS_PER_TOPIC = 1.0  # fixed estimate

def build_plan(subject: str, topics: list[str], days: int, hours_per_day: float) -> list[DailyTask]:
    ...
```

**Algorithm (round-robin, hour-aware):**
1. Normalize topics: strip whitespace, drop empties.
2. Compute `capacity_per_day = floor(hours_per_day / HOURS_PER_TOPIC)`. If `capacity_per_day < 1`, raise a validation error (hours-per-day too small for one topic).
3. Compute `total_capacity = capacity_per_day * days`. If `len(topics) > total_capacity`, raise a validation error ("plan does not fit").
4. Distribute topics across days by iterating topics in order and assigning to day `i % days` (1-indexed), skipping any day already at `capacity_per_day`. This guarantees:
   - every topic lands in `1..days`,
   - no day exceeds its hour budget,
   - workload is evenly spread.
5. For each day 1..days, emit a `DailyTask` with the ordered topics assigned and `estimated_hours = len(topics_that_day) * HOURS_PER_TOPIC`. Days with no topics get an empty list and 0.0 hours.

### Pydantic schemas
Added to `backend/app/study_plan.py` (kept alongside the algorithm to keep the feature self-contained).

```python
class StudyPlanRequest(BaseModel):
    subject: str = Field(min_length=1)
    topics: list[str] = Field(min_length=1)
    days: int = Field(ge=1)
    hours_per_day: float = Field(gt=0)

class DailyTask(BaseModel):
    day: int              # 1-indexed
    topics: list[str]
    estimated_hours: float

class StudyPlanResponse(BaseModel):
    subject: str
    days: list[DailyTask]
```

- `subject` is `min_length=1` after strip (validator strips before checking).
- A field validator on `topics` strips each string and rejects the request if the resulting list is empty.

### Route: `backend/app/main.py`
Add a single endpoint. No changes to existing routes.

```python
@app.post("/study-plan", response_model=StudyPlanResponse)
def generate_study_plan(payload: StudyPlanRequest) -> StudyPlanResponse:
    try:
        daily = build_plan(payload.subject, payload.topics, payload.days, payload.hours_per_day)
    except PlanValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return StudyPlanResponse(subject=payload.subject, days=daily)
```

`PlanValidationError` is a small local exception raised by `build_plan` for the "does not fit" and "hours-per-day too small" cases that Pydantic can't express with simple field constraints.

## Frontend

### New component: `frontend/src/StudyPlanGenerator.tsx`
A single self-contained component rendered from `App.tsx` (added below the hero, existing content untouched).

**State:**
- `subject: string`
- `topicsInput: string` (comma-separated; parsed on submit)
- `days: number`
- `hoursPerDay: number`
- `plan: StudyPlanResponse | null`
- `error: string | null`
- `loading: boolean`

**Behavior:**
1. Form fields are controlled inputs. Numeric inputs use `type="number"`.
2. On submit, parse topics by splitting on `,`, trimming, and dropping empties.
3. POST to `http://localhost:8000/study-plan` with JSON body.
4. On 2xx, store response in `plan`.
5. On non-2xx, read `detail` (string or Pydantic error list) and store a display string in `error`.
6. When `plan` is set, render a list of `Day N — X.X hrs` with topics as sub-items.

### API type
```ts
type DailyTask = { day: number; topics: string[]; estimated_hours: number };
type StudyPlanResponse = { subject: string; days: DailyTask[] };
```

Kept inline in the component file; no shared types module needed for a single-consumer type.

## Error handling
- Pydantic field violations → FastAPI's default 422 body (`detail` is a list). Frontend flattens the first message for display.
- `PlanValidationError` from `build_plan` → 422 with a plain string `detail`.
- Network / unknown errors → frontend shows a generic "Could not generate plan" message.

## Testing strategy
Unit tests for `build_plan` covering: even distribution, uneven remainder, hour budget respected, empty topics after strip, capacity-exceeded, hours-per-day-too-small. (Only if the user later asks for tests — not part of the initial task list per the project's default.)

## Non-goals recap
- No persistence layer.
- No modifications to `Topic` / `Question` tables or endpoints.
- No auth.
- No AI/LLM topic estimation. Fixed 1 hour per topic keeps the feature deterministic and easy to reason about; it can be revisited later.
