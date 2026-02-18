import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd

from autopilot.detection import run_detection


trips = pd.read_csv("data/trips.csv")
expenses = pd.read_csv("data/expenses.csv")

findings = run_detection(trips, expenses)

print("\nDetection Findings:\n")

for f in findings[:10]:
    print(f)

print(f"\nTotal findings: {len(findings)}")
