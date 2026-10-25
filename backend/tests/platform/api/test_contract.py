import ast
from pathlib import Path
from uuid import uuid4

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.contract, pytest.mark.integration]


async def test_openapi_has_unique_operations_and_named_problem_contracts(
    client: AsyncClient,
) -> None:
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    operations = [
        operation
        for path in schema["paths"].values()
        for method, operation in path.items()
        if method in {"get", "post", "put", "delete", "patch"}
    ]
    ids = [operation["operationId"] for operation in operations]
    assert len(ids) == len(set(ids))
    create = schema["paths"]["/api/v1/plans"]["post"]
    for status in ("401", "404", "409", "422"):
        assert "application/problem+json" in create["responses"][status]["content"]
    missing = await client.get(f"/api/v1/plans/{uuid4()}")
    assert missing.status_code == 404
    assert missing.json()["code"] == "not_found"


@pytest.mark.parametrize("updates", [{"weeks": 0}, {"title": " "}, {"unknown": True}])
async def test_invalid_payload_does_not_mutate_plan_list(
    client: AsyncClient, updates: dict
) -> None:
    body = {
        "title": "Plan",
        "start_date": "2026-10-26",
        "weeks": 1,
        "days": [{"name": "A", "weekday": 0}],
    }
    response = await client.post("/api/v1/plans", json=body | updates)
    assert response.status_code == 422
    assert response.json()["code"] == "request_validation_error"
    assert (await client.get("/api/v1/plans")).json()["items"] == []


def test_domain_and_application_keep_framework_and_adapter_dependencies_out() -> None:
    source = Path(__file__).parents[3] / "src" / "backend"
    forbidden = {
        "fastapi",
        "fastapi_canon",
        "dishka",
        "sqlalchemy",
        "sqlmodel",
        "pydantic",
        "httpx",
        "jwt",
    }
    for path in (source / "features").rglob("*.py"):
        if not ({"domain", "application"} & set(path.parts)):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert module.split(".")[0] not in forbidden, path
                assert "infrastructure" not in module.split("."), path
                assert "presentation" not in module.split("."), path
            elif isinstance(node, ast.Import):
                assert not any(alias.name.split(".")[0] in forbidden for alias in node.names), path
