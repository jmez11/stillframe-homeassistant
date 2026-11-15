"""Cache metrics and per-album cache status without account metadata."""
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.entity import EntityCategory

from .const import PHOTO_SOURCE_EXPLANATION
from .entity import StillframeEntity
from .policy import control_summary, daily_hours_enabled


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = entry.runtime_data
    async_add_entities([CacheSensor(coordinator, key, name, unit) for key, name, unit in (
        ("downloaded", "Cached photos", None), ("discovered", "Discovered photos", None),
        ("buffer_percent", "Playback buffer", "%"), ("bytes", "Photo cache size", "B"),
        ("status", "Sync status", None),
    )] + [AlbumStatus(coordinator)] + [ControlStatus(coordinator, key, name) for key, name in (
        ("playback", "Playback control status"), ("albums", "Album control status"),
        ("display_mode", "Display mode control status"), ("showing", "Photos showing"),
    )])


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


class ControlStatus(StillframeEntity, SensorEntity):
    def __init__(self, coordinator, key, name):
        super().__init__(coordinator, "control_" + key, name)
        self.key = key

    @property
    def native_value(self):
        return control_summary(self.coordinator.data)[self.key]

    @property
    def extra_state_attributes(self):
        state = self.coordinator.data
        p = state["controls"]
        if self.key == "showing":
            return {"requested_on": state["display"]["requested_on"],
                    "reported_at": state["display"].get("reported", {}).get("at"),
                    "meaning": "Photo playback, not confirmation of TV panel power"}
        if self.key == "playback":
            return {"daily_hours_enabled": daily_hours_enabled(state), "saved_start": p["active_start"],
                    "saved_end": p["active_end"], "timezone": p["timezone"],
                    "managed_in": "Shared frame setting; editable in the app or Home Assistant",
                    "override": p["power"] != "auto", "resume": "Resume daily hours"}
        return {"configured_in": "Home Assistant", "runs_on": "Frame, including while Home Assistant is offline",
                "resume": "Resume album schedule" if self.key == "albums" else "Resume display mode schedule",
                "google_sources_managed_in": "Google Photos"}
