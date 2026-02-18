import pandas as pd


# -------------------------------------------------------
# Helper
# -------------------------------------------------------

def _prepare_trip_fields(trips_df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds derived fields needed for analysis.
    """

    df = trips_df.copy()

    df["booking_date"] = pd.to_datetime(df["booking_date"])
    df["travel_date"] = pd.to_datetime(df["travel_date"])

    df["advance_days"] = (
        df["travel_date"] - df["booking_date"]
    ).dt.days

    df["route"] = df["origin"] + "-" + df["destination"]

    return df


# -------------------------------------------------------
# Detection 1 — Late bookings
# -------------------------------------------------------

def find_late_bookings(trips_df: pd.DataFrame, min_advance_days: int = 3):

    df = _prepare_trip_fields(trips_df)

    findings = []

    grouped = df.groupby("route")

    for route, group in grouped:

        total = len(group)

        late_mask = group["advance_days"] < min_advance_days
        late_count = late_mask.sum()

        pct_late = late_count / total

        if late_count == 0:
            continue

        late_trips = group[late_mask]

        # Assume early booking would cost 15% less
        estimated_early_cost = late_trips["fare"] * 0.85

        overspend = (late_trips["fare"] - estimated_early_cost).sum()

        findings.append({
            "type": "late_booking",
            "route": route,
            "total_trips": int(total),
            "late_trips": int(late_count),
            "pct_late": round(float(pct_late), 3),
            "estimated_leakage": int(overspend)
        })

    return findings


# -------------------------------------------------------
# Detection 2 — Non-preferred hotels and airlines
# -------------------------------------------------------

def find_non_preferred_usage(trips_df: pd.DataFrame):

    df = _prepare_trip_fields(trips_df)

    findings = []

    grouped = df.groupby("route")

    for route, group in grouped:

        total = len(group)

        non_pref_hotel = (~group["is_preferred_hotel"]).sum()
        non_pref_airline = (~group["is_preferred_airline"]).sum()

        hotel_pct = non_pref_hotel / total
        airline_pct = non_pref_airline / total

        hotel_leakage = (
            group.loc[~group["is_preferred_hotel"], "hotel_rate"] * 0.12
        ).sum()

        airline_leakage = (
            group.loc[~group["is_preferred_airline"], "fare"] * 0.10
        ).sum()

        if hotel_pct > 0.2:

            findings.append({
                "type": "non_preferred_hotel",
                "route": route,
                "non_preferred_pct": round(float(hotel_pct), 3),
                "estimated_leakage": int(hotel_leakage)
            })

        if airline_pct > 0.2:

            findings.append({
                "type": "non_preferred_airline",
                "route": route,
                "non_preferred_pct": round(float(airline_pct), 3),
                "estimated_leakage": int(airline_leakage)
            })

    return findings


# -------------------------------------------------------
# Detection 3 — Over-cap bookings
# -------------------------------------------------------

def find_over_cap_bookings(trips_df: pd.DataFrame):

    df = _prepare_trip_fields(trips_df)

    findings = []

    # Flight cap violations
    flight_violations = df[df["fare"] > df["policy_route_cap"]]

    if len(flight_violations) > 0:

        grouped = flight_violations.groupby("route")

        for route, group in grouped:

            excess = (group["fare"] - group["policy_route_cap"]).sum()

            findings.append({
                "type": "over_cap_flight",
                "route": route,
                "violations": int(len(group)),
                "estimated_leakage": int(excess)
            })

    # Hotel cap proxy (use route cap as proxy for demo)
    hotel_violations = df[df["hotel_rate"] > df["policy_route_cap"]]

    if len(hotel_violations) > 0:

        grouped = hotel_violations.groupby("route")

        for route, group in grouped:

            excess = (
                group["hotel_rate"] - group["policy_route_cap"]
            ).sum()

            findings.append({
                "type": "over_cap_hotel",
                "route": route,
                "violations": int(len(group)),
                "estimated_leakage": int(excess)
            })

    return findings


# -------------------------------------------------------
# Detection 4 — Expense outliers
# -------------------------------------------------------

def find_expense_outliers(expenses_df: pd.DataFrame):

    df = expenses_df.copy()

    df["date"] = pd.to_datetime(df["date"])

    findings = []

    grouped = df.groupby("category")

    for category, group in grouped:

        mean_spend = group["amount"].mean()

        threshold = group["amount"].quantile(0.95)

        outliers = group[group["amount"] > threshold]

        outlier_leakage = (
            outliers["amount"] - mean_spend
        ).clip(lower=0).sum()

        findings.append({
            "type": "expense_outliers",
            "category": category,
            "mean_spend": int(mean_spend),
            "outlier_count": int(len(outliers)),
            "estimated_leakage": int(outlier_leakage)
        })

    # Weekend entertainment analysis
    weekend = df[
        (df["category"] == "Entertainment") &
        (df["is_weekend"] == True)
    ]

    weekday = df[
        (df["category"] == "Entertainment") &
        (df["is_weekend"] == False)
    ]

    if len(weekday) > 0 and len(weekend) > 0:

        weekend_mean = weekend["amount"].mean()
        weekday_mean = weekday["amount"].mean()

        if weekend_mean > weekday_mean * 1.5:

            leakage = (
                weekend["amount"] - weekday_mean
            ).clip(lower=0).sum()

            findings.append({
                "type": "weekend_entertainment_abuse",
                "weekend_mean": int(weekend_mean),
                "weekday_mean": int(weekday_mean),
                "estimated_leakage": int(leakage)
            })

    return findings


# -------------------------------------------------------
# Unified detection entry point
# -------------------------------------------------------

def run_detection(trips_df: pd.DataFrame, expenses_df: pd.DataFrame):

    findings = []

    findings.extend(find_late_bookings(trips_df))

    findings.extend(find_non_preferred_usage(trips_df))

    findings.extend(find_over_cap_bookings(trips_df))

    findings.extend(find_expense_outliers(expenses_df))

    return findings
