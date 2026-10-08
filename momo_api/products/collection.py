from typing import Optional

from ..models.currency import DEFAULT_CURRENCY
from ..models.payment_request import PaymentRequest
from ..models.transaction import Transaction
from .base import AbstractApiProduct


class CollectionApi(AbstractApiProduct):
    """MTN MoMo Collection API: receive payments."""

    PRODUCT_PATH = "collection"

    def request_to_pay(self, request: PaymentRequest, reference_id: Optional[str] = None) -> str:
        """Request a payment from a consumer. The payer authorizes it out of band,
        so this returns a reference id to poll with ``get_payment_status()``.

        :param reference_id: UUID to use as the reference id instead of a random
            one, so the payment can be queried even if the response never arrives
        """
        return self._submit("v1_0/requesttopay", request.to_dict(), reference_id)

    def get_payment_status(self, payment_id: str) -> Transaction:
        return self._get_transaction(f"v1_0/requesttopay/{payment_id}")

    def quick_pay(
        self,
        amount: str,
        phone: str,
        reference: str,
        currency: str = DEFAULT_CURRENCY,
        reference_id: Optional[str] = None,
    ) -> str:
        """Shorthand for a payment with no message or note."""
        return self.request_to_pay(PaymentRequest.make(amount, phone, reference, currency), reference_id)
