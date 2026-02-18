import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


MODEL = "llama-3.1-8b-instant"


def generate_recommendations_with_llm(findings):

    prompt = f"""
You are the autonomous optimization engine for a corporate Travel & Expense platform (similar to ITILITE Autopilot).

Your role is to act as a senior T&E consultant and policy optimization agent that continuously reduces travel spend while maintaining employee experience and policy fairness.

You are operating inside an automated execution loop:

Detection → Recommendation → Simulation → Policy Update → Continuous Optimization

Your recommendations will be directly evaluated and may be automatically applied to company travel policy.

OBJECTIVES (in priority order):

1. Reduce unnecessary spend and leakage.
2. Improve compliance with preferred vendors and policy caps.
3. Increase advance booking behavior to reduce airfare costs.
4. Reduce suspicious or non-compliant expense patterns.
5. Maintain low operational risk and minimal employee friction.

You are given structured leakage findings detected from real company travel and expense data.

Each finding includes quantified leakage, policy violations, or behavioral inefficiencies.

Your task is to convert these findings into precise, actionable, enterprise-grade optimization recommendations.

STRICT REQUIREMENTS:

Return ONLY a valid JSON array.

Each recommendation must contain EXACTLY these fields:

id: string
lever_type: one of ["policy", "vendor", "behavior", "approval"]
title: concise executive-level action title
description: 1–2 sentence explanation including quantified problem and expected impact
estimated_monthly_savings: integer (in INR)
risk_level: one of ["low", "medium", "high"]
targets: object describing affected route, city, department, or category

RECOMMENDATION GUIDELINES:

• Prioritize highest financial impact recommendations first.
• Focus on systemic fixes, not individual anomalies.
• Prefer behavioral nudges and vendor optimization before strict enforcement.
• Use "policy" lever_type only when structural policy change is needed.
• Use "approval" lever_type when adding approval guardrails.
• Use "vendor" lever_type when shifting to preferred vendors improves savings.
• Use "behavior" lever_type when employee booking timing or habits should change.

RISK LEVEL DEFINITION:

low → minimal disruption, nudges or vendor optimization
medium → introduces approval gates or tighter enforcement
high → strict restrictions or major policy changes

Only produce 3–5 recommendations maximum.

FINDINGS DATA:
{json.dumps(findings, indent=2)}

Return ONLY JSON.
No explanation.
No markdown.
No extra text.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an autonomous enterprise T&E optimization agent "
                    "operating inside a production travel management platform."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1
    )

    text = response.choices[0].message.content

    try:
        return json.loads(text)
    except:
        return None


def ask_question(question, metrics):

    prompt = f"""
You are the natural language analytics interface for a corporate Travel & Expense platform (similar to ITILITE Iris).

You answer executive and finance team questions about travel spend, leakage, and optimization opportunities.

You are NOT a chatbot. You are a precise enterprise analytics interface.

Use ONLY the provided metrics.

Be concise, factual, and executive-friendly.

Always include specific numbers.

Never speculate beyond given data.

All currency values are in Indian Rupees (₹).

METRICS:
{json.dumps(metrics, indent=2)}

QUESTION:
{question}

ANSWER GUIDELINES:

• Maximum 2 sentences.
• Use concrete numbers.
• Focus on financial impact.
• Answer like a finance analytics dashboard, not conversational AI.

Return only the answer text.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are the analytics engine of an enterprise travel optimization platform."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.0
    )

    return response.choices[0].message.content

def interpret_findings(findings):

    prompt = f"""
You are the analytics engine of a corporate travel platform.

Analyze these findings and explain the key optimization opportunities.

Focus on:

• largest leakage drivers
• behavioral vs policy issues
• vendor optimization opportunities
• priority areas for intervention

Findings:
{json.dumps(findings, indent=2)}

Return 3 concise executive insights.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a travel analytics expert."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )

    return response.choices[0].message.content

def select_recommendations_with_llm(recommendations, config):

    prompt = f"""
You are the Autopilot decision engine of a corporate travel platform.

Your task is to select which recommendations to apply automatically.

Constraints:

Max changes allowed: {config["max_changes"]}
Max risk allowed: {config["max_risk"]}

Prioritize:

• highest savings
• lowest operational risk
• minimal employee disruption
• long-term policy stability

Recommendations:
{json.dumps(recommendations, indent=2)}

Return JSON array of selected recommendation IDs in priority order.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are an autonomous optimization agent."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return json.loads(response.choices[0].message.content)

def explain_simulation(simulation_data):

    prompt = f"""
Explain this travel policy simulation outcome:

{json.dumps(simulation_data, indent=2)}

Explain savings drivers clearly.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a travel optimization analyst."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

def analyze_autopilot_history(history):

    prompt = f"""
You are the continuous learning engine of an autonomous travel optimization system.

Analyze past Autopilot runs and identify:

• which optimization strategies delivered best savings
• trends in leakage reduction
• most effective policy interventions
• recommendations for future optimization focus

Run history:
{json.dumps(history, indent=2)}

Return 3 concise insights.
"""

    response = client.chat.completions.create(

        model=MODEL,

        messages=[
            {
                "role": "system",
                "content": "You are an autonomous optimization learning engine."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0.1
    )

    return response.choices[0].message.content


