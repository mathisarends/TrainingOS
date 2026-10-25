from decimal import Decimal
from uuid import UUID

from pydantic import Field

from backend.features.users.domain import EffortScale, WeightUnit
from backend.platform.api.schema import Schema


class PreferencesRequest(Schema):
    unit: WeightUnit = WeightUnit.KG
    rounding_step: Decimal = Field(default=Decimal("2.5"), gt=0, le=100)
    effort_scale: EffortScale = EffortScale.RPE
    target_weight: Decimal | None = Field(default=None, gt=0, le=1000)
    timezone: str = Field(default="Europe/Berlin", max_length=100)


class UserResponse(Schema):
    id: UUID
    unit: WeightUnit
    rounding_step: Decimal
    effort_scale: EffortScale
    target_weight: Decimal | None
    timezone: str
