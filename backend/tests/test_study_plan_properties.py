"""Property-based tests for app.study_plan.build_plan.

Invariants (from the spec):
  1. Every input topic appears exactly once in the plan.
  2. Every day in the plan is in 1..days.
  3. No day's assigned hours exceed hours_per_day.
  4. Total assigned hours == len(topics) * HOURS_PER_TOPIC.
  5. The plan contains exactly `days` entries.
  6. Topic ordering may vary; no topic is lost or duplicated.

Invalid-input tests confirm PlanValidationError is raised for:
  - empty topics (including all-blank)
  - days < 1
  - hours_per_day <= 0
  - required hours exceed total available hours
"""

from __future__ import annotations

import math
from collections import Counter

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from app.study_plan import (
    HOURS_PER_TOPIC,
    PlanValidationError,
    build_plan,
)

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Non-blank topic strings. Restrict the alphabet so cleaning is predictable
# and to avoid surrogate/whitespace-only surprises.
topic_strategy = st.text(
    alphabet=st.characters(
        min_codepoint=33, max_codepoint=126, blacklist_categories=("Cs",)
    ),
    min_size=1,
    max_size=20,
).filter(lambda s: s.strip() != "")

subject_strategy = st.text(min_size=1, max_size=30).filter(lambda s: s.strip() != "")


@st.composite
def valid_plan_inputs(draw):
    """Draw (subject, topics, days, hours_per_day) that build_plan will accept.

    Guarantees capacity_per_day >= 1 and len(topics) <= capacity_per_day * days.
    """
    subject = draw(subject_strategy)
    days = draw(st.integers(min_value=1, max_value=30))
    hours_per_day = draw(
        st.floats(
            min_value=HOURS_PER_TOPIC,
            max_value=12.0,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    capacity_per_day = int(hours_per_day // HOURS_PER_TOPIC)
    assume(capacity_per_day >= 1)
    max_topics = capacity_per_day * days
    n_topics = draw(st.integers(min_value=1, max_value=min(max_topics, 60)))
    topics = draw(
        st.lists(topic_strategy, min_size=n_topics, max_size=n_topics)
    )
    return subject, topics, days, hours_per_day


# ---------------------------------------------------------------------------
# Invariants on valid inputs
# ---------------------------------------------------------------------------


@given(valid_plan_inputs())
@settings(max_examples=200, deadline=None)
def test_plan_has_exactly_requested_days(inputs):
    subject, topics, days, hours_per_day = inputs
    plan = build_plan(subject, topics, days, hours_per_day)
    # Invariant 5.
    assert len(plan) == days


@given(valid_plan_inputs())
@settings(max_examples=200, deadline=None)
def test_day_numbers_are_in_range(inputs):
    subject, topics, days, hours_per_day = inputs
    plan = build_plan(subject, topics, days, hours_per_day)
    # Invariant 2.
    day_numbers = [d.day for d in plan]
    assert day_numbers == list(range(1, days + 1))
    for d in plan:
        assert 1 <= d.day <= days


@given(valid_plan_inputs())
@settings(max_examples=200, deadline=None)
def test_every_topic_appears_exactly_once(inputs):
    subject, topics, days, hours_per_day = inputs
    plan = build_plan(subject, topics, days, hours_per_day)
    scheduled = [t for d in plan for t in d.topics]
    # Invariants 1 and 6: same multiset as input topics (after the module's
    # own trimming, which is a no-op here because we generate non-blank tokens).
    assert Counter(scheduled) == Counter(topics)


@given(valid_plan_inputs())
@settings(max_examples=200, deadline=None)
def test_no_day_exceeds_hour_budget(inputs):
    subject, topics, days, hours_per_day = inputs
    plan = build_plan(subject, topics, days, hours_per_day)
    # Invariant 3. Use a tiny tolerance to be robust against float representation.
    for d in plan:
        assert d.estimated_hours <= hours_per_day + 1e-9
        assert math.isclose(
            d.estimated_hours, len(d.topics) * HOURS_PER_TOPIC, rel_tol=0, abs_tol=1e-9
        )


@given(valid_plan_inputs())
@settings(max_examples=200, deadline=None)
def test_total_hours_matches_topic_count(inputs):
    subject, topics, days, hours_per_day = inputs
    plan = build_plan(subject, topics, days, hours_per_day)
    total = sum(d.estimated_hours for d in plan)
    # Invariant 4.
    assert math.isclose(total, len(topics) * HOURS_PER_TOPIC, abs_tol=1e-9)


# ---------------------------------------------------------------------------
# Invalid-input tests
# ---------------------------------------------------------------------------


@given(
    days=st.integers(min_value=1, max_value=10),
    hours_per_day=st.floats(
        min_value=1.0, max_value=8.0, allow_nan=False, allow_infinity=False
    ),
)
def test_empty_topics_raises(days, hours_per_day):
    with pytest.raises(PlanValidationError):
        build_plan("Math", [], days, hours_per_day)


@given(
    blanks=st.lists(
        st.sampled_from(["", " ", "   ", "\t", "\n"]), min_size=1, max_size=6
    ),
    days=st.integers(min_value=1, max_value=10),
    hours_per_day=st.floats(
        min_value=1.0, max_value=8.0, allow_nan=False, allow_infinity=False
    ),
)
def test_all_blank_topics_raises(blanks, days, hours_per_day):
    with pytest.raises(PlanValidationError):
        build_plan("Math", blanks, days, hours_per_day)


@given(
    days=st.integers(max_value=0),
    hours_per_day=st.floats(
        min_value=1.0, max_value=8.0, allow_nan=False, allow_infinity=False
    ),
    topics=st.lists(topic_strategy, min_size=1, max_size=5),
)
def test_days_less_than_one_raises(days, hours_per_day, topics):
    with pytest.raises(PlanValidationError):
        build_plan("Math", topics, days, hours_per_day)


@given(
    days=st.integers(min_value=1, max_value=10),
    hours_per_day=st.floats(
        max_value=0.0, allow_nan=False, allow_infinity=False
    ),
    topics=st.lists(topic_strategy, min_size=1, max_size=5),
)
def test_hours_per_day_non_positive_raises(days, hours_per_day, topics):
    with pytest.raises(PlanValidationError):
        build_plan("Math", topics, days, hours_per_day)


@st.composite
def overcapacity_inputs(draw):
    """Inputs where topics exceed total capacity (days * capacity_per_day)."""
    days = draw(st.integers(min_value=1, max_value=10))
    hours_per_day = draw(
        st.floats(
            min_value=HOURS_PER_TOPIC,
            max_value=6.0,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    capacity_per_day = int(hours_per_day // HOURS_PER_TOPIC)
    assume(capacity_per_day >= 1)
    total_capacity = capacity_per_day * days
    n_topics = draw(st.integers(min_value=total_capacity + 1, max_value=total_capacity + 20))
    topics = draw(st.lists(topic_strategy, min_size=n_topics, max_size=n_topics))
    return topics, days, hours_per_day


@given(overcapacity_inputs())
@settings(max_examples=100, deadline=None)
def test_overcapacity_raises(inputs):
    topics, days, hours_per_day = inputs
    with pytest.raises(PlanValidationError):
        build_plan("Math", topics, days, hours_per_day)
