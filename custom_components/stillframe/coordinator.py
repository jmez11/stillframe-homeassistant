"""One poll per frame, shared by all entities."""
from datetime import timedelta
import asyncio
import logging

from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import StillframeAuthError, StillframeError


class StillframeCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, client):
        super().__init__(hass, logging.getLogger(__name__), name="Stillframe",
                         config_entry=entry, update_interval=timedelta(seconds=30))
        self.client = client
        self.command_lock = asyncio.Lock()

    async def _async_update_data(self):
        try:
            async with self.command_lock:
                return await self.client.state()
        except StillframeAuthError as error:
            raise ConfigEntryAuthFailed from error
        except StillframeError as error:
            raise UpdateFailed(str(error)) from error

    async def control(self, **values):
        try:
            async with self.command_lock:
                state = await self.client.control(**values)
                self.async_set_updated_data(state)
        except StillframeError as error:
            raise HomeAssistantError(str(error)) from error
