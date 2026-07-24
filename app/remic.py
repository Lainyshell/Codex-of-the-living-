"""
REMIC Interest Calculator — Verdigris Botanica Tribal Nation

Implements IRS/government-aligned REMIC interest formulas for the following
classes and rate types:

  Standard class (A, B): principal * pass_through_rate * days / 360
  IO class:             notional * io_rate * days / 360
  PO class:             interest = 0 (principal-only)
  Royalty variant:      royalty = gross_revenue * royalty_rate
                        REMIC interest on royalty (if securitised):
                            royalty * pass_through_rate * days / 360

Day-count convention: 30/360 (standard REMIC)
Rounding: ROUND_HALF_UP to 2 decimal places throughout.
"""

from decimal import Decimal, ROUND_HALF_UP

VALID_RATE_TYPES = frozenset({"royalty", "gov_obligation"})
VALID_REMIC_CLASSES = frozenset({"A", "B", "IO", "PO"})

_CENTS = Decimal("0.01")
_360 = Decimal("360")


def _dec(value, name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        raise ValueError(f"{name} must be a numeric value; got {value!r}")


def calculate_interest(
    *,
    principal: float | str,
    pass_through_rate: float | str,
    days: int,
    remic_class: str,
    rate_type: str = "gov_obligation",
    # IO-class extras
    notional: float | str | None = None,
    io_rate: float | str | None = None,
    # Royalty extras
    gross_revenue: float | str | None = None,
    royalty_rate: float | str | None = None,
) -> dict:
    """
    Calculate REMIC interest for a single obligation.

    Returns a dict with:
        royalty_amount  Decimal — royalty component (0 for gov_obligation)
        interest_amount Decimal — REMIC interest component
        total_amount    Decimal — principal + interest (royalties excluded from total)
        remic_class     str
        rate_type       str
        days            int
    """
    if rate_type not in VALID_RATE_TYPES:
        raise ValueError(
            f"Invalid rate_type {rate_type!r}. Must be one of {sorted(VALID_RATE_TYPES)}."
        )
    if remic_class not in VALID_REMIC_CLASSES:
        raise ValueError(
            f"Invalid remic_class {remic_class!r}. Must be one of {sorted(VALID_REMIC_CLASSES)}."
        )
    if not isinstance(days, int) or days <= 0:
        raise ValueError(f"days must be a positive integer; got {days!r}")

    principal_d = _dec(principal, "principal")
    if principal_d <= Decimal("0"):
        raise ValueError("principal must be positive")

    pass_through_rate_d = _dec(pass_through_rate, "pass_through_rate")

    royalty_amount = Decimal("0")
    interest_amount = Decimal("0")

    # PO class: no interest, principal only
    if remic_class == "PO":
        return {
            "royalty_amount": royalty_amount,
            "interest_amount": interest_amount,
            "total_amount": principal_d,
            "remic_class": remic_class,
            "rate_type": rate_type,
            "days": days,
        }

    if rate_type == "royalty":
        if gross_revenue is None or royalty_rate is None:
            raise ValueError(
                "rate_type='royalty' requires gross_revenue and royalty_rate"
            )
        gross_revenue_d = _dec(gross_revenue, "gross_revenue")
        royalty_rate_d = _dec(royalty_rate, "royalty_rate")
        if gross_revenue_d < Decimal("0"):
            raise ValueError("gross_revenue must be non-negative")
        royalty_amount = (gross_revenue_d * royalty_rate_d).quantize(
            _CENTS, rounding=ROUND_HALF_UP
        )
        interest_base = royalty_amount
    else:
        interest_base = principal_d

    if remic_class == "IO":
        if notional is None or io_rate is None:
            raise ValueError("remic_class='IO' requires notional and io_rate")
        notional_d = _dec(notional, "notional")
        io_rate_d = _dec(io_rate, "io_rate")
        if notional_d <= Decimal("0"):
            raise ValueError("notional must be positive")
        interest_amount = (notional_d * io_rate_d * days / _360).quantize(
            _CENTS, rounding=ROUND_HALF_UP
        )
    else:
        interest_amount = (interest_base * pass_through_rate_d * days / _360).quantize(
            _CENTS, rounding=ROUND_HALF_UP
        )

    total_amount = (principal_d + interest_amount).quantize(_CENTS, rounding=ROUND_HALF_UP)

    return {
        "royalty_amount": royalty_amount,
        "interest_amount": interest_amount,
        "total_amount": total_amount,
        "remic_class": remic_class,
        "rate_type": rate_type,
        "days": days,
    }
