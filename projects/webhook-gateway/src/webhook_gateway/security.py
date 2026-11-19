from __future__ import annotations

import hashlib
import hmac


def verify_signature(payload: bytes, supplied: str | None, secret: str) -> bool:
    if not supplied:
        return False
    expected = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, supplied.strip())
