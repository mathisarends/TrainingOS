from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class WeighIn:
    id: UUID
    user_id: UUID
    date: date
    weight_kg: Decimal
