from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class GuardrailEvalResult:
    test_id: str
    query: str
    expected_allowed: bool
    actual_allowed: bool
    passed: bool
    reason: str


@dataclass(frozen=True)
class BudgetComplianceResult:
    test_id: str
    passed: bool
    budget_cap: Decimal
    total_cost: Decimal
    is_over_budget: bool
    difference: Decimal


@dataclass(frozen=True)
class ItineraryQualityResult:
    test_id: str
    passed: bool
    total_days: int
    expected_min_days: int
    slots_complete: bool
    has_transit_mode: bool


def score_guardrail_verdict(
    test_id: str,
    query: str,
    expected_allowed: bool,
    actual_allowed: bool,
    reason: str,
) -> GuardrailEvalResult:
    passed = expected_allowed == actual_allowed
    return GuardrailEvalResult(
        test_id=test_id,
        query=query,
        expected_allowed=expected_allowed,
        actual_allowed=actual_allowed,
        passed=passed,
        reason=reason,
    )


def score_budget_compliance(
    test_id: str,
    budget_cap: Decimal,
    total_cost: Decimal,
) -> BudgetComplianceResult:
    is_over = total_cost > budget_cap
    diff = total_cost - budget_cap
    passed = not is_over and total_cost > Decimal("0")
    return BudgetComplianceResult(
        test_id=test_id,
        passed=passed,
        budget_cap=budget_cap,
        total_cost=total_cost,
        is_over_budget=is_over,
        difference=diff,
    )


def score_itinerary_quality(
    test_id: str,
    day_plans: list[Any],
    min_days: int,
) -> ItineraryQualityResult:
    days_count = len(day_plans)
    meets_days = days_count >= min_days
    all_slots = True
    has_transit = True

    for p in day_plans:
        morning = getattr(p, "morning", "") if hasattr(p, "morning") else p.get("morning", "")
        afternoon = getattr(p, "afternoon", "") if hasattr(p, "afternoon") else p.get("afternoon", "")
        evening = getattr(p, "evening", "") if hasattr(p, "evening") else p.get("evening", "")
        trans = getattr(p, "transport_mode", "") if hasattr(p, "transport_mode") else p.get("transport_mode", "")

        if not (morning and afternoon and evening):
            all_slots = False
        if not trans:
            has_transit = False

    passed = meets_days and all_slots and has_transit
    return ItineraryQualityResult(
        test_id=test_id,
        passed=passed,
        total_days=days_count,
        expected_min_days=min_days,
        slots_complete=all_slots,
        has_transit_mode=has_transit,
    )
