"""
Payments orchestration — Stripe PaymentIntent creation and DocuSign envelope routing.

All credentials are read exclusively from environment variables:

    STRIPE_API_KEY              — Stripe secret key (sk_live_... / sk_test_...)

    -- DocuSign JWT (preferred) --
    DOCUSIGN_INTEGRATION_KEY    — Remic Portal integration key (OAuth client ID)
                                   Value: 54934ea2-813f-4288-8a8e-e09c293701ce
                                   RSA Keypair ID in DocuSign dashboard:
                                   428733c8-7467-4743-aede-3193af7620b0
    DOCUSIGN_USER_ID            — DocuSign user GUID to impersonate (API Username)
    DOCUSIGN_PRIVATE_KEY        — RSA private key PEM content (the private half of
                                   keypair 428733c8-7467-4743-aede-3193af7620b0)
    DOCUSIGN_OAUTH_HOST         — OAuth hostname (default: account.docusign.com)
                                   FedRAMP / GovCloud: account.docusign.us

    -- DocuSign common --
    DOCUSIGN_ACCOUNT_ID         — DocuSign account UUID
    DOCUSIGN_BASE_URL           — DocuSign REST API base URL
                                   e.g. https://na4.docusign.net/restapi
    DOCUSIGN_HMAC_KEY           — Shared HMAC secret for webhook signature verification

    -- Backward-compat bypass (skips JWT when set) --
    DOCUSIGN_ACCESS_TOKEN       — Pre-obtained ******; JWT auth is skipped
                                   when this variable is present

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
            "jurisdiction": "VBTNT",
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

# Remic Portal — Integration Key (OAuth client ID).
# Store this value in the DOCUSIGN_INTEGRATION_KEY environment variable.
# RSA Keypair ID in the DocuSign dashboard (for reference):
#   428733c8-7467-4743-aede-3193af7620b0
_DOCUSIGN_INTEGRATION_KEY_DEFAULT = "54934ea2-813f-4288-8a8e-e09c293701ce"


def _ds_env(var: str, required: bool = True) -> str:
    val = os.environ.get(var, "")
    if required and not val:
        raise RuntimeError(
            f"DocuSign environment variable {var!r} is not set. "
            "Configure all DOCUSIGN_* variables before routing envelopes."
        )
    return val


def _get_docusign_token() -> str:
    """
    Obtain a DocuSign access token via JWT Grant or bypass mode.

    Priority:
      1. If DOCUSIGN_ACCESS_TOKEN is set, return it directly (bypass JWT).
      2. Otherwise perform JWT Grant using:
           DOCUSIGN_INTEGRATION_KEY  (defaults to the Remic Portal key)
           DOCUSIGN_USER_ID          (API Username / impersonated user GUID)
           DOCUSIGN_PRIVATE_KEY      (PEM content of RSA keypair
                                      428733c8-7467-4743-aede-3193af7620b0)
           DOCUSIGN_OAUTH_HOST       (default: account.docusign.com)
    """
    bypass = os.environ.get("DOCUSIGN_ACCESS_TOKEN", "")
    if bypass:
        return bypass

    # JWT Grant via the docusign-esign SDK
    from docusign_esign import ApiClient  # type: ignore[import-untyped]

    integration_key = os.environ.get(
        "DOCUSIGN_INTEGRATION_KEY", _DOCUSIGN_INTEGRATION_KEY_DEFAULT
    )
    user_id = _ds_env("DOCUSIGN_USER_ID")
    private_key_raw = _ds_env("DOCUSIGN_PRIVATE_KEY")
    oauth_host = os.environ.get("DOCUSIGN_OAUTH_HOST", "account.docusign.com")

    private_key_bytes = private_key_raw.encode("utf-8")

    api_client = ApiClient()
    api_client.host = _ds_env("DOCUSIGN_BASE_URL")

    try:
        token_response = api_client.request_jwt_user_token(
            client_id=integration_key,
            user_id=user_id,
            oauth_host_name=oauth_host,
            private_key_bytes=private_key_bytes,
            expires_in=3600,
            scopes=["signature", "impersonation"],
        )
    except Exception as exc:
        raise RuntimeError(
            f"DocuSign JWT token request failed: {exc}. "
            "Verify DOCUSIGN_INTEGRATION_KEY, DOCUSIGN_USER_ID, "
            "DOCUSIGN_PRIVATE_KEY, and DOCUSIGN_OAUTH_HOST."
        ) from exc

    return token_response.access_token


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
    Build and send a DocuSign envelope via the SDK (EnvelopesApi).
    Returns a dict with envelope_id and status.
    """
    from docusign_esign import ApiClient, EnvelopesApi  # type: ignore[import-untyped]
    from docusign_esign.models import (  # type: ignore[import-untyped]
        EnvelopeDefinition,
        Tabs,
        TemplateRole,
        Text,
    )

    account_id = _ds_env("DOCUSIGN_ACCOUNT_ID")
    base_url = _ds_env("DOCUSIGN_BASE_URL")
    access_token = _get_docusign_token()
    template_id = _resolve_template(rate_type, remic_class)

    recipients = _build_recipients(vendor_name, vendor_email)

    tab_values = [
        Text(tab_label="principal", value=principal),
        Text(tab_label="interest", value=interest),
        Text(tab_label="total", value=total),
        Text(tab_label="remic_class", value=remic_class),
        Text(tab_label="payment_id", value=stripe_payment_id),
        Text(tab_label="vendor_id", value=vendor_id),
        Text(tab_label="obligation_id", value=obligation_id),
        Text(tab_label="transaction_id", value=transaction_id),
        Text(tab_label="jurisdiction", value="VBTNT"),
    ]

    template_roles = [
        TemplateRole(
            email=r["email"],
            name=r["name"],
            role_name=r["roleName"],
            tabs=Tabs(text_tabs=tab_values),
        )
        for r in recipients
    ]

    email_subject = f"Payment Obligation {obligation_id} — Signature Required"
    envelope_def = EnvelopeDefinition(
        template_id=template_id,
        template_roles=template_roles,
        status="sent",
        email_subject=email_subject,
    )

    api_client = ApiClient()
    api_client.host = f"{base_url}/v2.1"

    api_client.set_default_header("Authorization", f"******")

    try:
        result = EnvelopesApi(api_client).create_envelope(
            account_id=account_id,
            envelope_definition=envelope_def,
        )
    except Exception as exc:
        raise RuntimeError(
            "DocuSign create_envelope failed: " + str(exc)
        ) from exc

    envelope_id = result.envelope_id
    if not envelope_id:
        raise RuntimeError("DocuSign did not return an envelopeId")

    return {"envelope_id": envelope_id, "status": result.status}


def get_docusign_api_client() -> tuple:
    """
    Return an authenticated ``(ApiClient, account_id)`` tuple.

    Callers can use this instead of accessing the private helpers directly.
    The API client's ``host`` is already set to ``{base_url}/v2.1`` and
    the ``Authorization`` header is pre-populated.
    """
    from docusign_esign import ApiClient  # type: ignore[import-untyped]

    account_id = _ds_env("DOCUSIGN_ACCOUNT_ID")
    base_url = _ds_env("DOCUSIGN_BASE_URL")
    access_token = _get_docusign_token()

    api_client = ApiClient()
    api_client.host = f"{base_url}/v2.1"
    api_client.set_default_header("Authorization", f"******")
    return api_client, account_id


def get_docusign_envelope_status(envelope_id: str) -> dict:
    """
    Fetch the current status of a DocuSign envelope from the REST API.

    Returns a dict with at least:
        envelope_id  str
        status       str   (e.g. "completed", "sent", "delivered", "voided")
    """
    from docusign_esign import EnvelopesApi  # type: ignore[import-untyped]

    api_client, account_id = get_docusign_api_client()

    try:
        envelope = EnvelopesApi(api_client).get_envelope(
            account_id=account_id,
            envelope_id=envelope_id,
        )
    except Exception as exc:
        raise RuntimeError(
            f"DocuSign get_envelope failed for {envelope_id!r}: {exc}"
        ) from exc

    return {
        "envelope_id": envelope.envelope_id or envelope_id,
        "status": envelope.status or "",
    }


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
