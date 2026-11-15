"""Resume the saved daily power schedule after an override."""
from homeassistant.components.button import ButtonEntity

from .entity import StillframeEntity


async def async_setup_entry(hass, entry, async_add_entities):
    entities = [ResumeButton(entry.runtime_data, "resume_schedule", "Follow daily hours")]
    for kind, name in (("album", "Resume album schedule"), ("mode", "Resume display mode schedule")):
        if f"{kind}_periods" in entry.runtime_data.data["controls"]:
            entities.append(ResumeAdvanced(entry.runtime_data, kind, name))
    async_add_entities(entities)


class ResumeButton(StillframeEntity, ButtonEntity):
    async def async_press(self):
        await self.coordinator.control(power="auto")


class ResumeAdvanced(StillframeEntity, ButtonEntity):
    def __init__(self, coordinator, kind, name):
        super().__init__(coordinator, "resume_" + kind + "_schedule", name)
        self.kind = kind

    @property
    def available(self):
        return super().available and bool(self.coordinator.data["controls"].get(f"{self.kind}_periods"))

    async def async_press(self):
        await self.coordinator.control(**{f"{self.kind}_schedule_enabled": True})
