"""Entities grouped under the physical frame's stable identity."""
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class StillframeEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, key, name):
        super().__init__(coordinator)
        device = coordinator.data["device"]
        self._attr_unique_id = f"{device['id']}_{key}"
        self._attr_name = name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device["id"])}, name=device["name"],
            manufacturer="Stillframe", model=device["model"], sw_version=device["version"],
            configuration_url=coordinator.client.url,
        )
