"""Cache metrics and per-album cache status without account metadata."""
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.entity import EntityCategory

from .const import PHOTO_SOURCE_EXPLANATION
from .entity import StillframeEntity


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    async_add_entities([CacheSensor(coordinator, key, name, unit) for key, name, unit in (
        ("downloaded", "Cached photos", None), ("discovered", "Discovered photos", None),
        ("buffer_percent", "Playback buffer", "%"), ("bytes", "Photo cache size", "B"),
        ("status", "Sync status", None),
    )] + [AlbumStatus(coordinator)])


class CacheSensor(StillframeEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, key, name, unit):
        super().__init__(coordinator, key, name)
        self.key = key
        self._attr_native_unit_of_measurement = unit
        if key != "status":
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        value = self.coordinator.data["cache"].get(self.key)
        return value[:255] if isinstance(value, str) else value

    @property
    def extra_state_attributes(self):
        return {"photo_sources": PHOTO_SOURCE_EXPLANATION} if self.key == "status" else None


class AlbumStatus(StillframeEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator):
        super().__init__(coordinator, "album_cache", "Album cache")

    @property
    def native_value(self):
        return len(self.coordinator.data["albums"])

    @property
    def extra_state_attributes(self):
        return {"photo_sources": PHOTO_SOURCE_EXPLANATION,
                "albums": self.coordinator.data["albums"],
                "periods": self.coordinator.data["controls"]["album_periods"],
                "mode_periods": self.coordinator.data["controls"].get("mode_periods", []),
                "timezone": self.coordinator.data["controls"]["timezone"],
                "cache_updated_at": self.coordinator.data["cache"].get("updated_at"),
                "display_reported": self.coordinator.data["display"].get("reported", {})}
