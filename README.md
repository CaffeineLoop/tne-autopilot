T&E Autopilot (AI Travel & Expense Optimization Agent)



This project is a working prototype of an AI agent that automatically analyzes a company’s travel and expense data, finds unnecessary spending, recommends improvements, and estimates savings before applying changes.
It is inspired by how modern travel platforms like ITILITE help companies optimize travel costs, but goes one step further by adding an autonomous “Autopilot” layer that can continuously detect problems, recommend fixes, simulate outcomes, and learn over time.
The goal of this project is to demonstrate how such an intelligent optimization system could be built end-to-end.


What this Autopilot does?

When you click Run Autopilot, the system performs the following steps:

Reads company travel and expense data
Detects inefficiencies like late bookings, non-preferred vendors, and policy violations
Uses AI to generate clear, actionable recommendations
Simulates the financial impact of applying those recommendations
Selects the best actions based on savings and risk
Shows projected savings and suggested policy changes
Logs each run and learns from past optimization results
Over time, the system builds a history and can explain what changes worked best.


Example questions you can ask

The system includes a natural language interface where you can ask questions like:

• Where are we overspending?
• What did Autopilot change recently?
• Which recommendation saved the most money?
• How much can we save next month?

The AI answers using real data from the system.

How the system is structured

The Autopilot works as a continuous optimization loop:
Detection Engine
→ finds spending inefficiencies
AI Recommendation Engine
→ converts findings into optimization strategies
Simulation Engine
→ estimates savings before applying changes
AI Decision Engine
→ selects best actions within safety guardrails
Autopilot Executor
→ applies policy changes in a sandbox
Learning Layer
→ tracks history and improves future decisions
Natural Language Interface
→ allows users to ask questions about the system



Technology used

Python
Streamlit (UI)
Pandas (data analysis)
Groq API (LLM intelligence layer)
Synthetic travel & expense dataset

The system is modular and can easily be connected to real company APIs instead of CSV data.




How to run locally?

Clone the repository
git clone https://github.com/YOUR_USERNAME/tne-autopilot.git
cd tne-autopilot


Install dependencies
pip install -r requirements.txt


Add your API key in .env
GROQ_API_KEY=your_key_here


Run the app
streamlit run ui/app.py

How to use the app?
Open the app in your browser.

Click Run Autopilot

View:

• detected inefficiencies
• recommendations
• projected savings
• policy changes

You can also ask questions in the Ask T&E section.

Why this project exists?

Most travel platforms can show insights, but someone still has to manually interpret them and take action.
This project demonstrates how an AI agent can close that gap by automatically:

• detecting problems
• recommending solutions
• simulating impact
• selecting actions
• learning over time

This makes optimization continuous instead of manual.



Notes

This is a prototype built using synthetic data for demonstration purposes.
The same architecture can be applied to real company travel systems.


Built as part of an exploration into autonomous enterprise optimization systems.


