import base64
import re

_PEM_HEADER = "-----BEGIN PUBLIC KEY-----"
_PEM_FOOTER = "-----END PUBLIC KEY-----"
_BASE64_TEXT = re.compile(r"^[A-Za-z0-9+/=\s]+$")


def _to_pem(key: str) -> str:
    """Airtel hands out the disbursement public key in several shapes: a PEM, a
    base64-encoded PEM, the bare base64 body, or that body base64-encoded again.
    Accept all four."""
    trimmed = key.strip()
    if _PEM_HEADER in trimmed:
        return trimmed

    try:
        decoded = base64.b64decode(trimmed, validate=False).decode("utf-8").strip()
    except (ValueError, UnicodeDecodeError):
        decoded = ""
    if _PEM_HEADER in decoded:
        return decoded

    # Either the base64 DER body itself, which decodes to binary, or that body
    # base64-encoded once more, which decodes to base64 text
    body = decoded if _BASE64_TEXT.match(decoded) else trimmed
    body = re.sub(r"\s", "", body)
    lines = "\n".join(body[i:i + 64] for i in range(0, len(body), 64))
    return f"{_PEM_HEADER}\n{lines}\n{_PEM_FOOTER}"


def encrypt_airtel_pin(pin: str, public_key: str) -> str:
    """Encrypt a disbursement PIN with Airtel's RSA public key.

    Airtel's transfer endpoint takes an encrypted PIN, never the PIN itself, and
    mandates PKCS#1 v1.5 padding. Requires the ``cryptography`` package:
    ``pip install "mtn-momo-client[airtel]"``.

    ::

        config = AirtelConfig.disbursement(
            client_id, client_secret, encrypt_airtel_pin("1234", os.environ["AIRTEL_PUBLIC_KEY"])
        )

    :param pin: the plain PIN
    :param public_key: Airtel's public key, base64-encoded or PEM
    :return: the encrypted PIN, base64-encoded
    """
    if not public_key or not public_key.strip():
        raise ValueError("Airtel public key is required to encrypt the PIN")

    try:
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives.serialization import load_pem_public_key
    except ImportError as error:  # pragma: no cover - depends on the environment
        raise ImportError(
            'encrypt_airtel_pin needs the "cryptography" package: '
            'pip install "mtn-momo-client[airtel]"'
        ) from error

    try:
        key = load_pem_public_key(_to_pem(public_key).encode("utf-8"))
        encrypted = key.encrypt(pin.encode("utf-8"), padding.PKCS1v15())  # type: ignore[union-attr]
    except Exception as error:
        raise ValueError(f"PIN encryption failed: {error}") from error
    return base64.b64encode(encrypted).decode("ascii")
