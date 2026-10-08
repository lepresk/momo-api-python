from typing import Any, Dict, Optional, Tuple, Union

import httpx

from .models.config import Config
from .products.collection import CollectionApi
from .products.disbursement import DisbursementApi
from .products.sandbox import SandboxApi

ConfigSource = Union[Dict[str, Any], Config]


class MomoApi:
    """Entry point for the MTN MoMo API client."""

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

    #: Every environment the client accepts: sandbox plus the 11 production markets
    ENVIRONMENTS: Tuple[str, ...] = (
        ENVIRONMENT_SANDBOX,
        ENVIRONMENT_MTN_CONGO,
        ENVIRONMENT_MTN_UGANDA,
        ENVIRONMENT_MTN_GHANA,
        ENVIRONMENT_IVORY_COAST,
        ENVIRONMENT_ZAMBIA,
        ENVIRONMENT_CAMEROON,
        ENVIRONMENT_BENIN,
        ENVIRONMENT_SWAZILAND,
        ENVIRONMENT_GUINEACONAKRY,
        ENVIRONMENT_SOUTHAFRICA,
        ENVIRONMENT_LIBERIA,
    )

    SANDBOX_URL = "https://sandbox.momodeveloper.mtn.com"
    PRODUCTION_URL = "https://proxy.momoapi.mtn.com"

    def __init__(self, environment: str, http_client: Optional[httpx.Client] = None) -> None:
        self._environment = environment
        self._base_url = self.get_base_url(environment)
        self._http_client = http_client

    @classmethod
    def get_base_url(cls, environment: str) -> str:
        """Resolve the API host for an environment.

        :raises ValueError: when the environment is not one of ``ENVIRONMENTS``
        """
        if environment == cls.ENVIRONMENT_SANDBOX:
            return cls.SANDBOX_URL
        if environment not in cls.ENVIRONMENTS:
            raise ValueError(f"Unknown environment: '{environment}'")
        return cls.PRODUCTION_URL

    @classmethod
    def create(cls, environment: str, http_client: Optional[httpx.Client] = None) -> "MomoApi":
        """Create a client for an environment. Pass ``http_client`` to route its
        traffic through your own ``httpx.Client`` (timeouts, retries, proxies)."""
        return cls(environment, http_client)

    @property
    def environment(self) -> str:
        return self._environment

    @staticmethod
    def _require(config: Dict[str, Any], key: str) -> str:
        value = config.get(key)
        if not value:
            raise ValueError(f"{key} is required")
        return str(value)

    @classmethod
    def _resolve(cls, source: ConfigSource, environment: str) -> Tuple[Config, str]:
        """Normalize either accepted shape into a config plus a validated environment."""
        if isinstance(source, Config):
            config, target = source, environment
        else:
            config = Config.collection(
                cls._require(source, "subscription_key"),
                cls._require(source, "api_user"),
                cls._require(source, "api_key"),
                source.get("callback_url", "") or "",
            )
            target = source.get("environment") or cls.ENVIRONMENT_SANDBOX
        cls.get_base_url(target)
        return config, target

    @classmethod
    def collection(
        cls,
        config: ConfigSource,
        environment: str = ENVIRONMENT_SANDBOX,
        http_client: Optional[httpx.Client] = None,
    ) -> CollectionApi:
        """Build a Collection client.

        ``config`` is either a dict of flat credentials, with ``environment``,
        ``subscription_key``, ``api_user``, ``api_key`` and an optional
        ``callback_url``, or a ``Config``, in which case the environment comes
        from the ``environment`` argument.
        """
        cfg, target = cls._resolve(config, environment)
        return CollectionApi(cfg, cls.get_base_url(target), target, http_client)

    @classmethod
    def disbursement(
        cls,
        config: ConfigSource,
        environment: str = ENVIRONMENT_SANDBOX,
        http_client: Optional[httpx.Client] = None,
    ) -> DisbursementApi:
        """Build a Disbursement client. See ``collection()``."""
        cfg, target = cls._resolve(config, environment)
        return DisbursementApi(cfg, cls.get_base_url(target), target, http_client)

    def sandbox(self, subscription_key: str) -> SandboxApi:
        """Access the sandbox provisioning endpoints.

        :raises ValueError: when this client is not bound to the sandbox
        """
        if self._environment != self.ENVIRONMENT_SANDBOX:
            raise ValueError(f"Environment must be {self.ENVIRONMENT_SANDBOX}")
        return SandboxApi(subscription_key, self._base_url, self._http_client)

    def get_collection(self, config: Config) -> CollectionApi:
        return CollectionApi(config, self._base_url, self._environment, self._http_client)

    def get_disbursement(self, config: Config) -> DisbursementApi:
        return DisbursementApi(config, self._base_url, self._environment, self._http_client)
