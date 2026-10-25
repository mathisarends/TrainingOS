from decimal import Decimal as D

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


async def test_bodyweight_is_unique_per_date_with_target_in_selected_unit(
    client: AsyncClient,
) -> None:
    await client.put("/api/v1/users/me/preferences", json={"target_weight": 85})
    first = await client.put("/api/v1/bodyweight", json={"date": "2026-10-25", "weight": 80})
    second = await client.put("/api/v1/bodyweight", json={"date": "2026-10-25", "weight": "80.5"})
    assert first.status_code == second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    history = (await client.get("/api/v1/bodyweight")).json()
    assert D(history["target_weight"]) == 85
    assert len(history["items"]) == 1
    assert D(history["items"][0]["weight"]) == D("80.5")
    assert (await client.delete(f"/api/v1/bodyweight/{first.json()['id']}")).status_code == 204
    assert (await client.get("/api/v1/bodyweight")).json()["items"] == []
