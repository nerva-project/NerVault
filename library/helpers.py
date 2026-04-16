from utils.models import Event
from utils.factory import cache


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
    return bool(await cache.redis.exists("maintenance"))


async def set_maintenance(enable: bool = False) -> None:
    """
    Enables or disables maintenance mode.

    Args:
        enable (bool): Whether to enable maintenance mode. Default is False.
    """
    if enable:
        await cache.redis.set("maintenance", 1)
    else:
        await cache.redis.delete("maintenance")
