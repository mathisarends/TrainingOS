from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from backend.features.users.domain import WeightUnit
from backend.platform.api.schema import Schema


class WeighInRequest(Schema):
    date: date
    weight: Decimal = Field(gt=0, le=1000, decimal_places=4)


class WeighInResponse(Schema):
    id: UUID
    date: date
    weight: Decimal


class BodyweightResponse(Schema):
    unit: WeightUnit
    target_weight: Decimal | None
    items: list[WeighInResponse]
