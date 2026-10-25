from decimal import Decimal as D

import pytest
from backend.features.athletes.domain import Preferences, WeightUnit
from backend.features.training.domain import backoff, e1rm, effort_to_rpe
from backend.shared import InvalidInput

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "weight,reps,rpe,expected",
    [("100", 5, "8", "125"), ("140", 5, "8", "175"), ("101", 1, "10", "105"), ("0", 8, "7", "0")],
)
def test_epley_rounds_up_to_athlete_step(weight: str, reps: int, rpe: str, expected: str) -> None:
    assert e1rm(weight_kg=D(weight), reps=reps, rpe=D(rpe), preferences=Preferences()) == D(
        expected
    )


def test_backoff_inverts_epley_and_rounds_to_nearest_step() -> None:
    assert backoff(maximum_kg=D(125), reps=5, rpe=D(8), preferences=Preferences()) == D("102.5")


def test_lb_rounding_happens_in_display_unit() -> None:
    preferences = Preferences(unit=WeightUnit.LB, rounding_step=D(5))
    result = e1rm(weight_kg=preferences.to_kg(D(220)), reps=5, rpe=D(8), preferences=preferences)
    assert preferences.from_kg(result) == D(275)


@pytest.mark.parametrize("effort", [D(-1), D("0.25"), D("9.5"), D(10)])
def test_invalid_rir_is_rejected(effort: D) -> None:
    with pytest.raises(InvalidInput):
        effort_to_rpe(effort, rir=True)


def test_rir_is_normalized_to_rpe() -> None:
    assert effort_to_rpe(D("2.5"), rir=True) == D("7.5")
