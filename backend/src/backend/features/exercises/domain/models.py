from enum import StrEnum
from uuid import UUID

from backend.shared import Aggregate


class Category(StrEnum):
    SQUAT = "squat"
    BENCH = "bench_press"
    DEADLIFT = "deadlift"
    OVERHEAD = "overhead_press"
    BACK = "back"
    CHEST = "chest"
    SHOULDERS = "shoulders"
    LEGS = "legs"
    BICEPS = "biceps"
    TRICEPS = "triceps"


class Exercise(Aggregate):
    def __init__(
        self,
        *,
        athlete_id: UUID,
        name: str,
        category: Category,
        main: bool = False,
        archived: bool = False,
        id: UUID | None = None,
    ) -> None:
        super().__init__(id=id)
        self._athlete_id = athlete_id
        self._name = name
        self._category = category
        self._main = main
        self._archived = archived

    @property
    def athlete_id(self) -> UUID:
        return self._athlete_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def category(self) -> Category:
        return self._category

    @property
    def main(self) -> bool:
        return self._main

    @property
    def archived(self) -> bool:
        return self._archived

    def revise(self, *, name: str, category: Category, main: bool) -> None:
        self._name, self._category, self._main = name, category, main

    def archive(self) -> None:
        self._archived = True


STANDARD_CATALOG = (
    ("Kniebeuge", Category.SQUAT, True),
    ("Bankdrücken", Category.BENCH, True),
    ("Kreuzheben", Category.DEADLIFT, True),
    ("Überkopfdrücken", Category.OVERHEAD, True),
    ("Langhantelrudern", Category.BACK, False),
    ("Klimmzüge", Category.BACK, False),
    ("Latzug", Category.BACK, False),
    ("Schrägbankdrücken", Category.CHEST, False),
    ("Butterfly", Category.CHEST, False),
    ("Seitheben", Category.SHOULDERS, False),
    ("Reverse Fly", Category.SHOULDERS, False),
    ("Beinpresse", Category.LEGS, False),
    ("Beinbeuger", Category.LEGS, False),
    ("Beinstrecker", Category.LEGS, False),
    ("Wadenheben", Category.LEGS, False),
    ("Bizepscurls", Category.BICEPS, False),
    ("Hammercurls", Category.BICEPS, False),
    ("Trizepsdrücken", Category.TRICEPS, False),
    ("French Press", Category.TRICEPS, False),
)
