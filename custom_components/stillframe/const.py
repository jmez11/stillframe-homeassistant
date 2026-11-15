"""Shared integration constants."""
from homeassistant.const import Platform

PHOTO_SOURCE_EXPLANATION = (
    "Albums are checked separately. With Highlights selected, Google also sends a mix of your selections. "
    "Photos not yet matched to an album may be Highlights or album photos. "
    "With Highlights alone, all returned photos are Highlights."
)

DOMAIN = "stillframe"
DISPLAY_MODES = {"auto": "Frame settings", "fullscreen": "Fullscreen", "side_by_side": "Side by side",
                 "mosaic": "Mosaic", "collage": "Collage", "pile": "Photo pile"}
PLATFORMS = [Platform.SWITCH, Platform.SELECT, Platform.TIME, Platform.SENSOR, Platform.BUTTON]
