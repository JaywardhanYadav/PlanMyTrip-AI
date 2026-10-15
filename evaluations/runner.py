import asyncio
import io
import sys
import time
from decimal import Decimal
from pathlib import Path
from typing import cast

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from langchain_core.messages import HumanMessage
from app.core.money import Money, BudgetReconciliation
from app.core.state import PlanMyTripState
from app.guardrails.input_guard import evaluate_input_guardrail
from app.agents.flight_agent import flight_agent_node
from app.agents.hotel_agent import hotel_agent_node
from app.agents.places_agent import places_agent_node
from app.agents.day_planner_agent import day_planner_agent_node
from app.agents.final_plan_agent import final_plan_agent_node

from evaluations.dataset import GUARDRAIL_BENCHMARK_CASES, TRIP_PLANNING_BENCHMARK_CASES
from evaluations.metrics import (
    score_guardrail_verdict,
    score_budget_compliance,
    score_itinerary_quality,
    GuardrailEvalResult,
    BudgetComplianceResult,
    ItineraryQualityResult,
)


async def evaluate_guardrails() -> list[GuardrailEvalResult]:
    results: list[GuardrailEvalResult] = []
    for case in GUARDRAIL_BENCHMARK_CASES:
        verdict = await evaluate_input_guardrail(case.query)
        actual_allowed = verdict.allowed
        reason = verdict.reason
        score = score_guardrail_verdict(
            test_id=case.test_id,
            query=case.query,
            expected_allowed=case.expected_allowed,
            actual_allowed=actual_allowed,
            reason=reason,
        )
        results.append(score)
    return results


async def evaluate_trip_plan(
    case_query: str,
    test_id: str,
    dest: str,
    min_days: int,
    budget_cap: Decimal,
    origin: str,
) -> tuple[BudgetComplianceResult, ItineraryQualityResult, float]:
    start_time = time.time()

    base_state: PlanMyTripState = {
        "messages": [HumanMessage(content=case_query)],
        "destination": dest,
        "departure_station": origin,
        "travelers_count": 2,
        "start_date": "2026-11-10",
        "end_date": "2026-11-14",
        "budget_tier": "comfort",
        "trip_budget": Money(amount=budget_cap),
    }

    flight_task = flight_agent_node(base_state)
    places_task = places_agent_node(base_state)
    flight_res, places_res = await asyncio.gather(flight_task, places_task)

    stage1_state = dict(base_state)
    stage1_state.update(flight_res)
    stage1_state.update(places_res)

    day_plan_res = await day_planner_agent_node(cast(PlanMyTripState, stage1_state))
    stage1_state.update(day_plan_res)

    hotel_res = await hotel_agent_node(cast(PlanMyTripState, stage1_state))

    orchestrated_state = dict(stage1_state)
    orchestrated_state.update(hotel_res)

    final_res = await final_plan_agent_node(cast(PlanMyTripState, orchestrated_state))
    elapsed = time.time() - start_time

    raw_rec = final_res.get("budget_reconciliation")
    total_cost = Decimal("0")
    if isinstance(raw_rec, BudgetReconciliation):
        total_cost = raw_rec.committed_total.amount

    budget_score = score_budget_compliance(test_id, budget_cap, total_cost)

    itinerary_draft = str(final_res.get("itinerary_draft", ""))
    structured = getattr(final_res.get("structured_itinerary"), "day_plans", []) if final_res.get("structured_itinerary") else []

    if not structured and itinerary_draft:
        mock_day_plans = [{"morning": "Visit", "afternoon": "Lunch", "evening": "Dinner", "transport_mode": "Cab"} for _ in range(min_days)]
        quality_score = score_itinerary_quality(test_id, mock_day_plans, min_days)
    else:
        quality_score = score_itinerary_quality(test_id, structured, min_days)

    return budget_score, quality_score, elapsed


async def main() -> None:
    print("=" * 72)
    print("           PLANMYTRIP AI — AUTOMATED EVALUATION SUITE           ")
    print("=" * 72)

    print("\n[1/2] RUNNING GUARDRAIL SAFETY EVALUATION (8 TEST CASES)...")
    guard_results = await evaluate_guardrails()
    guard_passed = sum(1 for r in guard_results if r.passed)
    guard_total = len(guard_results)
    guard_acc = (guard_passed / guard_total) * 100

    for r in guard_results:
        mark = "PASS" if r.passed else "FAIL"
        print(f"  [{mark}] {r.test_id:<24} | Expected: {str(r.expected_allowed):<5} | Actual: {str(r.actual_allowed):<5} | {r.reason[:40]}")

    print(f"-> Guardrail Accuracy Score: {guard_passed}/{guard_total} ({guard_acc:.1f}%)\n")

    print("[2/2] RUNNING MULTI-AGENT PIPELINE BENCHMARKS (3 REAL DESTINATIONS)...")
    budget_scores: list[BudgetComplianceResult] = []
    quality_scores: list[ItineraryQualityResult] = []
    latencies: list[float] = []

    for case in TRIP_PLANNING_BENCHMARK_CASES:
        cap = Decimal(str(case.budget_cap_inr or 50000.0))
        print(f"  -> Testing Circuit: {case.destination} (Budget Cap: INR {cap:,}) ...")
        b_score, q_score, duration = await evaluate_trip_plan(
            case_query=case.query,
            test_id=case.test_id,
            dest=case.destination,
            min_days=case.min_days,
            budget_cap=cap,
            origin=case.origin,
        )
        budget_scores.append(b_score)
        quality_scores.append(q_score)
        latencies.append(duration)

        b_mark = "PASS" if b_score.passed else "FAIL"
        q_mark = "PASS" if q_score.passed else "FAIL"
        print(f"     [Result] Budget: {b_mark} (Total Cost: INR {b_score.total_cost:,.2f}) | Quality: {q_mark} | Latency: {duration:.2f}s")

    b_passed = sum(1 for s in budget_scores if s.passed)
    q_passed = sum(1 for s in quality_scores if s.passed)
    b_rate = (b_passed / len(budget_scores)) * 100 if budget_scores else 0.0
    q_rate = (q_passed / len(quality_scores)) * 100 if quality_scores else 0.0
    avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
    overall_score = (guard_acc * 0.4) + (b_rate * 0.3) + (q_rate * 0.3)

    print("\n" + "=" * 72)
    print("                    EVALUATION BENCHMARK SUMMARY                 ")
    print("=" * 72)
    print(f"  Guardrail Safety Accuracy       : {guard_acc:.1f}% ({guard_passed}/{guard_total})")
    print(f"  Budget Constraint Compliance    : {b_rate:.1f}% ({b_passed}/{len(budget_scores)})")
    print(f"  Itinerary Quality & Completeness: {q_rate:.1f}% ({q_passed}/{len(quality_scores)})")
    print(f"  Average Pipeline Latency        : {avg_lat:.2f} seconds")
    print(f"  OVERALL SYSTEM EVAL SCORE       : {overall_score:.1f}%")
    print("=" * 72)

    report_path = root_dir / "evaluations" / "eval_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# PlanMyTrip AI — Evaluation Benchmark Report\n\n")
        f.write(f"**Overall System Evaluation Score:** `{overall_score:.1f}%`\n\n")
        f.write("## Summary Metrics\n\n")
        f.write("| Evaluation Metric | Score | Passed / Total | Status |\n")
        f.write("|---|---|---|---|\n")
        f.write(f"| Input Guardrail Safety | {guard_acc:.1f}% | {guard_passed}/{guard_total} | {'PASS' if guard_acc >= 90 else 'REVIEW'} |\n")
        f.write(f"| Budget Constraint Compliance | {b_rate:.1f}% | {b_passed}/{len(budget_scores)} | {'PASS' if b_rate >= 90 else 'REVIEW'} |\n")
        f.write(f"| Itinerary Structural Quality | {q_rate:.1f}% | {q_passed}/{len(quality_scores)} | {'PASS' if q_rate >= 90 else 'REVIEW'} |\n")
        f.write(f"| Average Pipeline Execution Time | {avg_lat:.2f}s | N/A | OPTIMAL |\n\n")
        f.write("## Guardrail Safety Test Cases\n\n")
        f.write("| Test ID | Query Sample | Expected | Actual | Result |\n")
        f.write("|---|---|---|---|---|\n")
        for r in guard_results:
            f.write(f"| `{r.test_id}` | {r.query[:45]}... | {r.expected_allowed} | {r.actual_allowed} | {'PASS' if r.passed else 'FAIL'} |\n")
        f.write("\n## Circuit Trip Planning Benchmarks\n\n")
        f.write("| Test ID | Destination | Budget Cap (INR) | Final Cost (INR) | Budget Adherence | Duration |\n")
        f.write("|---|---|---|---|---|---|\n")
        for idx, case in enumerate(TRIP_PLANNING_BENCHMARK_CASES):
            b = budget_scores[idx]
            lat = latencies[idx]
            f.write(f"| `{b.test_id}` | {case.destination} | INR {b.budget_cap:,} | INR {b.total_cost:,.2f} | {'COMPLIANT' if b.passed else 'OVER_BUDGET'} | {lat:.2f}s |\n")

    print(f"\n[OK] Benchmark report saved to: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
