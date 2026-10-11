import pytest

from momo_api import CollectionApi, Config, DisbursementApi, MomoApi, SandboxApi

CREDENTIALS = {"subscription_key": "k", "api_user": "u", "api_key": "s"}


class TestGetBaseUrl:
    def test_resolves_the_sandbox_environment_to_the_sandbox_host(self):
        assert MomoApi.get_base_url("sandbox") == MomoApi.SANDBOX_URL

    @pytest.mark.parametrize("environment", [e for e in MomoApi.ENVIRONMENTS if e != "sandbox"])
    def test_resolves_every_production_market_to_the_production_host(self, environment):
        assert MomoApi.get_base_url(environment) == MomoApi.PRODUCTION_URL

    def test_rejects_an_unknown_environment_instead_of_silently_hitting_production(self):
        with pytest.raises(ValueError, match="Unknown environment: 'mtnatlantis'"):
            MomoApi.get_base_url("mtnatlantis")

    def test_lists_sandbox_and_the_eleven_production_markets(self):
        assert len(MomoApi.ENVIRONMENTS) == 12


@pytest.mark.parametrize("factory,product", [
    (MomoApi.collection, CollectionApi),
    (MomoApi.disbursement, DisbursementApi),
])
class TestProductFactories:
    def test_honours_the_requested_production_environment(self, factory, product):
        api = factory({**CREDENTIALS, "environment": MomoApi.ENVIRONMENT_MTN_CONGO})
        assert isinstance(api, product)
        assert api.environment == "mtncongo"
        assert api.base_url == MomoApi.PRODUCTION_URL

    def test_defaults_to_sandbox_when_no_environment_is_given(self, factory, product):
        api = factory(CREDENTIALS)
        assert (api.environment, api.base_url) == ("sandbox", MomoApi.SANDBOX_URL)

    def test_carries_the_callback_url_into_the_config(self, factory, product):
        assert factory({**CREDENTIALS, "callback_url": "https://cb.example"}).config.callback_uri == "https://cb.example"

    def test_defaults_the_callback_url_to_an_empty_string(self, factory, product):
        assert factory(CREDENTIALS).config.callback_uri == ""

    @pytest.mark.parametrize("missing", ["subscription_key", "api_user", "api_key"])
    def test_rejects_a_missing_credential(self, factory, product, missing):
        with pytest.raises(ValueError, match=f"{missing} is required"):
            factory({k: v for k, v in CREDENTIALS.items() if k != missing})

    def test_rejects_an_unknown_environment(self, factory, product):
        with pytest.raises(ValueError, match="Unknown environment"):
            factory({**CREDENTIALS, "environment": "nowhere"})

    def test_accepts_a_config_instance_defaulting_to_sandbox(self, factory, product):
        api = factory(Config.collection("k", "u", "s"))
        assert api.environment == "sandbox"
        assert api.subscription_key == "k"

    def test_accepts_a_config_instance_with_an_explicit_environment(self, factory, product):
        api = factory(Config.collection("k", "u", "s"), MomoApi.ENVIRONMENT_MTN_UGANDA)
        assert api.environment == "mtnuganda"

    def test_rejects_an_unknown_environment_with_a_config_instance(self, factory, product):
        with pytest.raises(ValueError, match="Unknown environment"):
            factory(Config.collection("k", "u", "s"), "nowhere")


class TestCreate:
    def test_rejects_an_unknown_environment(self):
        with pytest.raises(ValueError, match="Unknown environment"):
            MomoApi.create("nowhere")

    def test_builds_products_bound_to_the_instance_environment(self):
        momo = MomoApi.create(MomoApi.ENVIRONMENT_MTN_GHANA)
        config = Config.collection("k", "u", "s")
        assert momo.get_collection(config).environment == "mtnghana"
        assert momo.get_disbursement(config).environment == "mtnghana"


class TestSandbox:
    def test_is_available_on_the_sandbox_environment(self):
        assert isinstance(MomoApi.create("sandbox").sandbox("k"), SandboxApi)

    def test_refuses_to_run_against_a_production_environment(self):
        with pytest.raises(ValueError, match="Environment must be sandbox"):
            MomoApi.create(MomoApi.ENVIRONMENT_MTN_CONGO).sandbox("k")
