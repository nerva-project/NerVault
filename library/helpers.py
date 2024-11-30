from __future__ import annotations

from utils.models import Event, Config


async def capture_event(username: str, category: str) -> None:
    """
    Captures an event for a given username and category.
    """
    event: Event = Event(user=username, category=category)
    await event.save()


async def on_maintenance() -> bool:
    """
    Checks if the system is in maintenance mode.

    Returns:
        bool: True if in maintenance mode, False otherwise.
    """
    try:
        rec: Config = Config("maintenance")
        await rec.load()
        return bool(rec.value)

    except AttributeError:
        return False


async def set_maintenance(enable: bool = False) -> None:
    """
    Enables or disables maintenance mode.

    Args:
        enable (bool): Whether to enable maintenance mode. Default is False.
    """
    rec: Config = Config("maintenance", enable)
    await rec.save()
