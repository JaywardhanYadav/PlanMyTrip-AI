import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator


CENT: Decimal = Decimal("0.01")
ONE_LAKH: Decimal = Decimal("100000")
ONE_CRORE: Decimal = Decimal("10000000")
ONE_THOUSAND: Decimal = Decimal("1000")


class CurrencyMismatchError(Exception):

    def __init__(self, currency_a: str, currency_b: str) -> None:
        super().__init__(
            f"Cannot perform financial arithmetic across different currencies: "
            f"'{currency_a}' and '{currency_b}'. Convert currencies explicitly first."
        )
        self.currency_a = currency_a
        self.currency_b = currency_b


def parse_indian_budget_decimal(raw: str | int | float | Decimal) -> Decimal:
    if isinstance(raw, (int, float, Decimal)):
        return Decimal(str(raw)).quantize(CENT, rounding=ROUND_HALF_UP)

    text = str(raw).lower().strip()
    text = text.replace(",", "").replace("₹", "").replace("rs.", "").replace("rs", "").replace("inr", "").strip()

    crore_match = re.search(r"([\d\.]+)\s*(?:crores?|cr\b)", text)
    if crore_match:
        val = Decimal(crore_match.group(1))
        return (val * ONE_CRORE).quantize(CENT, rounding=ROUND_HALF_UP)

    lakh_match = re.search(r"([\d\.]+)\s*(?:lakhs?|lacs?|lac\b|l\b)", text)
    if lakh_match:
        val = Decimal(lakh_match.group(1))
        return (val * ONE_LAKH).quantize(CENT, rounding=ROUND_HALF_UP)

    k_match = re.search(r"([\d\.]+)\s*(?:thousands?|k\b)", text)
    if k_match:
        val = Decimal(k_match.group(1))
        return (val * ONE_THOUSAND).quantize(CENT, rounding=ROUND_HALF_UP)

    number_match = re.search(r"([\d\.]+)", text)
    if number_match:
        return Decimal(number_match.group(1)).quantize(CENT, rounding=ROUND_HALF_UP)

    return Decimal("200000.00")


def format_inr_amount(amount: Decimal) -> str:
    sign = "-" if amount < Decimal("0") else ""
    abs_amount = abs(amount)
    parts = f"{abs_amount:.2f}".split(".")
    int_part = parts[0]
    dec_part = parts[1]

    if len(int_part) <= 3:
        formatted_int = int_part
    else:
        last_three = int_part[-3:]
        remaining = int_part[:-3]
        chunks: list[str] = []
        while len(remaining) > 2:
            chunks.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            chunks.insert(0, remaining)
        formatted_int = ",".join(chunks) + "," + last_three

    return f"₹{sign}{formatted_int}.{dec_part}"


class Money(BaseModel):

    model_config = ConfigDict(frozen=True, extra="forbid")

    amount: Decimal = Field(
        description="Exact monetary amount quantized to 2 decimal places."
    )

    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
        description="Uppercase 3-letter ISO-4217 currency code.",
    )

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("amount")
    @classmethod
    def quantize_amount(cls, value: Decimal) -> Decimal:
        return value.quantize(CENT, rounding=ROUND_HALF_UP)

    def __add__(self, other: Self) -> "Money":
        self._assert_same_currency(other)
        return Money(
            amount=self.amount + other.amount,
            currency=self.currency,
        )

    def __sub__(self, other: Self) -> "Money":
        self._assert_same_currency(other)
        return Money(
            amount=self.amount - other.amount,
            currency=self.currency,
        )

    def __mul__(self, factor: Decimal | int) -> "Money":
        if isinstance(factor, int):
            factor = Decimal(factor)

        return Money(
            amount=self.amount * factor,
            currency=self.currency,
        )

    def __truediv__(self, divisor: Decimal | int) -> "Money":
        if isinstance(divisor, int):
            divisor = Decimal(divisor)

        if divisor == Decimal("0"):
            raise ZeroDivisionError("Cannot divide Money by zero.")

        return Money(
            amount=self.amount / divisor,
            currency=self.currency,
        )

    def __lt__(self, other: Self) -> bool:
        self._assert_same_currency(other)
        return self.amount < other.amount

    def __le__(self, other: Self) -> bool:
        self._assert_same_currency(other)
        return self.amount <= other.amount

    def __gt__(self, other: Self) -> bool:
        self._assert_same_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: Self) -> bool:
        self._assert_same_currency(other)
        return self.amount >= other.amount

    def _assert_same_currency(self, other: Self) -> None:
        if self.currency != other.currency:
            raise CurrencyMismatchError(
                self.currency,
                other.currency,
            )

    @classmethod
    def zero(cls, currency: str = "INR") -> "Money":
        return cls(
            amount=Decimal("0.00"),
            currency=currency,
        )

    @classmethod
    def from_str(
        cls,
        amount_str: str,
        currency: str = "INR",
    ) -> "Money":
        dec_amount = parse_indian_budget_decimal(amount_str)
        return cls(
            amount=dec_amount,
            currency=currency,
        )

    def to_formatted_str(self) -> str:
        if self.currency == "INR":
            return format_inr_amount(self.amount)
        formatted_amount = f"{self.amount:,.2f}"
        return f"{formatted_amount} {self.currency}"

    def to_words(self) -> str:
        if self.currency != "INR":
            return self.to_formatted_str()
        abs_val = abs(self.amount)
        if abs_val >= ONE_CRORE:
            cr_val = abs_val / ONE_CRORE
            return f"{cr_val:.2f}".rstrip("0").rstrip(".") + " Crore INR"
        elif abs_val >= ONE_LAKH:
            lakh_val = abs_val / ONE_LAKH
            return f"{lakh_val:.2f}".rstrip("0").rstrip(".") + " Lakh INR"
        elif abs_val >= ONE_THOUSAND:
            k_val = abs_val / ONE_THOUSAND
            return f"{k_val:.2f}".rstrip("0").rstrip(".") + " Thousand INR"
        return format_inr_amount(self.amount)


class BudgetReconciliation(BaseModel):

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_cap: Money = Field(
        description="User-defined maximum trip budget cap."
    )

    allocated_flights: Money = Field(
        description="Subtotal for selected flights."
    )

    allocated_hotels: Money = Field(
        description="Subtotal for selected hotels."
    )

    allocated_activities: Money = Field(
        description="Subtotal for selected activities."
    )

    committed_total: Money = Field(
        description="Exact sum of all selected items."
    )

    remaining_balance: Money = Field(
        description="total_cap minus committed_total."
    )

    is_over_budget: bool = Field(
        description="True if committed_total strictly exceeds total_cap."
    )

    overage_amount: Money = Field(
        description="Amount exceeding budget (zero if within budget)."
    )


def reconcile_trip_budget(
    total_cap: Money,
    flight_costs: list[Money],
    hotel_costs: list[Money],
    activity_costs: list[Money],
) -> BudgetReconciliation:

    target_currency = total_cap.currency

    allocated_flights = Money.zero(target_currency)

    for cost in flight_costs:
        allocated_flights += cost

    allocated_hotels = Money.zero(target_currency)

    for cost in hotel_costs:
        allocated_hotels += cost

    allocated_activities = Money.zero(target_currency)

    for cost in activity_costs:
        allocated_activities += cost

    committed_total = (
        allocated_flights
        + allocated_hotels
        + allocated_activities
    )

    remaining_balance = total_cap - committed_total

    is_over = committed_total > total_cap

    overage = (
        committed_total - total_cap
        if is_over
        else Money.zero(target_currency)
    )

    return BudgetReconciliation(
        total_cap=total_cap,
        allocated_flights=allocated_flights,
        allocated_hotels=allocated_hotels,
        allocated_activities=allocated_activities,
        committed_total=committed_total,
        remaining_balance=remaining_balance,
        is_over_budget=is_over,
        overage_amount=overage,
    )