"""Exercise ownership and actual-playback status without Home Assistant stubs."""
from datetime import datetime, timezone
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("stillframe_policy", Path(__file__).parents[1] / "custom_components/stillframe/policy.py")
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


def state():
    return {"controls": {"power": "auto", "daily_hours_enabled": False, "active_start": "08:00", "active_end": "22:00",
            "timezone": "America/Los_Angeles", "album_ids": [], "album_periods": [], "album_schedule_enabled": True,
            "display_mode": "auto", "mode_periods": [], "mode_schedule_enabled": True}, "display": {"reported": {}}}


def test_daily_hours_and_manual_override_are_distinct():
    s = state()
    assert policy.control_summary(s)["playback"] == "Any time - daily hours off"
    s["controls"]["daily_hours_enabled"] = True
    assert policy.control_summary(s)["playback"] == "Following daily hours"
    s["controls"]["power"] = "off"
    assert policy.control_summary(s)["playback"] == "Keep stopped - manual override"
    del s["controls"]["daily_hours_enabled"]
    assert policy.daily_hours_enabled(s)
    s["controls"]["active_end"] = "08:00"
    assert not policy.daily_hours_enabled(s)


def test_advanced_control_has_independent_schedule_pause_and_fallback():
    s = state()
    s["controls"]["mode_periods"] = [{"start": "22:00", "end": "06:00", "display_mode": "pile"}]
    night = datetime(2026, 1, 2, 7, tzinfo=timezone.utc)
    assert policy.control_summary(s, night)["display_mode"] == "Following Home Assistant schedule"
    assert policy.control_summary(s, night)["albums"] == "All selected sources"
    end = datetime(2026, 1, 2, 14, tzinfo=timezone.utc)
    assert policy.control_summary(s, end)["display_mode"] == "Frame settings"
    s["controls"]["mode_schedule_enabled"] = False
    assert policy.control_summary(s, night)["display_mode"] == "Manual selection; HA schedule paused"


def test_requested_on_is_not_proof_of_photos_showing_and_stale_is_unknown():
    s = state()
    now = datetime(2026, 1, 2, 7, tzinfo=timezone.utc)
    s["display"]["requested_on"] = True
    assert policy.control_summary(s, now)["showing"] == "Unknown"
    s["display"]["reported"] = {"powered": False, "at": now.timestamp()}
    assert policy.control_summary(s, now)["showing"] == "Not showing photos"
    s["display"]["reported"]["powered"] = True
    assert policy.control_summary(s, now)["showing"] == "Showing photos"
    s["display"]["reported"]["at"] -= 91
    assert policy.control_summary(s, now)["showing"] == "Unknown"


def test_daily_hours_status_explains_override_even_when_the_toggle_is_on():
    s = state()
    for enabled in (False, True):
        s["controls"]["daily_hours_enabled"] = enabled
        for power, choice in (("on", "Keep playing"), ("off", "Keep stopped")):
            s["controls"]["power"] = power
            s["display"]["control_sources"] = {"playback": "Manual override: keep off"}
            summary = policy.control_summary(s)
            assert summary["playback"] == choice + " - manual override"
            assert summary["daily_hours"] == (f"Paused - {choice} is active" if enabled else f"Off - {choice} still applies")
        s["controls"]["power"] = "auto"
        assert policy.control_summary(s)["daily_hours"] == ("Following saved times" if enabled else "Off - photos may play at any time")
