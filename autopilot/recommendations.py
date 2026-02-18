import json
import uuid
from typing import List, Dict

from autopilot.models import Recommendation
from autopilot.llm_client import generate_recommendations_with_llm


# -------------------------------------------------------
# Helper
# -------------------------------------------------------

def _generate_id():

    return "reco_" + uuid.uuid4().hex[:8]


def _estimate_monthly(leakage):

    # assume current data is ~3 months
    return int(leakage / 3)


# -------------------------------------------------------
# Rule-based fallback recommendations
# -------------------------------------------------------

def _rule_based_recommendations(findings: List[Dict]) -> List[Recommendation]:

    recos = []

    for f in findings:

        leakage = f.get("estimated_leakage", 0)

        if leakage < 20000:
            continue

        # Late booking reco
        if f["type"] == "late_booking":

            if f["pct_late"] > 0.5:

                recos.append(
                    Recommendation(
                        id=_generate_id(),
                        lever_type="behavior",
                        title=f"Reduce late bookings on {f['route']}",
                        description=(
                            f"{int(f['pct_late']*100)}% of trips on {f['route']} "
                            f"are booked late. Enforcing advance booking nudges "
                            f"can significantly reduce airfare costs."
                        ),
                        estimated_monthly_savings=_estimate_monthly(leakage),
                        risk_level="low",
                        targets={"route": f["route"]}
                    )
                )

        # Non preferred hotel
        elif f["type"] == "non_preferred_hotel":

            recos.append(
                Recommendation(
                    id=_generate_id(),
                    lever_type="vendor",
                    title=f"Increase preferred hotel usage on {f['route']}",
                    description=(
                        f"Significant usage of non-preferred hotels detected "
                        f"on {f['route']}. Encouraging preferred vendor booking "
                        f"can improve negotiated rate utilization."
                    ),
                    estimated_monthly_savings=_estimate_monthly(leakage),
                    risk_level="low",
                    targets={"route": f["route"]}
                )
            )

        # Over cap flights
        elif f["type"] == "over_cap_flight":

            recos.append(
                Recommendation(
                    id=_generate_id(),
                    lever_type="policy",
                    title=f"Enforce flight caps on {f['route']}",
                    description=(
                        f"{f['violations']} bookings exceeded policy caps. "
                        f"Stricter approval or automated enforcement can "
                        f"reduce cap violations."
                    ),
                    estimated_monthly_savings=_estimate_monthly(leakage),
                    risk_level="medium",
                    targets={"route": f["route"]}
                )
            )

        # Expense abuse
        elif f["type"] == "weekend_entertainment_abuse":

            recos.append(
                Recommendation(
                    id=_generate_id(),
                    lever_type="approval",
                    title="Control weekend entertainment expenses",
                    description=(
                        "Weekend entertainment expenses are significantly higher "
                        "than weekday averages. Additional approval guardrails "
                        "can reduce unnecessary spend."
                    ),
                    estimated_monthly_savings=_estimate_monthly(leakage),
                    risk_level="medium",
                    targets={"category": "Entertainment"}
                )
            )

    return recos


# -------------------------------------------------------
# Optional LLM enrichment
# -------------------------------------------------------

def _enrich_with_llm(findings: List[Dict], base_recos: List[Recommendation]):

    return base_recos


# -------------------------------------------------------
# Main entry point
# -------------------------------------------------------

def generate_recommendations(findings: List[Dict]) -> List[Recommendation]:

    # First try LLM-generated recommendations
    llm_recos = generate_recommendations_with_llm(findings)

    if llm_recos:

        # Convert dict → Recommendation objects
        recos = []

        for r in llm_recos:

            try:

                recos.append(
                    Recommendation(
                        id=r.get("id", _generate_id()),
                        lever_type=r.get("lever_type", "policy"),
                        title=r.get("title", "Recommendation"),
                        description=r.get("description", ""),
                        estimated_monthly_savings=int(
                            r.get("estimated_monthly_savings", 0)
                        ),
                        risk_level=r.get("risk_level", "medium"),
                        targets=r.get("targets", {})
                    )
                )

            except Exception:
                continue

        if recos:

            recos.sort(
                key=lambda x: x.estimated_monthly_savings,
                reverse=True
            )

            return recos

    # Fallback to rule-based recommendations
    recos = _rule_based_recommendations(findings)

    recos.sort(
        key=lambda r: r.estimated_monthly_savings,
        reverse=True
    )

    return recos
