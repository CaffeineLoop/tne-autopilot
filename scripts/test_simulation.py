import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd

from autopilot.detection import run_detection
from autopilot.recommendations import generate_recommendations
from autopilot.simulation import run_simulation


trips = pd.read_csv("data/trips.csv")
expenses = pd.read_csv("data/expenses.csv")

findings = run_detection(trips, expenses)

recos = generate_recommendations(findings)

print("\nSimulation Results:\n")

for reco in recos[:3]:

    result = run_simulation(reco, trips, expenses)

    print("Reco:", reco.title)

    print(vars(result))

    print()
