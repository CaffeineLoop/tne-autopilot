import json
from datetime import datetime
from typing import Dict, List

import pandas as pd

from autopilot.models import (
    AutopilotPlan,
    Recommendation,
    SimulationResult
)

from autopilot.detection import run_detection
from autopilot.recommendations import generate_recommendations
from autopilot.simulation import run_simulation

import os
from datetime import datetime


# -------------------------------------------------------
# FIXED: Safe absolute project root path
# -------------------------------------------------------

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

HISTORY_FILE = os.path.join(
    PROJECT_ROOT,
    "data",
    "history",
    "autopilot_runs.json"
)


# -------------------------------------------------------
# FIXED: Safe logging function (Streamlit Cloud compatible)
# -------------------------------------------------------

def log_autopilot_run(plan):

    # Ensure directory exists
    history_dir = os.path.dirname(HISTORY_FILE)
    os.makedirs(history_dir, exist_ok=True)

    run_record = {
        "timestamp": datetime.now().isoformat(),
        "total_spend": plan.total_spend,
        "estimated_leakage": plan.estimated_leakage,
        "potential_savings": plan.potential_monthly_savings,
        "recommendations": [
            {
                "id": r.id,
                "title": r.title,
                "lever_type": r.lever_type,
                "savings": r.estimated_monthly_savings,
                "risk": r.risk_level
            }
            for r in plan.approved_recommendations
        ]
    }

    # Create file if missing
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            json.dump([], f)

    # Read existing history
    with open(HISTORY_FILE, "r") as f:
        history = json.load(f)

    # Append new record
    history.append(run_record)

    # Save history
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------

RISK_ORDER = {
    "low": 1,
    "medium": 2,
    "high": 3
}


def _calculate_total_spend(trips_df, expenses_df):

    flight_spend = trips_df["fare"].sum()
    hotel_spend = trips_df["hotel_rate"].sum()
    expense_spend = expenses_df["amount"].sum()

    return float(flight_spend + hotel_spend + expense_spend)


def _calculate_total_leakage(findings):

    return float(
        sum(f.get("estimated_leakage", 0) for f in findings)
    )


def _filter_by_guardrails(
    recos: List[Recommendation],
    simulations: Dict[str, SimulationResult],
    config: Dict
):

    max_changes = config.get("max_changes", 3)
    max_risk = config.get("max_risk", "medium")

    max_risk_val = RISK_ORDER[max_risk]

    approved = []

    for reco in recos:

        if len(approved) >= max_changes:
            break

        if RISK_ORDER[reco.risk_level] <= max_risk_val:
            approved.append(reco)

    return approved


def _generate_policy_changes(
    approved_recos: List[Recommendation],
    simulations: Dict[str, SimulationResult]
):

    changes = []

    for reco in approved_recos:

        sim = simulations.get(reco.id)

        if reco.lever_type == "behavior":

            changes.append({
                "type": "policy_rule",
                "action": "enforce_min_advance_booking",
                "route": reco.targets.get("route"),
                "new_min_days": 5,
                "expected_monthly_savings": sim.monthly_savings
            })

        elif reco.lever_type == "vendor":

            changes.append({
                "type": "vendor_enforcement",
                "route": reco.targets.get("route"),
                "action": "prefer_preferred_hotels",
                "expected_monthly_savings": sim.monthly_savings
            })

        elif reco.lever_type == "approval":

            changes.append({
                "type": "approval_rule",
                "category": reco.targets.get("category"),
                "action": "require_approval_weekend",
                "expected_monthly_savings": sim.monthly_savings
            })

    return changes


# -------------------------------------------------------
# Main Autopilot loop
# -------------------------------------------------------

def run_autopilot(
    trips_df: pd.DataFrame,
    expenses_df: pd.DataFrame,
    policies: Dict,
    config: Dict
) -> AutopilotPlan:

    # Step 1: Detection
    findings = run_detection(trips_df, expenses_df)

    # Step 2: Recommendations
    recos = generate_recommendations(findings)

    # Step 3: Simulation
    simulations = {}

    for reco in recos:

        sim = run_simulation(reco, trips_df, expenses_df)

        simulations[reco.id] = sim

    # Step 4: Rank recommendations by simulation savings
    recos.sort(
        key=lambda r: simulations[r.id].monthly_savings,
        reverse=True
    )

    # Step 5: Apply guardrails
    approved_recos = _filter_by_guardrails(
        recos,
        simulations,
        config
    )

    # Step 6: Policy changes
    policy_changes = _generate_policy_changes(
        approved_recos,
        simulations
    )

    # Step 7: Summary metrics
    total_spend = _calculate_total_spend(trips_df, expenses_df)

    total_leakage = _calculate_total_leakage(findings)

    total_savings = sum(
        simulations[r.id].monthly_savings
        for r in approved_recos
    )

    plan = AutopilotPlan(

        timestamp=datetime.utcnow().isoformat(),

        total_spend=total_spend,

        estimated_leakage=total_leakage,

        potential_monthly_savings=total_savings,

        approved_recommendations=approved_recos,

        simulations=[simulations[r.id] for r in approved_recos],

        suggested_policy_changes=policy_changes
    )

    # NEW: Log run for continuous learning
    log_autopilot_run(plan)

    return plan


# -------------------------------------------------------
# Apply plan to sandbox policies
# -------------------------------------------------------

def apply_plan_to_policies(
    plan: AutopilotPlan,
    policies: Dict
) -> Dict:

    new_policies = json.loads(json.dumps(policies))

    for change in plan.suggested_policy_changes:

        if change["type"] == "policy_rule":

            route = change["route"]

            new_policies.setdefault("rules", {})

            new_policies["rules"][f"min_advance_days_{route}"] = (
                change["new_min_days"]
            )

        elif change["type"] == "approval_rule":

            category = change["category"]

            new_policies.setdefault("approval_rules", {})

            new_policies["approval_rules"][category] = (
                "weekend_required"
            )

    return new_policies
