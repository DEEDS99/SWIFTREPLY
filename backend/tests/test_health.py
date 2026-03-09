"""Basic backend tests."""

import pytest
from httpx import AsyncClient
from httpx import ASGITransport


@pytest.mark.asyncio
async def test_health():
    """Test the health endpoint."""
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_root():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["app"] == "SwiftReply"
