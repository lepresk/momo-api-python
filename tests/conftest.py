import json
import os
import pytest

from momo_api import MomoApi
from momo_api.models.config import Config
from momo_api.products.collection import CollectionApi
from momo_api.products.disbursement import DisbursementApi
from momo_api.products.sandbox import SandboxApi

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

SANDBOX_BASE_URL = "https://sandbox.momodeveloper.mtn.com"
ENVIRONMENT = MomoApi.ENVIRONMENT_SANDBOX

SUBSCRIPTION_KEY = "test-subscription-key"
API_USER = "test-api-user-uuid"
API_KEY = "test-api-key-secret"
CALLBACK_URL = "https://callback.example.com/notify"


def load_fixture(name: str) -> dict:
    path = os.path.join(FIXTURES_DIR, name)
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def collection_config() -> dict:
    return {
        "environment": ENVIRONMENT,
        "subscription_key": SUBSCRIPTION_KEY,
        "api_user": API_USER,
        "api_key": API_KEY,
        "callback_url": CALLBACK_URL,
    }


@pytest.fixture
def collection_api(collection_config) -> CollectionApi:
    return MomoApi.collection(collection_config)


@pytest.fixture
def disbursement_config() -> dict:
    return {
        "environment": ENVIRONMENT,
        "subscription_key": SUBSCRIPTION_KEY,
        "api_user": API_USER,
        "api_key": API_KEY,
        "callback_url": CALLBACK_URL,
    }


@pytest.fixture
def disbursement_api(disbursement_config) -> DisbursementApi:
    return MomoApi.disbursement(disbursement_config)


@pytest.fixture
def sandbox_api() -> SandboxApi:
    momo = MomoApi.create(ENVIRONMENT)
    return momo.sandbox(SUBSCRIPTION_KEY)


@pytest.fixture
def token_response() -> dict:
    return load_fixture("token.json")


@pytest.fixture
def account_balance_response() -> dict:
    return load_fixture("account_balance.json")
