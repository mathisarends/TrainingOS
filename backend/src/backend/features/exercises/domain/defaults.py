from dataclasses import dataclass
from decimal import Decimal

from backend.features.training.domain import validate_effort
from backend.shared import InvalidInput

from .models import Category


@dataclass(frozen=True)
class CategoryDefaults:
    category: Category
    rest_seconds: int
    sets: int
    reps: int
    target_rpe: Decimal

    def __post_init__(self) -> None:
        if (
            not 0 <= self.rest_seconds <= 3600
            or not 1 <= self.sets <= 100
            or not 1 <= self.reps <= 100
        ):
            raise InvalidInput("Invalid category default bounds")
        validate_effort(self.target_rpe)


def standard_defaults(category: Category) -> CategoryDefaults:
    """Initial category prescriptions from the original TrainingSystems catalog."""
    values = {
        Category.SQUAT: (240, 3, 7, "7.5"),
        Category.BENCH: (180, 4, 8, "8"),
        Category.DEADLIFT: (240, 3, 6, "7"),
        Category.OVERHEAD: (150, 3, 10, "8.5"),
        Category.BACK: (120, 3, 12, "8.5"),
        Category.CHEST: (120, 3, 12, "8.5"),
        Category.SHOULDERS: (90, 3, 12, "8.5"),
        Category.LEGS: (120, 3, 12, "8.5"),
        Category.BICEPS: (90, 3, 12, "8.5"),
        Category.TRICEPS: (90, 3, 12, "8.5"),
    }
    rest, sets, reps, rpe = values[category]
    return CategoryDefaults(category, rest, sets, reps, Decimal(rpe))


def resolve_defaults(stored: list[CategoryDefaults]) -> list[CategoryDefaults]:
    by_category = {item.category: item for item in stored}
    return [by_category.get(category, standard_defaults(category)) for category in Category]
