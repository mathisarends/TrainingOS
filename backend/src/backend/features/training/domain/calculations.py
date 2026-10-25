from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from backend.features.users.domain import Preferences
from backend.shared import InvalidInput


def validate_effort(rpe: Decimal) -> Decimal:
    if not rpe.is_finite() or not Decimal(1) <= rpe <= Decimal(10) or rpe % Decimal("0.5"):
        raise InvalidInput("RPE must be between 1 and 10 in steps of 0.5")
    return rpe


def effort_to_rpe(value: Decimal, *, rir: bool) -> Decimal:
    return validate_effort(Decimal(10) - value if rir else value)


def e1rm(*, weight_kg: Decimal, reps: int, rpe: Decimal, preferences: Preferences) -> Decimal:
    validate_effort(rpe)
    estimate = preferences.from_kg(weight_kg) * (1 + (Decimal(reps) + 10 - rpe) / 30)
    rounded = (estimate / preferences.rounding_step).to_integral_value(rounding=ROUND_CEILING)
    return preferences.to_kg(rounded * preferences.rounding_step)


def backoff(*, maximum_kg: Decimal, reps: int, rpe: Decimal, preferences: Preferences) -> Decimal:
    validate_effort(rpe)
    weight = preferences.from_kg(maximum_kg) / (1 + (Decimal(reps) + 10 - rpe) / 30)
    rounded = (weight / preferences.rounding_step).to_integral_value(rounding=ROUND_HALF_UP)
    return preferences.to_kg(rounded * preferences.rounding_step)
