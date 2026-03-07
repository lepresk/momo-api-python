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

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url

    @classmethod
    def create(cls, mode: str = ENVIRONMENT_STAGING) -> "AirtelApi":
        base_url = PRODUCTION_URL if mode == ENVIRONMENT_PRODUCTION else STAGING_URL
        return cls(base_url)

    def get_collection(self, config: AirtelConfig) -> AirtelCollectionApi:
        return AirtelCollectionApi(config, self._base_url)

    def get_disbursement(self, config: AirtelConfig) -> AirtelDisbursementApi:
        return AirtelDisbursementApi(config, self._base_url)

    @classmethod
    def collection(cls, mode: str, config: AirtelConfig) -> AirtelCollectionApi:
        """Shorthand factory for the Collection API."""
        return cls.create(mode).get_collection(config)

    @classmethod
    def disbursement(cls, mode: str, config: AirtelConfig) -> AirtelDisbursementApi:
        """Shorthand factory for the Disbursement API."""
        return cls.create(mode).get_disbursement(config)
