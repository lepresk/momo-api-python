import httpx
import pytest

from momo_api import AirtelApi, AirtelConfig, CollectionApi, Config, MomoApi

TOKEN = {"access_token": "t", "token_type": "access_token", "expires_in": 3600}
CREDENTIALS = {"subscription_key": "k", "api_user": "u", "api_key": "s"}


def recording_client():
    """An httpx.Client whose transport records every request instead of sending it."""
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path.endswith("/token/") or request.url.path.endswith("/oauth2/token"):
            return httpx.Response(200, json=TOKEN)
        return httpx.Response(200, json={"availableBalance": "10", "currency": "XAF",
                                         "data": {"balance": "10", "currency": "XAF"}})

    return httpx.Client(transport=httpx.MockTransport(handler)), seen


def test_is_used_by_a_product_built_directly():
    client, seen = recording_client()
    CollectionApi(Config.collection("k", "u", "s"), MomoApi.SANDBOX_URL, "sandbox", client).get_balance()
    assert len(seen) == 2


@pytest.mark.parametrize("factory", [MomoApi.collection, MomoApi.disbursement])
def test_is_accepted_by_the_static_factories(factory):
    client, seen = recording_client()
    factory(CREDENTIALS, http_client=client).get_balance()
    assert len(seen) == 2


def test_is_accepted_by_create_and_inherited_by_its_products():
    client, seen = recording_client()
    momo = MomoApi.create("sandbox", client)
    momo.get_collection(Config.collection("k", "u", "s")).get_balance()
    momo.get_disbursement(Config.disbursement("k", "u", "s")).get_balance()
    assert len(seen) == 4


def test_is_inherited_by_the_sandbox_product():
    client, seen = recording_client()
    MomoApi.create("sandbox", client).sandbox("k").get_api_user("user-1")
    assert seen[0].url.path == "/v1_0/apiuser/user-1"


def test_does_not_leak_between_clients():
    first, first_seen = recording_client()
    second, second_seen = recording_client()
    MomoApi.collection(CREDENTIALS, http_client=first).get_balance()
    MomoApi.collection(CREDENTIALS, http_client=second).get_balance()
    assert len(first_seen) == 2 and len(second_seen) == 2


def test_falls_back_to_a_one_off_client_when_none_is_supplied(httpx_mock):
    httpx_mock.add_response(method="POST", url=f"{MomoApi.SANDBOX_URL}/collection/token/", json=TOKEN)
    httpx_mock.add_response(url=f"{MomoApi.SANDBOX_URL}/collection/v1_0/account/balance",
                            json={"availableBalance": "10", "currency": "EUR"})
    assert MomoApi.collection(CREDENTIALS).get_balance().available_balance == "10"


def test_is_accepted_by_airtel_create_and_the_shorthand_factories():
    client, seen = recording_client()
    AirtelApi.create("staging", client).get_collection(AirtelConfig.collection("c", "s")).get_balance()
    AirtelApi.disbursement("staging", AirtelConfig.disbursement("c", "s", "pin"), client).get_balance()
    assert len(seen) == 4
