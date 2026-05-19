"""
Built-in (non-serialised) placeholders that are always available at runtime.

These are not stored in AppConfig – they are injected by the runtime into each
group/session scope (e.g. recording_number is incremented per recording).
PlaceholderService merges this list with the user-configured placeholders so
that widgets always show the full set of valid names.
"""

from flow3r.core.placeholder.placeholder_info import PlaceholderInfo

SYSTEM_PLACEHOLDERS: list[PlaceholderInfo] = [
    PlaceholderInfo("group_name",           "Group Name"),
    PlaceholderInfo("recording_number",     "Recording Number"),
    PlaceholderInfo("recording_start_time", "Recording Start Time"),
]

