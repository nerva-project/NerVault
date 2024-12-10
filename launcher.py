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


loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Run the asynchronous create_app function and retrieve the app instance
app: Quart = loop.run_until_complete(asyncio.gather(create_app()))[0]


def main() -> None:
    """
    Main function to run the app
    """
    app.run(
        host="0.0.0.0", port=17569, loop=loop
    )  # , certfile="cert.pem", keyfile="key.pem")


if __name__ == "__main__":
    main()
