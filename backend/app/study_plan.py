"""Study plan generation.

Pure, stateless module. No database, no framework coupling beyond Pydantic.
See .kiro/specs/study-plan-generator/design.md for the algorithm rationale.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

HOURS_PER_TOPIC: float = 1.0


class PlanValidationError(ValueError):
    """Raised when inputs are structurally valid but the plan can't be built."""


class StudyPlanRequest(BaseModel):
    subject: str = Field(min_length=1)
    topics: list[str] = Field(min_length=1)
    days: int = Field(ge=1)
    hours_per_day: float = Field(gt=0)

    @field_validator("subject")
    @classmethod
    def _strip_subject(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("subject must not be blank")
        return v

    @field_validator("topics")
    @classmethod
    def _clean_topics(cls, v: list[str]) -> list[str]:
        cleaned = [t.strip() for t in v if t and t.strip()]
        if not cleaned:
            raise ValueError("topics must contain at least one non-blank entry")
        return cleaned


class DailyTask(BaseModel):
    day: int
    topics: list[str]
    estimated_hours: float


class StudyPlanResponse(BaseModel):
    subject: str
    days: list[DailyTask]


def build_plan(
    subject: str,
    topics: list[str],
    days: int,
    hours_per_day: float,
) -> list[DailyTask]:
    """Distribute topics across `days`, respecting `hours_per_day`.

    Raises PlanValidationError when the workload cannot fit.
    """
    if days < 1:
        raise PlanValidationError("days must be >= 1")
    if hours_per_day <= 0:
        raise PlanValidationError("hours_per_day must be > 0")

    cleaned = [t.strip() for t in topics if t and t.strip()]
    if not cleaned:
        raise PlanValidationError("topics must contain at least one non-blank entry")

    capacity_per_day = int(hours_per_day // HOURS_PER_TOPIC)
    if capacity_per_day < 1:
        raise PlanValidationError(
            "hours_per_day is too small to fit a single topic"
        )

    total_capacity = capacity_per_day * days
    if len(cleaned) > total_capacity:
        raise PlanValidationError(
            f"plan does not fit: {len(cleaned)} topics require more than "
            f"{total_capacity} hours available ({days} days * {capacity_per_day}h)"
        )

    # Round-robin assignment, skipping full days.
    buckets: list[list[str]] = [[] for _ in range(days)]
    idx = 0
    for topic in cleaned:
        # advance until we find a day with remaining capacity
        while len(buckets[idx % days]) >= capacity_per_day:
            idx += 1
        buckets[idx % days].append(topic)
        idx += 1

    return [
        DailyTask(
            day=i + 1,
            topics=bucket,
            estimated_hours=len(bucket) * HOURS_PER_TOPIC,
        )
        for i, bucket in enumerate(buckets)
    ]
