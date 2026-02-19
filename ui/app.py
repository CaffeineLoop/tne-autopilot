import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
import plotly.express as px

from autopilot.agent import run_autopilot, apply_plan_to_policies
from autopilot.llm_client import ask_question, analyze_autopilot_history
from autopilot.detection import run_detection


# ---------------------------------------------------
# Load data
# ---------------------------------------------------

@st.cache_data
def load_data():

    trips = pd.read_csv("data/trips.csv")
    expenses = pd.read_csv("data/expenses.csv")

    with open("data/policies.json") as f:
        policies = json.load(f)

    return trips, expenses, policies


# ---------------------------------------------------
# Sidebar config
# ---------------------------------------------------

st.sidebar.title("Autopilot Settings")

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Autopilot",
        "Insights",
        "Policies",
        "Ask T&E",
        "Autopilot Learning"
    ]
)

st.sidebar.markdown("---")

max_changes = st.sidebar.slider(
    "Max changes per run",
    1, 5, 3
)

max_risk = st.sidebar.selectbox(
    "Max risk level",
    ["low", "medium", "high"],
    index=1
)

mode = st.sidebar.radio(
    "Mode",
    ["Simulate", "Apply"]
)

config = {
    "max_changes": max_changes,
    "max_risk": max_risk
}


# ---------------------------------------------------
# Load data
# ---------------------------------------------------

trips, expenses, policies = load_data()


# ---------------------------------------------------
# Title
# ---------------------------------------------------

st.title("T&E Autopilot")

st.caption(
    "AI agent that continuously optimizes your travel & expense program."
)


# ---------------------------------------------------
# Session state init
# ---------------------------------------------------

if "plan" not in st.session_state:
    st.session_state.plan = None

if "autopilot_history" not in st.session_state:
    st.session_state.autopilot_history = []


# ---------------------------------------------------
# Helper: get history from session_state only
# Streamlit Cloud has a read-only filesystem, so we
# never read/write history from disk — session_state
# is the single source of truth for run history.
# ---------------------------------------------------

def get_history():
    return st.session_state.get("autopilot_history", [])


# ---------------------------------------------------
# Run autopilot
# ---------------------------------------------------

if st.button("Run Autopilot"):

    plan = run_autopilot(
        trips,
        expenses,
        policies,
        config
    )

    st.session_state.plan = plan

    if mode == "Apply":
        # NOTE: Writing to data/policies.json will silently fail on
        # Streamlit Cloud (read-only filesystem). Policy changes are
        # reflected in-memory for this session only. To persist policy
        # changes, connect a database (e.g. Supabase) or use st.secrets.
        try:
            new_policies = apply_plan_to_policies(plan, policies)
            with open("data/policies.json", "w") as f:
                json.dump(new_policies, f, indent=2)
            st.success("Policies updated.")
        except OSError:
            st.warning(
                "Policy changes applied in-memory for this session. "
                "Persistent saves are not available on Streamlit Cloud."
            )


plan = st.session_state.plan


# ---------------------------------------------------
# KPI section
# ---------------------------------------------------

if plan:

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Spend",
        f"₹{int(plan.total_spend):,}"
    )

    col2.metric(
        "Estimated Leakage",
        f"₹{int(plan.estimated_leakage):,}"
    )

    col3.metric(
        "Potential Monthly Savings",
        f"₹{int(plan.potential_monthly_savings):,}"
    )


# ---------------------------------------------------
# Dashboard page
# ---------------------------------------------------

if page == "Dashboard":

    st.header("Overview")

    if not plan:

        st.info("Run Autopilot to generate insights.")

    else:

        st.subheader("Top Opportunities")

        for reco, sim in zip(
            plan.approved_recommendations,
            plan.simulations
        ):

            st.write(
                f"• {reco.title} → ₹{int(sim.monthly_savings):,}/month savings"
            )


# ---------------------------------------------------
# Autopilot page
# ---------------------------------------------------

elif page == "Autopilot":

    st.header("Autopilot Recommendations")

    if not plan:

        st.info("Click 'Run Autopilot' first.")

    else:

        for reco, sim in zip(
            plan.approved_recommendations,
            plan.simulations
        ):

            with st.expander(
                f"{reco.title} — ₹{int(sim.monthly_savings):,}/month"
            ):

                st.write("Lever:", reco.lever_type)
                st.write("Risk:", reco.risk_level)

                st.write(
                    f"Monthly Savings: ₹{int(sim.monthly_savings):,}"
                )

                st.write(
                    f"Annual Savings: ₹{int(sim.annual_savings):,}"
                )

                st.write(sim.explanation)

                df = pd.DataFrame({
                    "Scenario": ["Before", "After"],
                    "Spend": [
                        sim.baseline_spend,
                        sim.projected_spend
                    ]
                })

                fig = px.bar(
                    df,
                    x="Scenario",
                    y="Spend",
                    title="Simulation Impact"
                )

                st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------
# Insights page
# ---------------------------------------------------

elif page == "Insights":

    st.header("Insights")

    findings = run_detection(trips, expenses)

    late_routes = [
        f for f in findings
        if f["type"] == "late_booking"
    ]

    if late_routes:

        df = pd.DataFrame(late_routes)

        fig = px.bar(
            df,
            x="route",
            y="pct_late",
            title="Late Booking Rate by Route"
        )

        st.plotly_chart(fig, use_container_width=True)

    st.subheader("All Findings")

    st.dataframe(pd.DataFrame(findings))


# ---------------------------------------------------
# Policies page
# ---------------------------------------------------

elif page == "Policies":

    st.header("Policy Control Panel")

    st.caption(
        "Edit policies and rerun Autopilot to see impact."
    )

    route_caps = policies.get("route_caps", {})
    category_caps = policies.get("category_caps", {})
    rules = policies.get("rules", {})

    st.subheader("Route Caps")

    updated_route_caps = {}

    for route, cap in route_caps.items():

        updated_route_caps[route] = st.number_input(
            f"{route}",
            value=int(cap),
            step=500,
            key=f"route_{route}"
        )

    st.subheader("Category Caps")

    updated_category_caps = {}

    for cat, cap in category_caps.items():

        updated_category_caps[cat] = st.number_input(
            f"{cat}",
            value=int(cap),
            step=100,
            key=f"cat_{cat}"
        )

    st.subheader("Rules")

    min_days = st.number_input(
        "Minimum advance booking days",
        value=int(rules.get("min_advance_days", 3)),
        step=1
    )

    max_weekend = st.number_input(
        "Max weekend entertainment",
        value=int(rules.get("max_weekend_entertainment", 500)),
        step=100
    )

    if st.button("Save Policies"):

        policies["route_caps"] = updated_route_caps
        policies["category_caps"] = updated_category_caps
        policies["rules"]["min_advance_days"] = min_days
        policies["rules"]["max_weekend_entertainment"] = max_weekend

        try:
            with open("data/policies.json", "w") as f:
                json.dump(policies, f, indent=2)
            st.success("Policies saved successfully.")
        except OSError:
            st.warning(
                "Policies updated in-memory for this session. "
                "Persistent saves are not available on Streamlit Cloud."
            )


# ---------------------------------------------------
# Ask T&E page
# ---------------------------------------------------

elif page == "Ask T&E":

    st.header("Ask Your T&E")

    question = st.text_input("Ask anything")

    if question:

        if plan:

            # FIXED: Read history from session_state, not from disk.
            # data/history/autopilot_runs.json does not exist on
            # Streamlit Cloud — the filesystem is read-only.
            history = get_history()

            metrics = {
                "current_plan": {
                    "total_spend": plan.total_spend,
                    "leakage": plan.estimated_leakage,
                    "savings": plan.potential_monthly_savings
                },
                "run_history": history[-5:]
            }

            answer = ask_question(question, metrics)

            st.write(answer)

        else:

            st.write("Run Autopilot first.")


# ---------------------------------------------------
# Autopilot Learning page
# ---------------------------------------------------

elif page == "Autopilot Learning":

    st.header("Autopilot Learning Insights")

    # FIXED: Read history from session_state, not from disk.
    # data/history/autopilot_runs.json does not exist on
    # Streamlit Cloud — the filesystem is read-only.
    history = get_history()

    if history:

        insights = analyze_autopilot_history(history)

        st.write(insights)

        st.subheader("Run History")

        st.json(history)

    else:

        st.info("No runs recorded yet. Run Autopilot to start building history.")