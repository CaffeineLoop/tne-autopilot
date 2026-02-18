import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd

from autopilot.agent import run_autopilot, apply_plan_to_policies


trips = pd.read_csv("data/trips.csv")
expenses = pd.read_csv("data/expenses.csv")

with open("data/policies.json") as f:
    policies = json.load(f)


config = {
    "max_changes": 3,
    "max_risk": "medium"
}


plan = run_autopilot(
    trips,
    expenses,
    policies,
    config
)


print("\nAUTOPILOT PLAN\n")

print("Total spend:", plan.total_spend)

print("Leakage:", plan.estimated_leakage)

print("Potential monthly savings:", plan.potential_monthly_savings)

print("\nApproved recommendations:\n")

for reco in plan.approved_recommendations:

    print(vars(reco))


print("\nPolicy changes:\n")

for change in plan.suggested_policy_changes:

    print(change)


# Apply changes
new_policies = apply_plan_to_policies(plan, policies)

print("\nUpdated policies:\n")

print(json.dumps(new_policies, indent=2))
