# Study Plan — API Contract Reference

The wire contract for `POST /study-plan`. Frontend types must mirror these shapes.

## Request

`POST http://localhost:8000/study-plan`

```json
{
  "subject": "Algorithms",
  "topics": ["Binary Search", "DFS", "BFS"],
  "days": 3,
  "hours_per_day": 2.0
}
```

Field rules:
- `subject`: non-blank string (trimmed).
- `topics`: non-empty list of strings. Each string is trimmed; all-blank entries are dropped. The list must be non-empty after cleaning.
- `days`: integer `>= 1`.
- `hours_per_day`: number `> 0`.

## Success response — 200

```json
{
  "subject": "Algorithms",
  "days": [
    { "day": 1, "topics": ["Binary Search"], "estimated_hours": 1.0 },
    { "day": 2, "topics": ["DFS"],           "estimated_hours": 1.0 },
    { "day": 3, "topics": ["BFS"],           "estimated_hours": 1.0 }
  ]
}
```

Guarantees (see `invariants.md`):
- `len(days) == request.days`.
- Union of all `topics` across days equals the cleaned request topics, each appearing exactly once.
- Every `estimated_hours <= request.hours_per_day`.

## Validation error — 422

Two shapes reach the client, both under HTTP 422:

**Pydantic field errors** (structured list from FastAPI's default handler):
```json
{
  "detail": [
    {
      "type": "greater_than",
      "loc": ["body", "hours_per_day"],
      "msg": "Input should be greater than 0",
      "input": 0
    }
  ]
}
```

**`PlanValidationError` from `build_plan`** (plain string, raised as `HTTPException(status_code=422, detail=...)`):
```json
{
  "detail": "plan does not fit: 5 topics require more than 3 hours available (3 days * 1h)"
}
```

The frontend must handle both: if `detail` is a string, show it directly; if it's a list, flatten the first `msg` (optionally prefixed by the last element of `loc`).

## TypeScript mirror

Keep these types inline with `StudyPlanGenerator.tsx`:

```ts
type DailyTask = {
  day: number;
  topics: string[];
  estimated_hours: number;
};

type StudyPlanResponse = {
  subject: string;
  days: DailyTask[];
};

type StudyPlanRequest = {
  subject: string;
  topics: string[];
  days: number;
  hours_per_day: number;
};
```

Do not rename fields on the wire without updating both sides in the same change.
