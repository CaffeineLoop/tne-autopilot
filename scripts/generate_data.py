import os
import json
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker


fake = Faker()

# Ensure reproducibility
random.seed(42)
np.random.seed(42)


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)


# -----------------------------
# Configuration
# -----------------------------

NUM_TRIPS = 1500
NUM_EMPLOYEES = 120

DEPARTMENTS = ["Sales", "Engineering", "Marketing", "Finance", "HR"]

ROUTES = [
    ("BLR", "DEL"),
    ("BLR", "BOM"),
    ("BOM", "DEL"),
    ("DEL", "BLR"),
    ("MAA", "BLR"),
    ("BLR", "MAA"),
]

AIRLINES = [
    ("IndiGo", True),
    ("Air India", True),
    ("Vistara", True),
    ("SpiceJet", False),
    ("Akasa Air", False),
]

HOTELS = [
    ("Taj", True),
    ("ITC", True),
    ("Marriott", True),
    ("Lemon Tree", False),
    ("Treebo", False),
    ("OYO", False),
]

EXPENSE_CATEGORIES = {
    "Meals": 1000,
    "Entertainment": 1000,
    "Taxi": 1500,
    "Hotel": 8000,
}


ROUTE_CAPS = {
    "BLR-DEL": 9000,
    "BLR-BOM": 8000,
    "BOM-DEL": 8500,
    "DEL-BLR": 9000,
    "MAA-BLR": 7000,
    "BLR-MAA": 7000,
}


# Routes intentionally designed to have late bookings
LATE_BOOKING_ROUTES = {"BLR-DEL", "DEL-BLR"}

# Routes intentionally designed to have good behavior
EARLY_BOOKING_ROUTES = {"BLR-MAA", "MAA-BLR"}


# -----------------------------
# Helper functions
# -----------------------------

def generate_employee_ids(n):
    return [f"EMP{str(i).zfill(4)}" for i in range(1, n + 1)]


def random_date_within_last_months(months=4):
    today = datetime.today()
    start = today - timedelta(days=30 * months)
    delta = today - start
    return start + timedelta(days=random.randint(0, delta.days))


def get_booking_date(travel_date, route):
    """
    Simulate realistic booking behavior.
    Some routes mostly late, some mostly early.
    """

    route_key = f"{route[0]}-{route[1]}"

    if route_key in LATE_BOOKING_ROUTES:
        advance_days = random.choice([0, 1, 2, 3])
    elif route_key in EARLY_BOOKING_ROUTES:
        advance_days = random.choice([7, 10, 14])
    else:
        advance_days = random.choice([2, 4, 6, 8])

    return travel_date - timedelta(days=advance_days)


def generate_fare(route_cap, is_late):
    """
    Late bookings cost more.
    Occasionally exceed cap.
    """

    base = route_cap * random.uniform(0.7, 1.1)

    if is_late:
        base *= random.uniform(1.1, 1.4)

    # occasional violations
    if random.random() < 0.15:
        base *= random.uniform(1.1, 1.3)

    return int(base)


def generate_hotel_rate(preferred):
    base = random.randint(4000, 9000)

    if not preferred:
        base *= random.uniform(1.0, 1.3)

    if random.random() < 0.2:
        base *= random.uniform(1.2, 1.5)

    return int(base)


# -----------------------------
# Trips generation
# -----------------------------

def generate_trips():

    employee_ids = generate_employee_ids(NUM_EMPLOYEES)

    rows = []

    for trip_id in range(1, NUM_TRIPS + 1):

        employee_id = random.choice(employee_ids)
        dept = random.choice(DEPARTMENTS)

        origin, destination = random.choice(ROUTES)
        route_key = f"{origin}-{destination}"

        travel_date = random_date_within_last_months()

        booking_date = get_booking_date(travel_date, (origin, destination))

        advance_days = (travel_date - booking_date).days
        is_late = advance_days < 3

        airline, is_pref_airline = random.choice(AIRLINES)
        hotel, is_pref_hotel = random.choice(HOTELS)

        route_cap = ROUTE_CAPS[route_key]

        fare = generate_fare(route_cap, is_late)

        hotel_rate = generate_hotel_rate(is_pref_hotel)

        rows.append({
            "trip_id": trip_id,
            "employee_id": employee_id,
            "dept": dept,
            "origin": origin,
            "destination": destination,
            "booking_date": booking_date.date(),
            "travel_date": travel_date.date(),
            "airline": airline,
            "fare": fare,
            "hotel_name": hotel,
            "hotel_city": destination,
            "hotel_rate": hotel_rate,
            "is_preferred_airline": is_pref_airline,
            "is_preferred_hotel": is_pref_hotel,
            "policy_route_cap": route_cap
        })

    df = pd.DataFrame(rows)

    return df


# -----------------------------
# Expenses generation
# -----------------------------

def generate_expenses(trips_df):

    rows = []

    expense_id = 1

    for _, trip in trips_df.iterrows():

        num_expenses = random.randint(2, 5)

        for _ in range(num_expenses):

            category = random.choice(list(EXPENSE_CATEGORIES.keys()))
            cap = EXPENSE_CATEGORIES[category]

            date = pd.to_datetime(trip["travel_date"]) + timedelta(
                days=random.randint(0, 3)
            )

            is_weekend = date.weekday() >= 5

            base = cap * random.uniform(0.6, 1.1)

            # Weekend entertainment outliers
            if category == "Entertainment" and is_weekend:
                if random.random() < 0.35:
                    base *= random.uniform(1.5, 3.0)

            # occasional violations
            if random.random() < 0.2:
                base *= random.uniform(1.2, 1.6)

            amount = int(base)

            rows.append({
                "expense_id": expense_id,
                "employee_id": trip["employee_id"],
                "dept": trip["dept"],
                "date": date.date(),
                "category": category,
                "amount": amount,
                "policy_cat_cap": cap,
                "is_weekend": is_weekend,
                "is_card": random.random() < 0.85,
                "receipt_available": random.random() < 0.9
            })

            expense_id += 1

    return pd.DataFrame(rows)


# -----------------------------
# Policies generation
# -----------------------------

def generate_policies():

    policies = {
        "route_caps": ROUTE_CAPS,
        "category_caps": EXPENSE_CATEGORIES,
        "rules": {
            "min_advance_days": 3,
            "max_weekend_entertainment": 500
        }
    }

    return policies


# -----------------------------
# Main
# -----------------------------

def main():

    print("Generating trips...")
    trips = generate_trips()

    print("Generating expenses...")
    expenses = generate_expenses(trips)

    print("Generating policies...")
    policies = generate_policies()

    trips.to_csv(os.path.join(DATA_DIR, "trips.csv"), index=False)
    expenses.to_csv(os.path.join(DATA_DIR, "expenses.csv"), index=False)

    with open(os.path.join(DATA_DIR, "policies.json"), "w") as f:
        json.dump(policies, f, indent=2)

    print("Done.")
    print(f"Trips: {len(trips)}")
    print(f"Expenses: {len(expenses)}")


if __name__ == "__main__":
    main()
