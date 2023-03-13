import os
import subprocess
import sys
import time

import httpx
from structlog import get_logger

from ice.settings import server_url
from ice.settings import settings

log = get_logger()


def is_server_running():
    from ice.routes.app import PING_RESPONSE

    try:
        response = httpx.get(server_url() + "/ping")
        return response.text == PING_RESPONSE
    except httpx.HTTPError:
        return False


def wait_until_server_running():
    start_time = time.time()
    while not is_server_running():
        if time.time() - start_time > 10:
            raise TimeoutError("Server didn't start within 10 seconds")
        time.sleep(0.1)


def ensure_server_running():
    if is_server_running():
        return

    log.info("Starting server, set OUGHT_ICE_AUTO_SERVER=0 to disable.")
    subprocess.Popen(
        [sys.executable, "-m", "ice.server", "start"],
        env=os.environ,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    wait_until_server_running()
    log.info("Server started! Run `python -m ice.server stop` to stop it.")


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
        print("Weird, the server is still running!")
        sys.exit(1)
    else:
        print("Server stopped!")


def start():
    import uvicorn

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
