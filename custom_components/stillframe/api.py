"""Small asynchronous client for the cross-platform Stillframe LAN API."""
from urllib.parse import urlsplit

import aiohttp


class StillframeError(Exception):
    """Frame communication failed."""


class StillframeAuthError(StillframeError):
    """Frame credentials rejected."""


def normalize_url(value):
    value = value.strip().rstrip("/")
    parsed = urlsplit(value)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Use an http(s) address without embedded credentials")
    if parsed.path or parsed.query or parsed.fragment:
        raise ValueError("Use the frame's base URL without a path")
    # Accessing port also validates its syntax and range.
    parsed.port
    return value


class StillframeClient:
    def __init__(self, session, url, username, password):
        self.session = session
        self.url = normalize_url(url)
        self.auth = aiohttp.BasicAuth(username, password)

    async def request(self, method, path, values=None):
        try:
            async with self.session.request(
                method, self.url + path, auth=self.auth, json=values,
                headers={"X-Stillframe-Client": "homeassistant", "Connection": "close"},
                timeout=aiohttp.ClientTimeout(total=45, sock_connect=5), allow_redirects=False,
            ) as response:
                if response.status == 401:
                    raise StillframeAuthError("Frame authentication failed")
                if response.status == 404:
                    raise StillframeError("Frame needs Stillframe LAN API v1 firmware")
                if response.status != 200:
                    raise StillframeError(f"Frame returned HTTP {response.status}")
                state = await response.json()
                if not isinstance(state, dict) or state.get("api_version") != 1:
                    raise StillframeError("Unsupported Stillframe API version")
                if not state.get("device", {}).get("id"):
                    raise StillframeError("Frame did not supply a stable device ID")
                return state
        except (aiohttp.ClientError, TimeoutError, ValueError) as error:
            raise StillframeError("Unable to communicate with frame") from error

    async def state(self):
        return await self.request("GET", "/api/v1/state")

    async def control(self, **values):
        return await self.request("POST", "/api/v1/control", values)
