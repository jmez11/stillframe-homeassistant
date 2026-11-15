# Stillframe LAN API v1

This contract is shared by the Home Assistant integration and each Stillframe
implementation. Pi OS and Daydream implement this contract; each platform
should implement these behaviors before advertising discovery.

## Discovery and identity

Advertise `_stillframe._tcp.local.` on the API port with TXT `api_version=1`,
`path=/api/v1/state` and `model=pi-os` (or the appropriate platform).
The instance name should contain the hostname to avoid collisions. No passwords
or account tokens belong in TXT records.

`device.id` is an appliance-generated UUID persisted outside app release files.
It must remain stable through restarts, app updates and Google reconnects. It is
independent of IP address, friendly name and Google registration ID. HA confirms
this identity after authentication, deduplicates by it, and uses it for entities.

## Authentication

When password protection is enabled on the frame, both endpoints require HTTP
Basic authentication with the frame credentials; missing or incorrect credentials
return 401. Frames may offer a local option to disable password protection. When
that option is disabled, HA accepts an empty password and sends no Authorization
header. JSON commands still require
`X-Stillframe-Client: homeassistant`. No cross-origin browser access is allowed.
Existing browser form routes retain session-based CSRF validation.

## GET /api/v1/state

```json
{
  "api_version": 1,
  "device": {"id": "persistent-uuid", "name": "Living room", "model": "Stillframe Pi OS", "version": "0.2.44"},
  "controls": {
    "power": "auto", "active_start": "08:00", "active_end": "22:00",
    "timezone": "America/Los_Angeles", "album_ids": [],
    "album_schedule_enabled": true, "album_periods": []
  },
  "display": {"requested_on": true, "active_album_ids": [], "reported": {}},
  "albums": [{"id": "local", "name": "Local uploads", "downloaded": 3, "total": 3, "percent": 100, "completed": true, "status": "Local"}],
  "cache": {"downloaded": 120, "discovered": 400, "bytes": 1200000, "buffer_percent": 66, "status": "Downloading"}
}
```

Additional cache fields are allowed. Cache statistics are collected asynchronously
at most once per 30 seconds; `cache.updated_at` is the last complete snapshot's
Unix timestamp. Counts and percentages may be null while the first scan runs.
Control responses must not wait for catalog scans or Google requests.
`reported` may contain `requested_on`, `powered` (boolean or null if unconfirmed),
`at` (Unix timestamp), and `active_album_ids`. It is asynchronous renderer telemetry,
not proof of physical monitor power consumption.

Album totals reflect discovered membership. `completed` means feed discovery is
complete, independently of cache percentage. A photo shared by several albums
can contribute to each album's count. Local uploads use the reserved ID `local`.
Album IDs must be stable opaque source IDs rather than names.

## POST /api/v1/control

Send a nonempty JSON object containing only fields to change. Return the complete
updated state. Unknown fields and invalid values return 400 without applying changes.
The server serializes partial updates to preserve unrelated settings.

Supported fields:

| Field | Meaning |
| --- | --- |
| `power` | `on`, `off`, or `auto`; on/off persist until explicitly changed |
| `active_start`, `active_end` | Daily hours, strict `HH:MM`, end exclusive, overnight supported; equal means all day |
| `timezone` | Valid nonempty IANA zone |
| `album_ids` | Unique IDs of already synced albums; empty means all enabled sources |
| `album_schedule_enabled` | Boolean; disable for immediate manual selection |
| `album_periods` | Up to 24 non-overlapping daily `{start,end,album_ids}` objects |
| `display_mode` | `auto` preserves native preferences; otherwise `fullscreen`, `side_by_side`, `mosaic`, `collage`, or `pile` |
| `mode_schedule_enabled` | Boolean; disable for immediate manual mode selection |
| `mode_periods` | Up to 24 non-overlapping daily `{start,end,display_mode}` objects |

Album periods use the frame timezone and take precedence over base `album_ids`
when enabled. Gaps use base selection. Equal period start/end means all day.
Selecting albums must not change Google source authorization, clear caches,
reset viewing history or restrict background synchronization. Restrict playback
before applying the candidate limit and never fall back to unrelated albums.
When membership is unknown (combined Google feed), do not assume membership in
a specifically selected album. An empty selection may play the combined feed.

Display power means display sleep/wake, not shutting down the device. Off must
override setup/pairing prompts. Scheduling and controls must survive HA outages.

Frames supporting mode schedules advertise `capabilities.mode_schedules: true`
and list their supported IDs in `capabilities.display_modes`. The three mode
control fields are an optional, backward-compatible extension to API v1.
`display.display_mode` is the effective policy (`auto` or a fixed mode), while
`display.layout` is the effective base layout and `display.reported.display_mode`
is the renderer's actual active layout.

Mode periods use the frame timezone and take precedence over base `display_mode`
while enabled. Gaps use the base mode. A fixed mode suppresses native random
mode rotation for its duration; `auto` restores native layout/rotation without
overwriting those settings. Mode and album schedules are validated separately,
so their periods may overlap each other.

## Shared daily hours and control ownership

Frames advertise `capabilities.shared_daily_hours: true` and expose the boolean
`controls.daily_hours_enabled`. The same times, enabled state and timezone are
used by native settings and HA. Disabled hours retain saved times. Manual power
on/off overrides the hours until `power: auto` is restored. Older frames omit
the flag; HA shows legacy hours but does not offer an unsupported enable switch.
When writing saved times, modern clients also send the current enabled state;
legacy time-only writes enable daily hours for backward compatibility.

`display.control_sources` describes effective playback, album and display-mode
control in plain language. Advanced schedules are configured in HA and executed
on the frame. Manual album/mode choices pause their schedule; resuming enables
it without replacing saved periods. Gaps use the saved base selection/settings.
Native Android migration adopts effective HA hours only while HA access is
enabled, removes the separate copy and preserves explicit power overrides.
