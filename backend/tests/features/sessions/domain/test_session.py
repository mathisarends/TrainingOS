from datetime import UTC, datetime, timedelta
from decimal import Decimal as D
from uuid import uuid4

import pytest

from backend.features.exercises.domain import Category
from backend.features.plans.domain import Prescription
from backend.features.sessions.domain import Session, SessionSlot
from backend.shared import Conflict, InvalidInput

pytestmark = pytest.mark.unit


def test_timer_uses_absolute_deadline_and_completion_clears_it() -> None:
    now = datetime(2026, 10, 25, 12, tzinfo=UTC)
    slot = SessionSlot(
        id=uuid4(),
        exercise_id=uuid4(),
        exercise_name="Squat",
        category=Category.SQUAT,
        main=True,
        rest_seconds=180,
        prescription=Prescription(week=1, sets=3, reps=5, target_rpe=D(8)),
    )
    session = Session(
        athlete_id=uuid4(),
        plan_id=uuid4(),
        plan_title="Plan",
        day_id=uuid4(),
        day_name="A",
        week=1,
        slots=(slot,),
        started_at=now,
    )
    session.record(slot_id=slot.id, weight_kg=D(100), reps=5, rpe=D(8), now=now)
    assert session.rest_ends_at == now + timedelta(seconds=180)
    with pytest.raises(Conflict):
        session.skip(slot_id=slot.id, skipped=True)
    session.finish(now + timedelta(minutes=45))
    assert session.duration_seconds == 2700
    assert session.rest_ends_at is None


@pytest.mark.parametrize("start_delta,end_delta", [(2, 1), (0, -1), (-2, 1)])
def test_session_correction_rejects_invalid_or_future_time(
    start_delta: int, end_delta: int
) -> None:
    now = datetime(2026, 10, 25, 12, tzinfo=UTC)
    session = Session(
        athlete_id=uuid4(),
        plan_id=uuid4(),
        plan_title="Plan",
        day_id=uuid4(),
        day_name="A",
        week=1,
        slots=(),
        started_at=now,
    )
    with pytest.raises(InvalidInput):
        session.correct_times(
            started_at=now + timedelta(minutes=start_delta),
            ended_at=now + timedelta(minutes=end_delta),
            now=now,
        )
