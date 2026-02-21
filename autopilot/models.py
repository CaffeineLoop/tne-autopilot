from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class Recommendation:

    id: str

    lever_type: str   # policy | vendor | behavior | approval

    title: str

    description: str

    estimated_monthly_savings: int

    risk_level: str   # low | medium | high

    targets: Dict = field(default_factory=dict)

@dataclass
class SimulationResult:

    recommendation_id: str

    baseline_spend: float

    projected_spend: float

    monthly_savings: float

    annual_savings: float

    savings_pct: float

    explanation: str

    confidence_score: float = 75.0

    from typing import List


@dataclass
class AutopilotPlan:

    timestamp: str

    total_spend: float

    estimated_leakage: float

    potential_monthly_savings: float

    approved_recommendations: List[Recommendation]

    simulations: List[SimulationResult]

    suggested_policy_changes: List[dict]