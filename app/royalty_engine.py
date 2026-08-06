"""
app/royalty_engine.py — Codex of the Living
Verdigris Botanica Tribal Nation Trust (VBTNT)

Economic-Return Layer — Sovereign Royalty Engine

Every DocuSign envelope event — completed or not — passes through this engine.
The engine calculates formula-based tribal returns and posts them to the VBTNT
Stripe account via a PaymentIntent.

Return categories
-----------------
royalty          — gross_revenue * royalty_rate (default 5 %)
REMIC_interest   — principal * pass_through_rate * days/360 (30/360 convention)
energy_return    — fixed sovereign energy surcharge per envelope event
sovereign_fee    — fixed tribal administrative fee per envelope event

Completed envelopes receive the full schedule.
Non-completed events receive the partial schedule (sovereign_fee + energy_return only).

All monetary values are Decimal strings to 2 decimal places.
Stripe amounts are integer USD cents (ROUND_HALF_UP).
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

# ---------------------------------------------------------------------------
# Rate schedule — all rates are VBTNT-sovereign and may only be amended by
# a formal written amendment issued by an authorized VBTNT principal.
# ---------------------------------------------------------------------------

_CENTS = Decimal("0.01")

# Royalty rate applied to gross contract revenue on completed envelopes
DEFAULT_ROYALTY_RATE = Decimal("0.05")          # 5 %

# REMIC pass-through rate for interest calculation on completed envelopes
DEFAULT_PASS_THROUGH_RATE = Decimal("0.06")     # 6 % annual

# Accrual period (days) used when the envelope carries no explicit day count
DEFAULT_ACCRUAL_DAYS = 30

# Fixed per-event sovereign fee (all events)
SOVEREIGN_FEE = Decimal("2.50")

# Fixed per-event energy return (all events)
ENERGY_RETURN = Decimal("1.00")

# Minimum Stripe PaymentIntent amount (USD cents) — Stripe rejects < $0.50
_STRIPE_MINIMUM_CENTS = 50

# ---------------------------------------------------------------------------
# Return-type constants (matches tribal_returns.return_type column)
# ---------------------------------------------------------------------------

RETURN_TYPE_ROYALTY = "royalty"
RETURN_TYPE_REMIC = "REMIC_interest"
RETURN_TYPE_ENERGY = "energy_return"
RETURN_TYPE_SOVEREIGN_FEE = "sovereign_fee"


def _dec(value, name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        raise ValueError(f"{name} must be numeric; got {value!r}")


def calculate_tribal_returns(
    *,
    envelope_status: str,
    principal: float | str | None = None,
    gross_revenue: float | str | None = None,
    royalty_rate: float | str | None = None,
    pass_through_rate: float | str | None = None,
    accrual_days: int | None = None,
) -> list[dict]:
    """
    Calculate all applicable tribal returns for a single envelope event.

    Parameters
    ----------
    envelope_status : str
        The DocuSign envelope status string (e.g. "completed", "sent", "voided").
    principal : numeric, optional
        Contract principal amount.  Used for REMIC interest on completed envelopes.
    gross_revenue : numeric, optional
        Gross contract revenue.  Used for royalty on completed envelopes.
    royalty_rate : numeric, optional
        Royalty rate (fraction).  Defaults to DEFAULT_ROYALTY_RATE.
    pass_through_rate : numeric, optional
        REMIC pass-through rate (annual, fraction).  Defaults to DEFAULT_PASS_THROUGH_RATE.
    accrual_days : int, optional
        Accrual days for REMIC interest.  Defaults to DEFAULT_ACCRUAL_DAYS.

    Returns
    -------
    list[dict]
        Each dict has keys: return_type (str), amount (str — Decimal to 2dp).
    """
    is_completed = (envelope_status or "").strip().lower() == "completed"
    returns: list[dict] = []

    # ── Every event: sovereign_fee ─────────────────────────────────────────
    returns.append({
        "return_type": RETURN_TYPE_SOVEREIGN_FEE,
        "amount": str(SOVEREIGN_FEE),
    })

    # ── Every event: energy_return ─────────────────────────────────────────
    returns.append({
        "return_type": RETURN_TYPE_ENERGY,
        "amount": str(ENERGY_RETURN),
    })

    if not is_completed:
        return returns

    # ── Completed envelopes only ───────────────────────────────────────────

    # Royalty
    if gross_revenue is not None:
        grev = _dec(gross_revenue, "gross_revenue")
        if grev < Decimal("0"):
            raise ValueError("gross_revenue must be non-negative")
        rate = (
            _dec(royalty_rate, "royalty_rate")
            if royalty_rate is not None
            else DEFAULT_ROYALTY_RATE
        )
        royalty_amount = (grev * rate).quantize(_CENTS, rounding=ROUND_HALF_UP)
        returns.append({
            "return_type": RETURN_TYPE_ROYALTY,
            "amount": str(royalty_amount),
        })

    # REMIC interest
    if principal is not None:
        p = _dec(principal, "principal")
        if p <= Decimal("0"):
            raise ValueError("principal must be positive")
        ptr = (
            _dec(pass_through_rate, "pass_through_rate")
            if pass_through_rate is not None
            else DEFAULT_PASS_THROUGH_RATE
        )
        days = accrual_days if accrual_days and accrual_days > 0 else DEFAULT_ACCRUAL_DAYS
        interest = (p * ptr * days / Decimal("360")).quantize(
            _CENTS, rounding=ROUND_HALF_UP
        )
        returns.append({
            "return_type": RETURN_TYPE_REMIC,
            "amount": str(interest),
        })

    return returns


def amount_to_cents(amount_str: str) -> int:
    """
    Convert a Decimal string amount (USD) to integer cents (ROUND_HALF_UP).
    Raises ValueError if the result is below the Stripe minimum.
    """
    cents = int(
        (Decimal(amount_str) * 100).to_integral_value(rounding=ROUND_HALF_UP)
    )
    return cents
