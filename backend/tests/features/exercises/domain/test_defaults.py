from decimal import Decimal

import pytest

from backend.features.exercises.domain import Category, CategoryDefaults, resolve_defaults
from backend.shared import InvalidInput

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("rest", "sets", "reps", "rpe"),
    [
        (-1, 3, 8, "8"),
        (3601, 3, 8, "8"),
        (90, 0, 8, "8"),
        (90, 3, 101, "8"),
        (90, 3, 8, "8.1"),
        (90, 3, 8, "NaN"),
    ],
)
def test_invalid_defaults_are_rejected(rest: int, sets: int, reps: int, rpe: str) -> None:
    with pytest.raises(InvalidInput):
        CategoryDefaults(Category.SQUAT, rest, sets, reps, Decimal(rpe))


def test_resolving_missing_categories_preserves_the_users_custom_defaults() -> None:
    custom = CategoryDefaults(Category.SQUAT, 300, 5, 4, Decimal("9"))
    resolved = resolve_defaults([custom])
    assert len(resolved) == len(Category)
    assert resolved[0] == custom
    bench = next(item for item in resolved if item.category == Category.BENCH)
    assert (bench.rest_seconds, bench.sets, bench.reps, bench.target_rpe) == (180, 4, 8, 8)
