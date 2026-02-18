import pandas as pd

trips = pd.read_csv("data/trips.csv")
expenses = pd.read_csv("data/expenses.csv")

print("\nTrips head:")
print(trips.head())

print("\nExpenses head:")
print(expenses.head())

trips["booking_date"] = pd.to_datetime(trips["booking_date"])
trips["travel_date"] = pd.to_datetime(trips["travel_date"])

trips["advance_days"] = (
    trips["travel_date"] - trips["booking_date"]
).dt.days

print("\nLate booking percentage:")
print((trips["advance_days"] < 3).mean())

print("\nAverage fare by route:")
print(trips.groupby(["origin", "destination"])["fare"].mean())

print("\nOver cap percentage:")
print((trips["fare"] > trips["policy_route_cap"]).mean())
