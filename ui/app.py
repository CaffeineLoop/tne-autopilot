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
# File Upload (sidebar)
# ---------------------------------------------------

st.sidebar.markdown("---")
st.sidebar.subheader("Upload Custom Data")

uploaded_trips = st.sidebar.file_uploader(
    "Upload trips.csv",
    type=["csv"],
    help="Replaces default trips data for this session only."
)

uploaded_expenses = st.sidebar.file_uploader(
    "Upload expenses.csv",
    type=["csv"],
    help="Replaces default expenses data for this session only."
)


# ---------------------------------------------------
# Load data
# ---------------------------------------------------

trips, expenses, policies = load_data()

# Override with uploaded files if provided (session-scoped, no backend files modified)
if uploaded_trips is not None:
    try:
        trips = pd.read_csv(uploaded_trips)
        st.sidebar.success("Custom trips.csv loaded.")
    except Exception as e:
        st.sidebar.error(f"Failed to read trips.csv: {e}")

if uploaded_expenses is not None:
    try:
        expenses = pd.read_csv(uploaded_expenses)
        st.sidebar.success("Custom expenses.csv loaded.")
    except Exception as e:
        st.sidebar.error(f"Failed to read expenses.csv: {e}")


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

    # Log run into session_state (safe — we are in Streamlit context here)
    run_record = {
        "timestamp": str(pd.Timestamp.now()),
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
    st.session_state.autopilot_history.append(run_record)

    if mode == "Apply":

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
    # Decision Summary
    # ---------------------------------------------------

    st.markdown("---")

    st.subheader("Decision Summary")

    num_changes = len(plan.approved_recommendations)

    annual_savings = plan.potential_monthly_savings * 12

    if num_changes == 0:

        st.info(
            "Autopilot analyzed the dataset and found no safe optimization "
            "opportunities within current guardrails."
        )

    else:

        st.success(
            f"Autopilot analyzed ₹{int(plan.total_spend):,} in travel and expense spend. "
            f"It identified ₹{int(plan.estimated_leakage):,} in potential leakage and "
            f"recommends implementing {num_changes} policy change(s). "
            f"These changes are expected to save ₹{int(plan.potential_monthly_savings):,} "
            f"per month (₹{int(annual_savings):,} annually) within your configured risk guardrails."
        )

        st.write("**Primary optimization areas:**")

        for reco in plan.approved_recommendations:

            st.write(f"• {reco.title}")


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

                st.markdown("### Why this recommendation?")

                st.info(sim.explanation)

                st.markdown("### Expected Impact")

                imp_col1, imp_col2, imp_col3 = st.columns(3)

                imp_col1.metric(
                    "Monthly Savings",
                    f"₹{int(sim.monthly_savings):,}"
                )

                imp_col2.metric(
                    "Annual Savings",
                    f"₹{int(sim.annual_savings):,}"
                )

                imp_col3.metric(
                    "Savings %",
                    f"{sim.savings_pct * 100:.1f}%"
                )

                st.markdown("### Confidence Score")

                confidence = getattr(sim, "confidence_score", 75.0)

                st.metric(
                    "Confidence",
                    f"{int(confidence)}%"
                )

                st.progress(confidence / 100)

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
    # Before vs After Policy View
    # ---------------------------------------------------

    if plan:

        st.markdown("---")

        st.subheader("Autopilot Policy Changes Preview")

        try:

            new_policies = apply_plan_to_policies(plan, policies)

            col1, col2 = st.columns(2)

            with col1:

                st.write("**Current Policies**")

                st.json(policies)

            with col2:

                st.write("**Autopilot Proposed Policies**")

                st.json(new_policies)

        except Exception:

            st.warning("Policy preview unavailable.")

    else:

        st.info("Run Autopilot to preview proposed policy changes.")


# ---------------------------------------------------
# Ask T&E page
# ---------------------------------------------------

elif page == "Ask T&E":

    st.header("Ask Your T&E")

    question = st.text_input("Ask anything")

    if question:

        if plan:

            history = st.session_state.autopilot_history

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

    st.header("Autopilot Run History")

    history = st.session_state.autopilot_history

    if not history:

        st.info("No runs recorded yet. Run Autopilot to start building history.")

    else:

        # ---------------------------------------------------
        # LLM learning insights (existing feature — preserved)
        # ---------------------------------------------------

        insights = analyze_autopilot_history(history)

        st.write(insights)

        st.markdown("---")

        # ---------------------------------------------------
        # Summary metrics
        # ---------------------------------------------------

        st.subheader("Summary")

        total_runs = len(history)

        latest = history[-1]

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Runs", total_runs)

        col2.metric(
            "Latest Monthly Savings",
            f"₹{int(latest['potential_savings']):,}"
        )

        col3.metric(
            "Latest Leakage Detected",
            f"₹{int(latest['estimated_leakage']):,}"
        )

        st.markdown("---")

        # ---------------------------------------------------
        # Run timeline table
        # ---------------------------------------------------

        st.subheader("Run Timeline")

        history_df = pd.DataFrame(history)

        history_df = history_df.sort_values(
            by="timestamp",
            ascending=False
        )

        history_df["timestamp"] = pd.to_datetime(
            history_df["timestamp"]
        ).dt.strftime("%Y-%m-%d %H:%M:%S")

        history_df["total_spend"] = history_df["total_spend"].astype(int)
        history_df["estimated_leakage"] = history_df["estimated_leakage"].astype(int)
        history_df["potential_savings"] = history_df["potential_savings"].astype(int)

        st.dataframe(
            history_df[[
                "timestamp",
                "total_spend",
                "estimated_leakage",
                "potential_savings"
            ]],
            use_container_width=True
        )

        st.markdown("---")

        # ---------------------------------------------------
        # Savings trend chart
        # ---------------------------------------------------

        st.subheader("Savings Trend")

        fig = px.line(
            history_df,
            x="timestamp",
            y="potential_savings",
            markers=True,
            title="Autopilot Savings Over Time"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # ---------------------------------------------------
        # Detailed run logs
        # ---------------------------------------------------

        st.subheader("Detailed Run Logs")

        for run in reversed(history):

            with st.expander(
                f"{run['timestamp']} — ₹{int(run['potential_savings']):,} savings"
            ):

                st.write("Total Spend:", f"₹{int(run['total_spend']):,}")
                st.write("Leakage:", f"₹{int(run['estimated_leakage']):,}")
                st.write("Savings:", f"₹{int(run['potential_savings']):,}")

                st.write("Recommendations:")

                for reco in run["recommendations"]:

                    st.write(
                        f"• {reco['title']} "
                        f"(₹{int(reco['savings']):,}, {reco['risk']})"
                    )