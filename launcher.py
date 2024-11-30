from __future__ import annotations

from typing import TYPE_CHECKING

import asyncio

from utils.factory import create_app

if TYPE_CHECKING:
    from quart import Quart

try:
    # noinspection PyUnresolvedReferences
    import uvloop

except ImportError:
    pass

else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def main() -> Quart:
    """
    Creates and returns the Quart application instance.

    Returns:
        Quart: The initialized Quart app instance.
    """
    _app: Quart = await create_app()
    return _app


if __name__ == "__main__":
    loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Run the asynchronous main function and retrieve the app instance
    app: Quart = loop.run_until_complete(asyncio.gather(main()))[0]
    app.run(host="0.0.0.0", port=13560, loop=loop)
