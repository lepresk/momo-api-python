from typing import Any, NoReturn, Optional

import httpx

#: Timeout of the default client. httpx's own default (5 s) is short for a
#: payment write, and a timeout leaves the outcome unknown: query the status
#: with your reference id before retrying.
DEFAULT_TIMEOUT = 30.0

from ..exceptions import create_exception


def send(client: Optional[httpx.Client], method: str, url: str, **kwargs: Any) -> httpx.Response:
    """Send through the caller's client when one was injected, so its timeouts,
    retries, proxies and connection pool apply; otherwise use a one-off client."""
    if client is not None:
        return client.request(method, url, **kwargs)
    with httpx.Client(timeout=DEFAULT_TIMEOUT) as one_off:
        return one_off.request(method, url, **kwargs)


def fail(response: httpx.Response) -> NoReturn:
    raise create_exception(response.status_code, response.text or None)


def assert_status(response: httpx.Response, expected: int) -> None:
    """Require an exact status code. The MTN write endpoints answer ``202 Accepted``
    with an empty body; any other status, including another 2xx, is a failure."""
    if response.status_code != expected:
        fail(response)


def read_json(response: httpx.Response) -> Any:
    """Read a JSON body, raising the matching ``MomoException`` on failure."""
    if not response.is_success:
        fail(response)
    return response.json()


def read_json_allow_empty(response: httpx.Response) -> Any:
    """Like ``read_json``, but tolerates the empty bodies the sandbox returns."""
    if not response.is_success:
        fail(response)
    return response.json() if response.content else {}
