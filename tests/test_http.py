import pytest
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
from src.func_python.http import ASGIApplication, DefaultFunction


def test_hello_world():
    print("Hello, World!")


@pytest.fixture
async def test_server():
    async def handle(scope, receive, send):
        assert scope["type"] == "http"
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"text/plain")],
            }
        )
        await send({"type": "http.response.body", "body": b"Hello, Server!"})

    app = ASGIApplication(DefaultFunction(handle))
    config = Config()
    config.bind = ["127.0.0.1:8081"]

    print("Starting test server on 127.0.0.1:8081")
    server_task = asyncio.create_task(serve(app, config))

    await asyncio.sleep(1)
    yield
    print("Stopping test server")
    server_task.cancel()
    await asyncio.sleep(1)  # Allow time for server shutdown
    print("Server stopped")


@pytest.mark.asyncio
async def test_server_running(test_server):
    import httpx

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8081") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert response.text == "Hello, Server!"
