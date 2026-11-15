"""Exercise the portable client against a real HTTP server, without HA stubs."""
import copy
import importlib.util
from pathlib import Path

import aiohttp
from aiohttp import web
import pytest
import pytest_asyncio

spec = importlib.util.spec_from_file_location(
    "stillframe_api", Path(__file__).parents[1] / "custom_components/stillframe/api.py")
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)

STATE = {"api_version": 1, "device": {"id": "stable-id"}, "controls": {"power": "auto"}}


@pytest_asyncio.fixture
async def frame(request):
    password_required = getattr(request, "param", True)
    state = copy.deepcopy(STATE)

    async def handle(request):
        if password_required and request.headers.get("Authorization") != aiohttp.BasicAuth("admin", "test-password").encode():
            return web.Response(status=401)
        if not password_required:
            assert "Authorization" not in request.headers
        if request.method == "POST":
            assert request.headers["X-Stillframe-Client"] == "homeassistant"
            state["controls"].update(await request.json())
        return web.json_response(state)

    app = web.Application()
    app.router.add_get("/api/v1/state", handle)
    app.router.add_post("/api/v1/control", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    async with aiohttp.ClientSession() as session:
        yield api.StillframeClient(session, f"http://127.0.0.1:{port}", "admin", "test-password"), state
    await runner.cleanup()


async def test_read_then_partial_control_preserves_identity(frame):
    client, _ = frame
    assert await client.state() == STATE
    updated = await client.control(power="off")
    assert updated["device"]["id"] == "stable-id"
    assert updated["controls"]["power"] == "off"


async def test_auth_failure_is_distinct(frame):
    client, _ = frame
    client.auth = aiohttp.BasicAuth("admin", "incorrect")
    with pytest.raises(api.StillframeAuthError):
        await client.state()


async def test_unknown_version_and_missing_identity_are_rejected(frame):
    client, state = frame
    state["api_version"] = 2
    with pytest.raises(api.StillframeError, match="version"):
        await client.state()
    state["api_version"] = 1
    state["device"] = {}
    with pytest.raises(api.StillframeError, match="stable"):
        await client.state()


@pytest.mark.parametrize("url", ["file:///etc/passwd", "http://admin:secret@frame:8080",
                                "http://frame/path", "http://frame?password=secret", "http://frame:bad"])
def test_rejects_invalid_urls_and_embedded_credentials(url):
    with pytest.raises(ValueError):
        api.normalize_url(url)


@pytest.mark.parametrize("frame", [False], indirect=True)
async def test_empty_password_reads_and_controls_without_authentication(frame):
    client, _ = frame
    passwordless = api.StillframeClient(client.session, client.url, "admin", "")
    assert passwordless.auth is None
    assert await passwordless.state() == STATE
    updated = await passwordless.control(power="off")
    assert updated["controls"]["power"] == "off"


async def test_empty_password_still_fails_when_frame_requires_it(frame):
    client, _ = frame
    passwordless = api.StillframeClient(client.session, client.url, "admin", "")
    with pytest.raises(api.StillframeAuthError):
        await passwordless.state()
