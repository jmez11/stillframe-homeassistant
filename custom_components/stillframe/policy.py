"""Plain-language control ownership, including compatibility with older frames."""
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def daily_hours_enabled(state):
    p = state["controls"]
    return p.get("daily_hours_enabled", p.get("active_start") != p.get("active_end"))


def control_summary(state, now=None):
    p = state["controls"]
    power = p["power"]
    result = {"playback": f"Manual override: keep {power}" if power != "auto" else
              "Following daily hours" if daily_hours_enabled(state) else "Daily hours disabled"}
    current = now or datetime.now().astimezone()
    zone = p.get("timezone")
    try:
        if zone:
            current = current.astimezone(ZoneInfo(zone))
    except ZoneInfoNotFoundError:
        pass
    minute = current.strftime("%H:%M")
    for field, key, fallback in (("album", "albums", "All selected sources"),
                                  ("mode", "display_mode", "Frame settings")):
        periods = p.get(f"{field}_periods", [])
        enabled = p.get(f"{field}_schedule_enabled", False)
        active = any(row["start"] == row["end"] or
                     (row["start"] <= minute < row["end"] if row["start"] < row["end"]
                      else minute >= row["start"] or minute < row["end"]) for row in periods)
        selected = bool(p.get("album_ids")) if field == "album" else p.get("display_mode", "auto") != "auto"
        result[key] = ("Following Home Assistant schedule" if enabled and active else
                       "Manual selection; HA schedule paused" if periods and not enabled else
                       "Home Assistant selection" if selected else fallback)
    result.update(state.get("display", {}).get("control_sources", {}))
    reported = state.get("display", {}).get("reported", {})
    stamp = reported.get("at")
    recent = isinstance(stamp, (float, int)) and -10 <= current.timestamp() - stamp <= 90
    actual = reported.get("powered") if recent else None
    result["showing"] = "Showing photos" if actual is True else "Not showing photos" if actual is False else "Unknown"
    return result
