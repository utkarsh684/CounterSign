"""Decimal-safe financial calculations and integer minor units converters.

Never uses floating-point numbers for financial logic.
Amounts are strictly represented in integer minor units (e.g., USD cents, EUR cents, JPY units).
"""

from decimal import Decimal, ROUND_HALF_EVEN
from typing import Tuple


def dollars_to_minor_units(amount_str_or_decimal: str | Decimal | float, currency: str = "USD") -> int:
    """Converts a major currency string (e.g. '120.50') into integer minor units (12050 cents)."""
    d = Decimal(str(amount_str_or_decimal)).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    # Most currencies have 2 decimal places (JPY has 0, BHD has 3)
    if currency.upper() in ["JPY", "KRW"]:
        return int(Decimal(str(amount_str_or_decimal)).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))
    return int(d * 100)


def minor_units_to_decimal(minor_units: int, currency: str = "USD") -> Decimal:
    """Converts integer minor units (12050) to Decimal (120.50)."""
    if currency.upper() in ["JPY", "KRW"]:
        return Decimal(minor_units)
    return (Decimal(minor_units) / Decimal(100)).quantize(Decimal("0.01"))


def minor_units_to_formatted_string(minor_units: int, currency: str = "USD") -> str:
    """Formats minor units into human readable string e.g. '$120.50'."""
    val = minor_units_to_decimal(minor_units, currency)
    symbol = "$" if currency.upper() == "USD" else f"{currency} "
    return f"{symbol}{val:,.2f}"
