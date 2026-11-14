"""Stillframe local integration, shared across Stillframe implementations."""
import voluptuous as vol

from homeassistant.const import CONF_PASSWORD, CONF_URL, CONF_USERNAME
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service import async_extract_config_entry_ids
from homeassistant.exceptions import HomeAssistantError

from .api import StillframeClient
from .const import DOMAIN, PLATFORMS
from .coordinator import StillframeCoordinator

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup_entry(hass, entry):
    client = StillframeClient(async_get_clientsession(hass), entry.data[CONF_URL],
                             entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
    coordinator = StillframeCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    if not hass.services.has_service(DOMAIN, "set_album_periods"):
        async def set_periods(call):
            entries = await async_extract_config_entry_ids(call)
            targets = [e for e in hass.config_entries.async_entries(DOMAIN)
                       if e.entry_id in entries and e.state.value == "loaded"]
            if not targets:
                raise HomeAssistantError("Target at least one loaded Stillframe device or entity")
            for target in targets:
                await target.runtime_data.control(album_periods=call.data["periods"],
                                                  album_schedule_enabled=True)

        hass.services.async_register(DOMAIN, "set_album_periods", set_periods, schema=vol.Schema({
            vol.Optional("entity_id"): cv.entity_ids,
            vol.Optional("device_id"): vol.All(cv.ensure_list, [cv.string]),
            vol.Optional("area_id"): vol.All(cv.ensure_list, [cv.string]),
            vol.Required("periods"): vol.All(cv.ensure_list, [dict]),
        }))
    return True


async def async_unload_entry(hass, entry):
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded and not any(e.entry_id != entry.entry_id and e.state.value == "loaded"
                            for e in hass.config_entries.async_entries(DOMAIN)):
        hass.services.async_remove(DOMAIN, "set_album_periods")
    return unloaded
