import re
from ..schemas.final_plan import StructuredItinerary
from .budget_reconciler import MultiTierTripBudget


def render_itinerary_markdown(itinerary: StructuredItinerary, budget_data: MultiTierTripBudget) -> str:
    clean_origin = re.sub(r"\s*\([A-Z]{3}\)", "", itinerary.origin).strip()
    clean_dest = re.sub(r"\s*\([A-Z]{3}\)", "", itinerary.destination).strip()
    clean_ret_origin = re.sub(r"\s*\([A-Z]{3}\)", "", itinerary.return_origin or "").strip() or clean_dest

    parts: list[str] = []

    parts.append(f"**{itinerary.trip_title}**")
    parts.append(f"**Travel Dates:** {itinerary.dates_formatted} ({itinerary.duration_label})")
    if clean_ret_origin and clean_ret_origin.lower() != clean_dest.lower():
        parts.append(f"**Route:** {clean_origin} ➔ {clean_dest} (Return from {clean_ret_origin})")
    else:
        parts.append(f"**Route:** {clean_origin} ➔ {clean_dest}")
    parts.append("")
    parts.append("---")
    parts.append("")

    if itinerary.flights:
        parts.append(f"✈️ **Flight Options ({clean_origin} to {clean_dest}):**")
        for idx, f in enumerate(itinerary.flights, 1):
            parts.append(f"- **Option {idx}:** **{f.carrier}** ({f.service_type}) | Timings: {f.timing} | ₹{f.price_per_person_inr:,.0f} per person (Total: ₹{f.total_price_inr:,.0f} for {budget_data.travelers_count} travelers)")
        parts.append("")
        parts.append("---")
        parts.append("")

    if itinerary.hotels:
        parts.append("🏨 **Places to Stay (Hotels):**")
        for idx, h in enumerate(itinerary.hotels, 1):
            clean_loc = re.sub(r"\s*\([A-Z]{3}\)", "", h.location).strip()
            clean_hname = re.sub(r"\s*\([A-Z]{3}\)", "", h.name).strip()
            parts.append(f"- **Option {idx}:** **{clean_hname}** ({clean_loc}) | Nightly: ₹{h.nightly_rate_inr:,.0f} | Total Stay: ₹{h.total_stay_inr:,.0f} | {h.amenities}")
        parts.append("")
        parts.append("---")
        parts.append("")

    parts.append("📅 **Day-by-Day Plan:**")
    parts.append("")

    for plan in itinerary.day_plans:
        parts.append(f"**Day {plan.day_number}: {plan.day_theme}**")
        parts.append(f"🌅 **Morning:** {plan.morning}")
        parts.append(f"☀️ **Afternoon:** {plan.afternoon}")
        parts.append(f"🌆 **Evening:** {plan.evening}")
        parts.append(f"🚗 **Transport:** {plan.transport_mode}")
        parts.append(f"📍 **Stay Tonight:** {plan.stay_area}")
        parts.append("")
        parts.append("---")
        parts.append("")

    if itinerary.return_flights:
        parts.append(f"🛬 **Return Flights ({clean_ret_origin} to {clean_origin}):**")
        for idx, rf in enumerate(itinerary.return_flights, 1):
            parts.append(f"- **Return Option {idx}:** **{rf.carrier}** ({rf.service_type}) | Timings: {rf.timing} | ₹{rf.price_per_person_inr:,.0f} per person (Total: ₹{rf.total_price_inr:,.0f} for {budget_data.travelers_count} travelers)")
        parts.append("")
        parts.append("---")
        parts.append("")

    parts.append("💰 **Estimated Trip Cost:**")
    parts.append("")

    if budget_data.budget_tier_specified == "unspecified":
        parts.append("Here are realistic average cost estimates across 3 standard travel styles:")
        parts.append("")

        b_tier = budget_data.budget_tier
        parts.append("🏷️ **1. Budget (Economy):**")
        parts.append(f"- **Travel Style:** {b_tier.description}")
        parts.append(f"- **Roundtrip Flights:** ~{b_tier.total_flights_cost.to_formatted_str()} (for all {budget_data.travelers_count} travelers)")
        parts.append(f"- **Hotels ({budget_data.duration_nights} nights):** ~{b_tier.total_hotel_cost.to_formatted_str()} ({b_tier.hotel_tier_name})")
        parts.append(f"- **Local Transport:** ~{b_tier.total_transit_cost.to_formatted_str()}")
        parts.append(f"- **Food & Daily Expenses:** ~{b_tier.total_dining_cost.to_formatted_str()}")
        parts.append(f"- **Estimated Total Cost:** ~{b_tier.total_trip_cost.to_formatted_str()}")
        parts.append("")

        m_tier = budget_data.mid_range_tier
        parts.append("🏷️ **2. Mid-Range (Comfort):**")
        parts.append(f"- **Travel Style:** {m_tier.description}")
        parts.append(f"- **Roundtrip Flights:** ~{m_tier.total_flights_cost.to_formatted_str()} (for all {budget_data.travelers_count} travelers)")
        parts.append(f"- **Hotels ({budget_data.duration_nights} nights):** ~{m_tier.total_hotel_cost.to_formatted_str()} ({m_tier.hotel_tier_name})")
        parts.append(f"- **Local Transport:** ~{m_tier.total_transit_cost.to_formatted_str()}")
        parts.append(f"- **Food & Daily Expenses:** ~{m_tier.total_dining_cost.to_formatted_str()}")
        parts.append(f"- **Estimated Total Cost:** ~{m_tier.total_trip_cost.to_formatted_str()}")
        parts.append("")

        l_tier = budget_data.luxury_tier
        parts.append("🏷️ **3. Luxury (5-Star & Premium):**")
        parts.append(f"- **Travel Style:** {l_tier.description}")
        parts.append(f"- **Roundtrip Flights:** ~{l_tier.total_flights_cost.to_formatted_str()} (for all {budget_data.travelers_count} travelers)")
        parts.append(f"- **Hotels ({budget_data.duration_nights} nights):** ~{l_tier.total_hotel_cost.to_formatted_str()} ({l_tier.hotel_tier_name})")
        parts.append(f"- **Local Transport:** ~{l_tier.total_transit_cost.to_formatted_str()}")
        parts.append(f"- **Food & Daily Expenses:** ~{l_tier.total_dining_cost.to_formatted_str()}")
        parts.append(f"- **Estimated Total Cost:** ~{l_tier.total_trip_cost.to_formatted_str()}")
        parts.append("")
    else:
        rec = budget_data.recommended_tier
        parts.append(f"🏷️ **{rec.tier_name}:**")
        parts.append(f"- **Roundtrip Flights:** ~{rec.total_flights_cost.to_formatted_str()} (for all {budget_data.travelers_count} travelers)")
        parts.append(f"- **Hotels ({budget_data.duration_nights} nights):** ~{rec.total_hotel_cost.to_formatted_str()} ({rec.hotel_tier_name})")
        parts.append(f"- **Local Transport:** ~{rec.total_transit_cost.to_formatted_str()}")
        parts.append(f"- **Food & Daily Expenses:** ~{rec.total_dining_cost.to_formatted_str()}")
        parts.append(f"- **Estimated Total Cost:** ~{rec.total_trip_cost.to_formatted_str()}")
        parts.append("")

    parts.append("*Note: All figures are indicative average estimates in Indian Rupees (₹ INR). Actual booking costs may fluctuate based on seasonal demand and advance reservations.*")
    parts.append("")
    parts.append(f"*{itinerary.closing_note}*")

    return "\n".join(parts)
