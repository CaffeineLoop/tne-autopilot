import pandas as pd
from typing import Dict

from autopilot.models import Recommendation, SimulationResult


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------

def _prepare_trips(trips_df):

    df = trips_df.copy()

    df["booking_date"] = pd.to_datetime(df["booking_date"])
    df["travel_date"] = pd.to_datetime(df["travel_date"])

    df["advance_days"] = (
        df["travel_date"] - df["booking_date"]
    ).dt.days

    df["route"] = df["origin"] + "-" + df["destination"]

    return df


# -------------------------------------------------------
# Simulation 1 — Advance booking enforcement
# -------------------------------------------------------

def simulate_advance_booking_change(
    reco: Recommendation,
    trips_df: pd.DataFrame
) -> SimulationResult:

    df = _prepare_trips(trips_df)

    route = reco.targets.get("route")

    impacted = df[
        (df["route"] == route) &
        (df["advance_days"] < 3)
    ]

    if len(impacted) == 0:

        return SimulationResult(
            recommendation_id=reco.id,
            baseline_spend=0,
            projected_spend=0,
            monthly_savings=0,
            annual_savings=0,
            savings_pct=0,
            explanation="No impacted trips found."
        )

    baseline = impacted["fare"].sum()

    # assume 60% compliance with new policy
    compliance_rate = 0.6

    shifted = impacted.sample(
        frac=compliance_rate,
        random_state=42
    )

    new_fares = shifted["fare"] * 0.85

    projected = baseline - (
        shifted["fare"].sum() - new_fares.sum()
    )

    savings = baseline - projected

    monthly = savings / 3
    annual = monthly * 12

    pct = savings / baseline if baseline else 0

    explanation = (
        f"If advance booking is enforced on {route}, "
        f"{int(compliance_rate*100)}% of late bookings shift earlier, "
        f"reducing airfare costs."
    )

    return SimulationResult(
        recommendation_id=reco.id,
        baseline_spend=float(baseline),
        projected_spend=float(projected),
        monthly_savings=float(monthly),
        annual_savings=float(annual),
        savings_pct=float(pct),
        explanation=explanation
    )


# -------------------------------------------------------
# Simulation 2 — Preferred hotel enforcement
# -------------------------------------------------------

def simulate_preferred_hotel_change(
    reco: Recommendation,
    trips_df: pd.DataFrame
) -> SimulationResult:

    df = _prepare_trips(trips_df)

    route = reco.targets.get("route")

    impacted = df[
        (df["route"] == route) &
        (~df["is_preferred_hotel"])
    ]

    preferred = df[
        (df["route"] == route) &
        (df["is_preferred_hotel"])
    ]

    if len(impacted) == 0 or len(preferred) == 0:

        return SimulationResult(
            recommendation_id=reco.id,
            baseline_spend=0,
            projected_spend=0,
            monthly_savings=0,
            annual_savings=0,
            savings_pct=0,
            explanation="No hotel optimization opportunity."
        )

    baseline = impacted["hotel_rate"].sum()

    preferred_avg = preferred["hotel_rate"].mean()

    compliance_rate = 0.7

    shifted = impacted.sample(
        frac=compliance_rate,
        random_state=42
    )

    new_cost = len(shifted) * preferred_avg

    projected = baseline - (
        shifted["hotel_rate"].sum() - new_cost
    )

    savings = baseline - projected

    monthly = savings / 3
    annual = monthly * 12

    pct = savings / baseline if baseline else 0

    explanation = (
        f"Shifting hotel bookings to preferred vendors "
        f"reduces average nightly rates on {route}."
    )

    return SimulationResult(
        recommendation_id=reco.id,
        baseline_spend=float(baseline),
        projected_spend=float(projected),
        monthly_savings=float(monthly),
        annual_savings=float(annual),
        savings_pct=float(pct),
        explanation=explanation
    )


# -------------------------------------------------------
# Simulation 3 — Expense abuse control
# -------------------------------------------------------

def simulate_expense_cap_change(
    reco: Recommendation,
    expenses_df: pd.DataFrame
) -> SimulationResult:

    df = expenses_df.copy()

    impacted = df[
        (df["category"] == "Entertainment") &
        (df["is_weekend"] == True)
    ]

    if len(impacted) == 0:

        return SimulationResult(
            recommendation_id=reco.id,
            baseline_spend=0,
            projected_spend=0,
            monthly_savings=0,
            annual_savings=0,
            savings_pct=0,
            explanation="No weekend entertainment spend."
        )

    baseline = impacted["amount"].sum()

    reduction_rate = 0.3

    projected = baseline * (1 - reduction_rate)

    savings = baseline - projected

    monthly = savings / 3
    annual = monthly * 12

    pct = savings / baseline if baseline else 0

    explanation = (
        "Adding approval guardrails reduces excessive "
        "weekend entertainment expenses."
    )

    return SimulationResult(
        recommendation_id=reco.id,
        baseline_spend=float(baseline),
        projected_spend=float(projected),
        monthly_savings=float(monthly),
        annual_savings=float(annual),
        savings_pct=float(pct),
        explanation=explanation
    )


# -------------------------------------------------------
# Unified simulation entry point
# -------------------------------------------------------

def run_simulation(
    reco: Recommendation,
    trips_df: pd.DataFrame,
    expenses_df: pd.DataFrame
) -> SimulationResult:

    if reco.lever_type == "behavior" and "route" in reco.targets:

        return simulate_advance_booking_change(reco, trips_df)

    elif reco.lever_type == "vendor":

        return simulate_preferred_hotel_change(reco, trips_df)

    elif reco.lever_type == "approval":

        return simulate_expense_cap_change(reco, expenses_df)

    else:

        return SimulationResult(
            recommendation_id=reco.id,
            baseline_spend=0,
            projected_spend=0,
            monthly_savings=0,
            annual_savings=0,
            savings_pct=0,
            explanation="Simulation not implemented for this type."
        )
