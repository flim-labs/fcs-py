import re

def sanitize_filename(name: str) -> str:
    """Sanitize filename by replacing invalid characters."""
    name = name.replace(' ', '_')
    name = re.sub(r'[/\\:*?"<>|]', '-', name)
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    return name

def get_channel_name(channel_id: int, custom_names: dict, truncate_len: int = None) -> str:
    """
    Get the display name for a channel.
    Returns "CustomName (Ch1)" if custom name exists, otherwise "Channel 1".
    Custom name can be truncated.
    """
    custom_name = custom_names.get(str(channel_id), None)
    default_part = f"(Ch{channel_id + 1})"
    if custom_name:
        if truncate_len and len(custom_name) > truncate_len:
            custom_name = custom_name[:truncate_len] + "..."
        return f"{custom_name} {default_part}"
    return f"Channel {channel_id + 1}"

def get_channel_short_name(channel_id: int, custom_names: dict) -> str:
    """
    Get the short display name for a channel.
    Returns "CustomName (Ch1)" if custom name exists, otherwise "Ch 1".
    """
    custom_name = custom_names.get(str(channel_id), None)
    default_part = f"(Ch{channel_id + 1})"
    if custom_name:
        return f"{custom_name} {default_part}"
    return f"Ch {channel_id + 1}"

def get_channel_name_parts(channel_id: int, custom_names: dict) -> tuple:
    """
    Get the custom and default parts of a channel name separately.
    """
    custom_name = custom_names.get(str(channel_id), None)
    default_part = f"(Ch{channel_id + 1})"
    if custom_name and custom_name.strip():
        return custom_name, default_part
    return f"Channel {channel_id + 1}", ""

def validate_channel_name(name: str) -> bool:
    """Validate channel name length."""
    return len(name) <= 50

