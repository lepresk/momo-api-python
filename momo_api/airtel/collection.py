from typing import Optional

from ..support.uuid import assert_uuid, generate_uuid
from .base import AbstractAirtelApi
from .transaction import AirtelTransaction


class AirtelCollectionApi(AbstractAirtelApi):
    """Airtel Money Collection API: receive payments."""

    def request_to_pay(
        self,
        amount: str,
        phone: str,
        reference: str,
        transaction_id: Optional[str] = None,
    ) -> str:
        """Initiate a payment request. Returns the externalId to poll with
        ``get_payment_status()``.

        :param transaction_id: UUID to use as the externalId instead of a random
            one, so the payment can be queried even if the response never arrives
        :raises MomoException: when Airtel refuses the payment, even with HTTP 200
        """
        external_id = generate_uuid() if transaction_id is None else transaction_id
        assert_uuid(external_id, "transaction_id")
        token = self.get_access_token()

        response = self._send(
            "POST",
            f"{self._base_url}/merchant/v1/payments/",
            json={
                "reference": reference,
                "subscriber": {
                    "country": self._config.country,
                    "currency": self._config.currency,
                    "msisdn": self._msisdn(phone),
                },
                "transaction": {
                    "amount": float(amount),
                    "country": self._config.country,
                    "currency": self._config.currency,
                    "id": external_id,
                },
            },
            headers={**self._airtel_headers(token), "Content-Type": "application/json"},
        )
        self._read_airtel(response)
        return external_id

    def get_payment_status(self, external_id: str) -> AirtelTransaction:
        """Pass the externalId returned by ``request_to_pay()``."""
        return self._get_transaction(f"/standard/v1/payments/{self._path_id(external_id)}", external_id)
