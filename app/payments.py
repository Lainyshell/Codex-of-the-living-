"""
Payments orchestration — Stripe PaymentIntent creation and DocuSign envelope routing.

All credentials are read exclusively from environment variables:

    STRIPE_API_KEY          — Stripe secret key (sk_live_... / sk_test_...)
    DOCUSIGN_INTEGRATION_KEY — DocuSign OAuth integration key (client ID)
    DOCUSIGN_ACCOUNT_ID      — DocuSign account UUID
    DOCUSIGN_BASE_URL        — DocuSign REST API base URL
                               e.g. https://na4.docusign.net/restapi
    DOCUSIGN_ACCESS_TOKEN    — DocuSign OAuth access token for API authentication
                               (injected by your OAuth flow or GitHub Environment Secret)

Obligation-type → DocuSign template mapping is configured via
DOCUSIGN_TEMPLATE_<RATE_TYPE>_<REMIC_CLASS> environment variables.
Fallback: DOCUSIGN_TEMPLATE_DEFAULT.

Example:
    DOCUSIGN_TEMPLATE_GOV_OBLIGATION_A=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    DOCUSIGN_TEMPLATE_ROYALTY_B=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    DOCUSIGN_TEMPLATE_DEFAULT=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

DocuSign routing order (configured via env):
    DOCUSIGN_RECIPIENT_1_NAME, DOCUSIGN_RECIPIENT_1_EMAIL  (vendor)
    DOCUSIGN_RECIPIENT_2_NAME, DOCUSIGN_RECIPIENT_2_EMAIL  (tribal finance)
    DOCUSIGN_RECIPIENT_3_NAME, DOCUSIGN_RECIPIENT_3_EMAIL  (compliance)
    ...up to DOCUSIGN_RECIPIENT_COUNT recipients

If no DocuSign env vars are set, the send_docusign_envelope function raises
RuntimeError — it will never silently skip routing.
"""

import os

import stripe  # type: ignore[import-untyped]

# ---------------------------------------------------------------------------
# Stripe
# ---------------------------------------------------------------------------


def _stripe_key() -> str:
    key = os.environ.get("STRIPE_API_KEY", "")
    if not key:
        raise RuntimeError(
            "STRIPE_API_KEY environment variable is not set. "
            "Set it to your Stripe secret key before processing payments."
        )
    return key


def create_stripe_payment(
    *,
    amount_cents: int,
    vendor_id: str,
    obligation_id: str,
    remic_class: str,
    interest_amount: str,
    docusign_template: str,
    idempotency_key: str,
) -> dict:
    """
    Create a Stripe PaymentIntent and return its id, client_secret, and status.

    amount_cents must be a positive integer (amount in smallest currency unit, USD cents).
    idempotency_key is forwarded to Stripe to ensure exactly-once creation.
    """
    if amount_cents <= 0:
        raise ValueError("amount_cents must be a positive integer")

    stripe.api_key = _stripe_key()

    intent = stripe.PaymentIntent.create(
        amount=amount_cents,
        currency="usd",
        metadata={
            "vendor_id": vendor_id,
            "obligation_id": obligation_id,
            "remic_class": remic_class,
            "interest_amount": interest_amount,
            "docusign_template": docusign_template,
        },
        idempotency_key=idempotency_key,
    )

    return {
        "stripe_payment_id": intent["id"],
        "client_secret": intent["client_secret"],
        "status": intent["status"],
    }


# ---------------------------------------------------------------------------
# DocuSign
# ---------------------------------------------------------------------------


def _ds_env(var: str, required: bool = True) -> str:
    val = os.environ.get(var, "")
    if required and not val:
        raise RuntimeError(
            f"DocuSign environment variable {var!r} is not set. "
            "Configure all DOCUSIGN_* variables before routing envelopes."
        )
    return val


def _resolve_template(rate_type: str, remic_class: str) -> str:
    """
    Look up the DocuSign template ID for a given rate_type + remic_class.
    Variable name pattern: DOCUSIGN_TEMPLATE_<RATE_TYPE>_<REMIC_CLASS>
    Falls back to DOCUSIGN_TEMPLATE_DEFAULT.
    """
    key = f"DOCUSIGN_TEMPLATE_{rate_type.upper()}_{remic_class.upper()}"
    template_id = os.environ.get(key) or os.environ.get("DOCUSIGN_TEMPLATE_DEFAULT", "")
    if not template_id:
        raise RuntimeError(
            f"No DocuSign template configured for rate_type={rate_type!r} "
            f"remic_class={remic_class!r}. "
            f"Set {key!r} or DOCUSIGN_TEMPLATE_DEFAULT."
        )
    return template_id


def _build_recipients(
    vendor_name: str,
    vendor_email: str,
) -> list[dict]:
    """
    Build the DocuSign recipient list.

    The vendor (recipient 1) is always the first signer.
    Additional recipients are read from DOCUSIGN_RECIPIENT_<N>_NAME / EMAIL,
    starting at N=2.
    """
    recipients = [
        {
            "email": vendor_email,
            "name": vendor_name,
            "recipientId": "1",
            "routingOrder": "1",
            "roleName": "Vendor",
        }
    ]
    count = int(os.environ.get("DOCUSIGN_RECIPIENT_COUNT", "1"))
    for n in range(2, count + 1):
        name = os.environ.get(f"DOCUSIGN_RECIPIENT_{n}_NAME", "")
        email = os.environ.get(f"DOCUSIGN_RECIPIENT_{n}_EMAIL", "")
        role = os.environ.get(f"DOCUSIGN_RECIPIENT_{n}_ROLE", f"Reviewer{n}")
        if name and email:
            recipients.append(
                {
                    "email": email,
                    "name": name,
                    "recipientId": str(n),
                    "routingOrder": str(n),
                    "roleName": role,
                }
            )
    return recipients


def send_docusign_envelope(
    *,
    vendor_name: str,
    vendor_email: str,
    rate_type: str,
    remic_class: str,
    principal: str,
    interest: str,
    total: str,
    stripe_payment_id: str,
    vendor_id: str,
    obligation_id: str,
    transaction_id: str,
) -> dict:
    """
    Build and send a DocuSign envelope via the REST API.
    Returns the envelope_id.
    """
    import requests as _requests

    account_id = _ds_env("DOCUSIGN_ACCOUNT_ID")
    base_url = _ds_env("DOCUSIGN_BASE_URL")
    access_token = _ds_env("DOCUSIGN_ACCESS_TOKEN")
    template_id = _resolve_template(rate_type, remic_class)

    recipients = _build_recipients(vendor_name, vendor_email)

    # Map recipients for template roles
    template_roles = []
    for r in recipients:
        template_roles.append(
            {
                "email": r["email"],
                "name": r["name"],
                "roleName": r["roleName"],
                "tabs": {
                    "textTabs": [
                        {"tabLabel": "principal", "value": principal},
                        {"tabLabel": "interest", "value": interest},
                        {"tabLabel": "total", "value": total},
                        {"tabLabel": "remic_class", "value": remic_class},
                        {"tabLabel": "payment_id", "value": stripe_payment_id},
                        {"tabLabel": "vendor_id", "value": vendor_id},
                        {"tabLabel": "obligation_id", "value": obligation_id},
                        {"tabLabel": "transaction_id", "value": transaction_id},
                    ]
                },
            }
        )

    envelope_def = {
        "templateId": template_id,
        "templateRoles": template_roles,
        "status": "sent",
        "emailSubject": f"Payment Obligation {obligation_id} — Signature Required",
    }

    url = f"{base_url}/v2.1/accounts/{account_id}/envelopes"
    resp = _requests.post(
        url,
        json=envelope_def,
        headers={
            "Authorization": f"******",
            "Accept": "application/json",
        },
        timeout=15,
    )
    resp.raise_for_status()
    result = resp.json()

    envelope_id = result.get("envelopeId")
    if not envelope_id:
        raise RuntimeError(
            "DocuSign did not return an envelopeId"
        )
    return {"envelope_id": envelope_id, "status": result.get("status")}


# ---------------------------------------------------------------------------
# Webhook signature verification
# ---------------------------------------------------------------------------


def verify_docusign_hmac(
    payload_bytes: bytes,
    signature_header: str,
    hmac_key: str,
) -> bool:
    """
    Verify a DocuSign Connect HMAC-SHA256 signature.

    DocuSign sends the signature as a Base64-encoded HMAC-SHA256 digest of the
    raw request body, keyed with the shared secret configured in Connect.

    Reference:
        https://developers.docusign.com/platform/webhooks/connect/validate-hmac/
    """
    import base64
    import hashlib
    import hmac as _hmac

    expected = _hmac.new(
        hmac_key.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).digest()
    expected_b64 = base64.b64encode(expected).decode("utf-8")
    return _hmac.compare_digest(expected_b64, signature_header)
