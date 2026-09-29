# Study Plan — Invariants Reference

Formal statement of the invariants that `build_plan` must uphold. Each is mirrored by a property-based test in `backend/tests/test_study_plan_properties.py`.

Let:
- `T` = the list of trimmed, non-blank input topics (after `strip` and dropping empties).
- `D` = the requested `days`, an integer `>= 1`.
- `H` = the requested `hours_per_day`, a float `> 0`.
- `C = floor(H / HOURS_PER_TOPIC)` = capacity per day (topics), required to be `>= 1`.
- `plan` = the returned `list[DailyTask]`.

## I1 — Full coverage, no duplication
`Counter([t for d in plan for t in d.topics]) == Counter(T)`

Every input topic (after cleaning) appears exactly once. Ordering within and across days may vary.

## I2 — Day count and range
- `len(plan) == D`.
- For every `d` in `plan`: `1 <= d.day <= D`.
- The `day` values are exactly `1, 2, ..., D` in order.

Empty days (with no topics) are permitted and valid.

## I3 — Hour budget per day
For every `d` in `plan`:
- `d.estimated_hours == len(d.topics) * HOURS_PER_TOPIC`
- `d.estimated_hours <= H` (within float tolerance `1e-9`)

## I4 — Total hours
`sum(d.estimated_hours for d in plan) == len(T) * HOURS_PER_TOPIC`

## I5 — Rejection of invalid inputs

`PlanValidationError` is raised (before any distribution is attempted) when:

| Condition | Reason string (representative) |
|---|---|
| `D < 1` | `"days must be >= 1"` |
| `H <= 0` | `"hours_per_day must be > 0"` |
| `T` is empty after trimming | `"topics must contain at least one non-blank entry"` |
| `C < 1` (i.e. `H < HOURS_PER_TOPIC`) | `"hours_per_day is too small to fit a single topic"` |
| `len(T) > C * D` | `"plan does not fit: ..."` |

Pydantic field constraints on `StudyPlanRequest` also raise structured 422s for `days < 1`, `hours_per_day <= 0`, blank `subject`, and empty/all-blank `topics` at the route boundary — but `build_plan` itself must remain robust to being called with the same values directly.

## Notes on tolerance
- All hour comparisons use an absolute tolerance of `1e-9` in tests, since `estimated_hours` is a float.
- Do not introduce floating-point arithmetic that accumulates error across days; compute each day's hours from `len(bucket) * HOURS_PER_TOPIC` directly.
