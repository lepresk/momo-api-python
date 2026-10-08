"""Edge cases found in review: inputs that crashed, or silently did the wrong thing."""
import httpx
import pytest
from pytest_httpx import HTTPXMock

from momo_api import (
    AirtelApi,
    AirtelConfig,
    ApiToken,
    Config,
    InternalServerErrorException,
    MomoApi,
    MomoException,
    ResourceNotFoundException,
    TokenCache,
    assert_uuid,
)
from momo_api.support import http

CREDENTIALS = {"subscription_key": "k", "api_user": "u", "api_key": "s"}
AIRTEL = AirtelApi.STAGING_URL
UUID = "3f1c9a2e-8b4d-4c6f-9a1e-2d7b5c8e0f13"


class TestEnvironmentResolution:
    def test_a_dict_without_environment_takes_the_environment_argument(self):
        api = MomoApi.collection(CREDENTIALS, MomoApi.ENVIRONMENT_MTN_CONGO)
        assert (api.environment, api.base_url) == ("mtncongo", MomoApi.PRODUCTION_URL)

    def test_the_dict_environment_wins_over_the_argument(self):
        api = MomoApi.disbursement({**CREDENTIALS, "environment": "mtnghana"}, MomoApi.ENVIRONMENT_MTN_CONGO)
        assert api.environment == "mtnghana"

    def test_an_empty_environment_is_rejected_rather_than_meaning_sandbox(self):
        with pytest.raises(ValueError, match="Unknown environment: ''"):
            MomoApi.collection({**CREDENTIALS, "environment": ""})


class TestUuidEdges:
    @pytest.mark.parametrize("value", [UUID + "\n", UUID + " ", "\n" + UUID, UUID + "\r\n"])
    def test_rejects_surrounding_whitespace(self, value):
        with pytest.raises(ValueError):
            assert_uuid(value, "reference_id")

    def test_a_trailing_newline_never_reaches_airtel(self, httpx_mock: HTTPXMock):
        api = AirtelApi.collection("staging", AirtelConfig.collection("c", "s"))
        with pytest.raises(ValueError):
            api.request_to_pay("100", "068511358", "R", UUID + "\n")
        assert httpx_mock.get_requests() == []


class TestDefaultTimeout:
    def test_the_default_client_waits_longer_than_httpx_five_seconds(self, monkeypatch):
        seen = {}

        class Recorder(httpx.Client):
            def __init__(self, **kwargs):
                seen.update(kwargs)
                super().__init__(transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})))

        monkeypatch.setattr(http.httpx, "Client", Recorder)
        http.send(None, "GET", "https://example.test/")
        assert seen["timeout"] == http.DEFAULT_TIMEOUT == 30.0


class TestTokens:
    @pytest.mark.parametrize("raw,expected", [(3600, 3600), ("3599.0", 3599), (None, 0), ("soon", 0)])
    def test_parses_expires_in_leniently(self, raw, expected):
        assert ApiToken.from_dict({"access_token": "t", "expires_in": raw}).expires_in == expected

    def test_never_caches_an_empty_token(self):
        cache = TokenCache()
        cache.set("", 3600)
        assert cache.get() is None

    def test_airtel_raises_when_no_access_token_is_returned(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(method="POST", url=f"{AIRTEL}/auth/oauth2/token", json={"access_token": None})
        api = AirtelApi.collection("staging", AirtelConfig.collection("c", "s"))
        with pytest.raises(MomoException, match="no access token"):
            api.get_access_token()


def airtel_with(httpx_mock: HTTPXMock, url: str, body) -> None:
    httpx_mock.add_response(method="POST", url=f"{AIRTEL}/auth/oauth2/token", json={"access_token": "t", "expires_in": 3600})
    httpx_mock.add_response(url=f"{AIRTEL}{url}", json=body)


class TestOddAirtelBodies:
    @pytest.mark.parametrize("body", [[], [1], {"data": "x"}, {"data": [1]}, {"data": {"transaction": "x"}}])
    def test_a_malformed_status_body_is_not_found_rather_than_a_crash(self, httpx_mock, body):
        airtel_with(httpx_mock, "/standard/v1/payments/abc", body)
        with pytest.raises(ResourceNotFoundException):
            AirtelApi.collection("staging", AirtelConfig.collection("c", "s")).get_payment_status("abc")

    @pytest.mark.parametrize("body", [{"data": {"balance": None, "currency": None}}, {"data": "x"}, []])
    def test_a_null_or_malformed_balance_reads_as_zero(self, httpx_mock, body):
        airtel_with(httpx_mock, "/standard/v1/users/balance", body)
        balance = AirtelApi.collection("staging", AirtelConfig.collection("c", "s")).get_balance()
        assert (balance.available_balance, balance.currency) == ("0", "")

    def test_a_fractional_refusal_code_maps_like_an_integer(self, httpx_mock):
        httpx_mock.add_response(method="POST", url=f"{AIRTEL}/auth/oauth2/token", json={"access_token": "t"})
        httpx_mock.add_response(method="POST", url=f"{AIRTEL}/merchant/v1/payments/",
                                json={"status": {"success": False, "code": "500.0", "message": "Down"}})
        with pytest.raises(InternalServerErrorException):
            AirtelApi.collection("staging", AirtelConfig.collection("c", "s")).request_to_pay("1", "068511358", "R")

    def test_a_status_lookup_refused_in_the_envelope_raises(self, httpx_mock):
        airtel_with(httpx_mock, "/standard/v1/users/balance",
                    {"status": {"success": False, "code": "401", "message": "Unauthorized"}})
        with pytest.raises(MomoException, match="Unauthorized"):
            AirtelApi.collection("staging", AirtelConfig.collection("c", "s")).get_balance()


class TestOddMtnBodies:
    @pytest.mark.parametrize("body,expected", [({"result": True}, True), ({"result": "false"}, False),
                                               ({"result": "true"}, False), ({}, False), ([True], False)])
    def test_check_account_holder_is_true_only_for_a_true_result(self, httpx_mock, body, expected):
        httpx_mock.add_response(method="POST", url=f"{MomoApi.SANDBOX_URL}/collection/token/", json={"access_token": "t", "expires_in": 3600})
        httpx_mock.add_response(url=f"{MomoApi.SANDBOX_URL}/collection/v1_0/accountholder/msisdn/1/active", json=body)
        assert MomoApi.collection(CREDENTIALS).check_account_holder("1") is expected

    def test_a_non_object_status_body_parses_as_an_empty_transaction(self, httpx_mock):
        httpx_mock.add_response(method="POST", url=f"{MomoApi.SANDBOX_URL}/collection/token/", json={"access_token": "t", "expires_in": 3600})
        httpx_mock.add_response(url=f"{MomoApi.SANDBOX_URL}/collection/v1_0/requesttopay/x", json=[])
        transaction = MomoApi.collection(CREDENTIALS).get_payment_status("x")
        assert transaction.status == "" and not transaction.is_successful()
