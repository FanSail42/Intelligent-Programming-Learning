import pytest


@pytest.mark.asyncio
async def test_health_returns_200(client):
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["message"] == "ok"
    assert body["data"]["status"] in ("healthy", "degraded")
    assert "components" in body["data"]
    assert set(body["data"]["components"]) == {"mysql", "redis", "chroma"}
