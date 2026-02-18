import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd

from autopilot.detection import run_detection
from autopilot.recommendations import generate_recommendations


trips = pd.read_csv("data/trips.csv")
expenses = pd.read_csv("data/expenses.csv")

findings = run_detection(trips, expenses)

recos = generate_recommendations(findings)

print("\nRecommendations:\n")

for r in recos:

    print(vars(r))
