# ✦ AURA — Autonomous Wealth Pilot
### Team 3G2B | Orchestron Competition 2025

---

## Project Structure

```
aura/
├── database/
│   ├── ledger.json          ← JSON ledger (Gokul)
│   ├── db.py                ← Read/Write operations
│   └── __init__.py
│
├── backend/
│   ├── tools.py             ← fetch_data, analyze_trends, execute_action (Reet)
│   ├── api.py               ← FastAPI REST server
│   └── __init__.py
│
├── agent/
│   ├── workflow.py          ← LangGraph state machine (Prathamesh)
│   └── __init__.py
│
├── frontend/
│   ├── streamlit_app.py     ← Streamlit dashboard (Shreeya)
│   ├── src/
│   │   ├── main.jsx
│   │   └── AuraDashboard.jsx ← React dashboard
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the FastAPI backend
```bash
uvicorn backend.api:app --reload --port 8000
```
API docs available at: http://localhost:8000/docs

### 3A. Run Streamlit frontend (Shreeya)
```bash
streamlit run frontend/streamlit_app.py
```
Opens at: http://localhost:8501

### 3B. Run React frontend (alternative)
```bash
cd frontend
npm install
npm run dev
```
Opens at: http://localhost:3000

---

## Architecture

```
User Prompt
     │
     ▼
[FastAPI /api/agent/run]
     │
     ▼
[LangGraph State Machine]
  ANALYZE → PLAN → REVIEW → EXECUTE
     │         │        │        │
  fetch_data  plan   human    execute_action
  analyze_    tasks  review   (auto or HITL)
  trends
     │
     ▼
{THOUGHT, PLAN, ACTION, UI_MESSAGE}
     │
     ▼
[Streamlit / React Frontend]
  Brain Panel | Plan Panel | Action Log | Approval Panel
```

---

## Team Responsibilities

| Member     | File(s)                          | Role             |
|------------|----------------------------------|------------------|
| Gokul      | database/ledger.json, db.py      | Database         |
| Reet       | backend/tools.py                 | Backend Tools    |
| Prathamesh | agent/workflow.py                | LangGraph Agent  |
| Shreeya    | frontend/streamlit_app.py        | Streamlit UI     |
| All        | frontend/src/AuraDashboard.jsx   | React UI         |

---

## Key Features

- **Goal-Driven Architecture**: Continuously tracks savings gap
- **LangGraph Pipeline**: Analyze → Plan → Review → Execute nodes
- **Structured Output**: [THOUGHT] [PLAN] [ACTION] [UI_MESSAGE]
- **Human-in-the-Loop**: Actions > ₹100 require user approval
- **Autonomous Execution**: Budget cuts and sub cancellations via tools
- **Persistent Ledger**: JSON database with full audit log

---

## API Endpoints

| Method | Endpoint              | Description                  |
|--------|-----------------------|------------------------------|
| GET    | /api/ledger           | Full ledger JSON             |
| GET    | /api/tools/fetch      | Run fetch_data()             |
| GET    | /api/tools/analyze    | Run analyze_trends()         |
| POST   | /api/tools/execute    | Run execute_action()         |
| POST   | /api/agent/run        | Run full agent workflow      |
| POST   | /api/budget/update    | Update a budget category     |
| POST   | /api/subscriptions/action | Cancel/flag subscription |
