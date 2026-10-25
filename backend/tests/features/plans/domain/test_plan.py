from dataclasses import replace
from datetime import date
from decimal import Decimal as D
from uuid import uuid4

from backend.features.exercises.domain import Category
from backend.features.plans.domain import Plan, Prescription, Slot, TrainingDay


def test_progression_caps_effort_and_preserves_identity() -> None:
    main = Slot(
        id=uuid4(),
        exercise_id=uuid4(),
        exercise_name="Squat",
        category=Category.SQUAT,
        main=True,
        rest_seconds=180,
        prescriptions=(Prescription(week=1, sets=3, reps=5, target_rpe=D(8)),),
    )
    accessory = replace(main, id=uuid4(), main=False)
    day = TrainingDay(id=uuid4(), name="A", weekday=0, slots=(main, accessory))
    plan = Plan(
        athlete_id=uuid4(), title="Strength", start_date=date(2026, 10, 26), weeks=5, days=(day,)
    )
    plan.progress(increment=D(1), deload=True)
    first, second = plan.days[0].slots
    assert (first.id, second.id) == (main.id, accessory.id)
    assert [p.target_rpe for p in first.prescriptions] == [D(8), D(9), D(9), D(9), D(6)]
    assert [p.target_rpe for p in second.prescriptions] == [D(8), D(9), D(10), D(10), D(7)]
    assert first.prescriptions[-1].sets == 2
    duplicate = plan.duplicate(
        athlete_id=plan.athlete_id, title="Copy", start_date=date(2026, 12, 1)
    )
    assert duplicate.id != plan.id
    assert duplicate.days[0].id != day.id
    assert duplicate.days[0].slots[0].id != main.id
    assert duplicate.days[0].slots[0].prescriptions == first.prescriptions
