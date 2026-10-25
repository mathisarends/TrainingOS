from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from backend.shared import Aggregate, InvalidInput


class WeightUnit(StrEnum):
    KG = "kg"
    LB = "lb"


class EffortScale(StrEnum):
    RPE = "rpe"
    RIR = "rir"


@dataclass(frozen=True)
class Preferences:
    unit: WeightUnit = WeightUnit.KG
    rounding_step: Decimal = Decimal("2.5")
    effort_scale: EffortScale = EffortScale.RPE
    target_weight_kg: Decimal | None = None
    timezone: str = "Europe/Berlin"

    def __post_init__(self) -> None:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        if not self.rounding_step.is_finite() or self.rounding_step <= 0:
            raise InvalidInput("Rounding step must be positive")
        try:
            ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise InvalidInput("Unknown timezone") from exc

    def to_kg(self, weight: Decimal) -> Decimal:
        return weight if self.unit == WeightUnit.KG else weight * Decimal("0.45359237")

    def from_kg(self, weight: Decimal) -> Decimal:
        return weight if self.unit == WeightUnit.KG else weight / Decimal("0.45359237")


class User(Aggregate):
    def __init__(self, *, preferences: Preferences | None = None, id: UUID | None = None) -> None:
        super().__init__(id=id)
        self._preferences = preferences or Preferences()

    @property
    def preferences(self) -> Preferences:
        return self._preferences

    def configure(self, preferences: Preferences) -> None:
        self._preferences = preferences
