from datetime import UTC, datetime
from uuid import UUID, uuid4


class Entity:
    def __init__(self, *, id: UUID | None = None, created_at: datetime | None = None) -> None:
        self._id = id or uuid4()
        self._created_at = created_at or datetime.now(UTC)

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def created_at(self) -> datetime:
        return self._created_at


Aggregate = Entity
