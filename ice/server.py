import sys

import httpx
import uvicorn

from ice.routes.app import is_server_running
from ice.settings import server_url
from ice.settings import settings


def stop():
    if not is_server_running():
        print(
            f"Server at {server_url()} is not running, maybe set OUGHT_ICE_HOST/PORT?"
        )
        sys.exit(0)

    url = server_url() + "/stop"
    print(f"Posting to {url}...")
    try:
        httpx.post(url)
    except httpx.RemoteProtocolError:
        pass  # expected as the server dies

    if is_server_running():
        print(f"Weird, the server is still running!")
        sys.exit(1)
    else:
        print(f"Server stopped!")


def start():
    params_by_name = {p.name: p for p in uvicorn.main.params}
    params_by_name["app"].default = "ice.routes.app:app"
    params_by_name["host"].default = settings.OUGHT_ICE_HOST
    params_by_name["port"].default = settings.OUGHT_ICE_PORT

    uvicorn.main()


def main():
    if sys.argv[1:2] == ["stop"]:
        if sys.argv[2:]:
            print(
                "The stop command takes no arguments, but you can set OUGHT_ICE_HOST/PORT environment variables."
            )
            sys.exit(1)
        stop()
        sys.exit(0)

    if sys.argv[1:2] == ["start"]:
        del sys.argv[1]  # remove redundant command

    start()


if __name__ == "__main__":
    main()
