from typing import Optional

import httpx

from .collection import AirtelCollectionApi
from .config import AirtelConfig
from .disbursement import AirtelDisbursementApi

ENVIRONMENT_PRODUCTION = "production"
ENVIRONMENT_STAGING = "staging"

PRODUCTION_URL = "https://openapi.airtel.cg"
STAGING_URL = "https://openapiuat.airtel.cg"


class AirtelApi:
    """Entry point for the Airtel Money API."""

    ENVIRONMENT_PRODUCTION = ENVIRONMENT_PRODUCTION
    ENVIRONMENT_STAGING = ENVIRONMENT_STAGING
    PRODUCTION_URL = PRODUCTION_URL
    STAGING_URL = STAGING_URL

    def __init__(self, base_url: str, http_client: Optional[httpx.Client] = None) -> None:
        self._base_url = base_url
        self._http_client = http_client

    @classmethod
    def create(cls, mode: str = ENVIRONMENT_STAGING, http_client: Optional[httpx.Client] = None) -> "AirtelApi":
        base_url = PRODUCTION_URL if mode == ENVIRONMENT_PRODUCTION else STAGING_URL
        return cls(base_url, http_client)

    def get_collection(self, config: AirtelConfig) -> AirtelCollectionApi:
        return AirtelCollectionApi(config, self._base_url, self._http_client)

    def get_disbursement(self, config: AirtelConfig) -> AirtelDisbursementApi:
        return AirtelDisbursementApi(config, self._base_url, self._http_client)

    @classmethod
    def collection(
        cls, mode: str, config: AirtelConfig, http_client: Optional[httpx.Client] = None
    ) -> AirtelCollectionApi:
        """Shorthand factory for the Collection API."""
        return cls.create(mode, http_client).get_collection(config)

    @classmethod
    def disbursement(
        cls, mode: str, config: AirtelConfig, http_client: Optional[httpx.Client] = None
    ) -> AirtelDisbursementApi:
        """Shorthand factory for the Disbursement API."""
        return cls.create(mode, http_client).get_disbursement(config)
