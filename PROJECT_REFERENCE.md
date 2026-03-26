# ✦ AURA — Project Reference Guide
### Team 3G2B · Orchestron Competition 2025

---

## 1. COMPLETE FILE STRUCTURE

```
aura/
│
├── 📁 database/                        ← GOKUL'S DOMAIN
│   ├── ledger.json                     JSON ledger (transactions, budgets, subscriptions, profile)
│   ├── db.py                           Read/Write API for ledger.json
│   └── __init__.py
│
├── 📁 backend/                         ← REET'S DOMAIN
│   ├── tools.py                        fetch_data(), analyze_trends(), execute_action()
│   ├── goal_engine.py                  Forecasting, scenario planning, deadline risk
│   ├── auth.py                         JWT authentication, login, user sessions
│   ├── api.py                          FastAPI REST server — all endpoints
│   └── __init__.py
│
├── 📁 agent/                           ← PRATHAMESH'S DOMAIN
│   ├── workflow.py                     LangGraph: ANALYZE → PLAN → REVIEW → EXECUTE
│   └── __init__.py
│
├── 📁 frontend/                        ← SHREEYA'S DOMAIN
│   ├── streamlit_app.py                Streamlit dashboard (Brain, Plan, Action Log, Approvals)
│   ├── Dockerfile.react                Docker config for React production build
│   ├── index.html                      React app HTML shell
│   ├── package.json                    Node dependencies
│   ├── vite.config.js                  Vite bundler config (proxy → backend)
│   └── src/
│       ├── main.jsx                    React entry point
│       └── AuraDashboard.jsx           Full React dashboard component
│
├── 📁 tests/                           ← SHARED
│   ├── test_tools.py                   25 pytest tests: DB, tools, goal engine, agent, integration
│   └── __init__.py
│
├── demo.py                             Terminal demo — full agent loop with colour output
├── requirements.txt                    All Python dependencies
├── .env.example                        Environment variable template
├── .gitignore                          Git ignore rules
├── Dockerfile                          Docker image for FastAPI backend
├── Dockerfile.streamlit                Docker image for Streamlit frontend
├── docker-compose.yml                  Spins up all 3 services together
└── README.md                           Setup & architecture docs
```

**Total: 27 files across 5 directories**

---

## 2. REQUIREMENTS.TXT

```
# ── Web Framework & Server ────────────────────────────────────────────────────
fastapi==0.111.0
uvicorn[standard]==0.30.1

# ── Streamlit UI ──────────────────────────────────────────────────────────────
streamlit==1.35.0

# ── LangGraph Agent ───────────────────────────────────────────────────────────
langgraph==0.1.14
langchain-core==0.2.5

# ── Auth (JWT) ────────────────────────────────────────────────────────────────
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9

# ── Data & Forecasting ────────────────────────────────────────────────────────
pydantic==2.7.3
pandas==2.2.2
python-dateutil==2.9.0

# ── Networking ────────────────────────────────────────────────────────────────
requests==2.32.3
httpx==0.27.0

# ── Environment ───────────────────────────────────────────────────────────────
python-dotenv==1.0.1

# ── Testing ───────────────────────────────────────────────────────────────────
pytest==8.2.2
pytest-asyncio==0.23.7
```

---

## 3. INSTALL COMMANDS

### Prerequisites
Make sure you have these installed first:
- Python 3.10+ → https://python.org
- Node.js 18+  → https://nodejs.org
- Git           → https://git-scm.com

### Step 1 — Clone / enter the project
```bash
cd aura
```

### Step 2 — Create a Python virtual environment (recommended)
```bash
# Create venv
python -m venv venv

# Activate it
# On Mac/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3 — Install all Python dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Install React/Node dependencies
```bash
cd frontend
npm install
cd ..
```

### Step 5 — Set up environment variables
```bash
cp .env.example .env
# Edit .env if needed (defaults work out of the box for local dev)
```

---

## 4. RUN COMMANDS

### Option A — Run everything separately (recommended for development)

**Terminal 1 — Start the FastAPI backend:**
```bash
uvicorn backend.api:app --reload --port 8000
```
→ API live at: http://localhost:8000
→ Swagger docs: http://localhost:8000/docs

**Terminal 2 — Start the Streamlit frontend:**
```bash
streamlit run frontend/streamlit_app.py
```
→ Dashboard at: http://localhost:8501

**Terminal 3 — Start the React frontend (optional):**
```bash
cd frontend
npm run dev
```
→ React UI at: http://localhost:3000

**Terminal demo (no server needed):**
```bash
python demo.py
```
→ Full agent loop in the terminal with colour output

**Run the test suite:**
```bash
pytest tests/ -v
```

---

### Option B — Run everything with Docker (one command)

```bash
# Build and start all 3 services
docker-compose up --build

# Stop everything
docker-compose down
```

Services started:
- FastAPI  → http://localhost:8000
- Streamlit → http://localhost:8501
- React    → http://localhost:3000

---

## 5. TECH STACK

### Backend
| Layer         | Technology          | Purpose                                      |
|---------------|---------------------|----------------------------------------------|
| REST API      | FastAPI             | Exposes all agent & tool endpoints           |
| ASGI Server   | Uvicorn             | Runs FastAPI in production                   |
| Agent Engine  | LangGraph           | State machine: Analyze→Plan→Review→Execute   |
| Agent Core    | LangChain Core      | Base abstractions for LangGraph              |
| Auth          | python-jose + passlib | JWT tokens, bcrypt password hashing        |
| Data Layer    | JSON (ledger.json)  | Lightweight transactional ledger             |
| Forecasting   | Python (dateutil)   | Goal projections, scenario modelling         |
| Validation    | Pydantic v2         | Request/response schema validation           |

### Frontend
| Layer         | Technology          | Purpose                                      |
|---------------|---------------------|----------------------------------------------|
| Dashboard     | Streamlit           | Primary competition UI (Python-native)       |
| Component UI  | React 18 + Vite     | Alternative rich frontend                    |
| Fonts         | DM Mono + Syne      | Custom typography                            |
| Charts        | Streamlit native    | Spend bars, progress rings                   |

### DevOps & Tooling
| Tool          | Technology          | Purpose                                      |
|---------------|---------------------|----------------------------------------------|
| Containerisation | Docker + Compose | One-command full-stack deployment            |
| Testing       | Pytest              | 25 unit + integration tests                  |
| Env Config    | python-dotenv       | Manages secrets and environment vars         |
| HTTP Client   | Requests + HTTPX    | Frontend ↔ API communication                |
| Package Mgmt  | pip + npm           | Python and Node dependency management        |

### Architecture Pattern
```
User → Streamlit/React
          ↓ HTTP
       FastAPI (REST)
          ↓
     LangGraph Agent
    ┌──────────────┐
    │ ANALYZE Node │ ← fetch_data()      ← ledger.json
    │ PLAN Node    │ ← analyze_trends()  ← ledger.json
    │ REVIEW Node  │ ← Human-in-Loop gate (>₹100)
    │ EXECUTE Node │ ← execute_action()  → ledger.json
    └──────────────┘
          ↓
    {THOUGHT, PLAN, ACTION, UI_MESSAGE}
          ↓
    Frontend renders structured output
```
