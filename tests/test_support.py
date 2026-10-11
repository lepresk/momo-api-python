import base64

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from momo_api import (
    AIRTEL_COUNTRY_CODES,
    AirtelTransaction,
    Config,
    assert_uuid,
    clean_phone_number,
    encrypt_airtel_pin,
    generate_uuid,
)


class TestCleanPhoneNumber:
    def test_strips_the_congo_brazzaville_country_code(self):
        assert clean_phone_number("242068511358") == "068511358"

    def test_strips_formatting_before_looking_for_the_country_code(self):
        assert clean_phone_number("+242 06 851 13 58") == "068511358"

    def test_leaves_a_local_number_untouched(self):
        assert clean_phone_number("068511358") == "068511358"

    def test_accepts_a_number(self):
        assert clean_phone_number(242068511358) == "068511358"

    def test_strips_only_the_first_matching_country_code(self):
        assert clean_phone_number("242242123456") == "242123456"

    @pytest.mark.parametrize("code", AIRTEL_COUNTRY_CODES)
    def test_handles_the_markets_it_claims_to_cover(self, code):
        assert clean_phone_number(f"{code}712345678") == "712345678"


class TestUuid:
    def test_generates_a_v4_uuid(self):
        value = generate_uuid()
        assert len(value) == 36 and value[14] == "4"

    @pytest.mark.parametrize("value", [
        "3f1c9a2e-8b4d-4c6f-9a1e-2d7b5c8e0f13",
        "886313e1-3b8a-5372-9b90-0c9aee199e5d",  # v5
        "3F1C9A2E-8B4D-4C6F-9A1E-2D7B5C8E0F13",
    ])
    def test_accepts_any_uuid(self, value):
        assert_uuid(value, "reference_id")

    @pytest.mark.parametrize("value", ["order-1", "", "3f1c9a2e8b4d4c6f9a1e2d7b5c8e0f13", "3f1c9a2e-8b4d-4c6f-9a1e-2d7b5c8e0f1"])
    def test_rejects_anything_else(self, value):
        with pytest.raises(ValueError, match="reference_id must be a UUID"):
            assert_uuid(value, "reference_id")


class TestAirtelTransaction:
    @pytest.mark.parametrize("status,pending,successful,failed", [
        ("TI", True, False, False),
        ("TIP", True, False, False),
        ("TS", False, True, False),
        ("TF", False, False, True),
        ("XYZ", False, False, False),
    ])
    def test_status_codes(self, status, pending, successful, failed):
        transaction = AirtelTransaction.parse({"id": "1", "status": status})
        assert (transaction.is_pending(), transaction.is_successful(), transaction.is_failed()) == (
            pending, successful, failed,
        )

    def test_exposes_reference_id_the_field_the_api_actually_returns(self):
        transaction = AirtelTransaction.parse({
            "id": "x", "status": "TS", "reference_id": "REF-1", "airtel_money_id": "AM-1", "message": "ok",
        })
        assert (transaction.reference_id, transaction.airtel_money_id, transaction.message) == ("REF-1", "AM-1", "ok")

    def test_returns_none_for_absent_optional_fields(self):
        transaction = AirtelTransaction.parse({})
        assert (transaction.id, transaction.status) == ("", "")
        assert transaction.reference_id is None and transaction.airtel_money_id is None


class TestConfig:
    def test_defaults_the_callback_uri_to_an_empty_string(self):
        assert Config.collection("k", "u", "s").callback_uri == ""

    def test_builds_the_same_config_from_either_product_factory(self):
        assert Config.collection("k", "u", "s", "cb") == Config.disbursement("k", "u", "s", "cb")

    def test_leaves_sandbox_credentials_blank_apart_from_the_subscription_key(self):
        assert Config.sandbox("k") == Config("k", "", "", "")

    def test_derives_a_new_config_with_a_different_callback_uri(self):
        original = Config.collection("k", "u", "s", "https://a.example")
        derived = original.with_callback_uri("https://b.example")
        assert derived.callback_uri == "https://b.example"
        assert original.callback_uri == "https://a.example"
        assert derived.api_key == "s"


@pytest.fixture(scope="module")
def keys():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    return private_key, pem


class TestEncryptAirtelPin:
    @staticmethod
    def decrypt(private_key, encrypted: str) -> str:
        return private_key.decrypt(base64.b64decode(encrypted), padding.PKCS1v15()).decode()

    def test_accepts_every_shape_airtel_hands_out(self, keys):
        private_key, pem = keys
        body = "".join(line for line in pem.splitlines() if "PUBLIC KEY" not in line)
        shapes = [
            pem,
            base64.b64encode(pem.encode()).decode(),
            body,  # the bare base64 DER body, as Airtel's portal shows it
            base64.b64encode(body.encode()).decode(),
        ]
        for shape in shapes:
            assert self.decrypt(private_key, encrypt_airtel_pin("1234", shape)) == "1234"

    def test_produces_one_rsa_block_with_random_padding(self, keys):
        _, pem = keys
        first, second = encrypt_airtel_pin("1234", pem), encrypt_airtel_pin("1234", pem)
        assert len(base64.b64decode(first)) == 256
        assert first != second

    @pytest.mark.parametrize("key", ["", "   "])
    def test_rejects_an_empty_key(self, key):
        with pytest.raises(ValueError, match="public key is required"):
            encrypt_airtel_pin("1234", key)

    def test_reports_what_failed_when_the_key_is_unusable(self):
        with pytest.raises(ValueError, match="PIN encryption failed"):
            encrypt_airtel_pin("1234", "not-a-key")
