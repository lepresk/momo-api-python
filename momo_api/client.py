from .models.config import Config
from .products.collection import CollectionApi
from .products.disbursement import DisbursementApi
from .products.sandbox import SandboxApi


class MomoApi:
    """Entry point for the MTN MoMo API client."""

    # Supported target environments
    ENVIRONMENT_MTN_CONGO = "mtncongo"
    ENVIRONMENT_MTN_UGANDA = "mtnuganda"
    ENVIRONMENT_MTN_GHANA = "mtnghana"
    ENVIRONMENT_IVORY_COAST = "mtnivorycoast"
    ENVIRONMENT_ZAMBIA = "mtnzambia"
    ENVIRONMENT_CAMEROON = "mtncameroon"
    ENVIRONMENT_BENIN = "mtnbenin"
    ENVIRONMENT_SWAZILAND = "mtnswaziland"
    ENVIRONMENT_GUINEACONAKRY = "mtnguineaconakry"
    ENVIRONMENT_SOUTHAFRICA = "mtnsouthafrica"
    ENVIRONMENT_LIBERIA = "mtnliberia"
    ENVIRONMENT_SANDBOX = "sandbox"

    SANDBOX_URL = "https://sandbox.momodeveloper.mtn.com"
    PRODUCTION_URL = "https://proxy.momoapi.mtn.com"

    def __init__(self, environment: str):
        self._environment = environment
        self._base_url = (
            self.SANDBOX_URL
            if environment == self.ENVIRONMENT_SANDBOX
            else self.PRODUCTION_URL
        )

    # ------------------------------------------------------------------
    # Class-level factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def create(cls, environment: str) -> "MomoApi":
        """Create a MomoApi instance for the given environment."""
        return cls(environment)

    @classmethod
    def _build_config(cls, config: dict) -> Config:
        return Config(
            subscription_key=config.get("subscription_key", ""),
            api_user=config.get("api_user", ""),
            api_key=config.get("api_key", ""),
            callback_uri=config.get("callback_url", ""),
        )

    @classmethod
    def _base_url_for_env(cls, environment: str) -> str:
        if environment == cls.ENVIRONMENT_SANDBOX:
            return cls.SANDBOX_URL
        return cls.PRODUCTION_URL

    @classmethod
    def collection(cls, config: dict) -> CollectionApi:
        """Create a CollectionApi instance from a config dict."""
        environment = config.get("environment", cls.ENVIRONMENT_SANDBOX)
        cfg = cls._build_config(config)
        base_url = cls._base_url_for_env(environment)
        return CollectionApi(cfg, base_url, environment)

    @classmethod
    def disbursement(cls, config: dict) -> DisbursementApi:
        """Create a DisbursementApi instance from a config dict."""
        environment = config.get("environment", cls.ENVIRONMENT_SANDBOX)
        cfg = cls._build_config(config)
        base_url = cls._base_url_for_env(environment)
        return DisbursementApi(cfg, base_url, environment)

    # ------------------------------------------------------------------
    # Instance-level helpers
    # ------------------------------------------------------------------

    def sandbox(self, subscription_key: str) -> SandboxApi:
        """Create a SandboxApi instance using this client's base URL."""
        return SandboxApi(subscription_key, self._base_url)
