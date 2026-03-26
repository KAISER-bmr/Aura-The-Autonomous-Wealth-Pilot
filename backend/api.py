"""
backend/api.py
Aura — FastAPI REST Server
Exposes agent and tool endpoints for the Streamlit/React frontend.
Run: uvicorn backend.api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.tools import fetch_data, analyze_trends, execute_action
from backend.goal_engine import compute_goal_forecast, compute_required_monthly_savings, set_savings_goal
from agent.workflow import run_agent_workflow
from database import db

try:
    from backend.auth import auth_router
    _auth_available = True
except ImportError:
    _auth_available = False

app = FastAPI(
    title="Aura Core Engine API",
    description="Autonomous Wealth Pilot — 3G2B Team",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── REQUEST MODELS ───────────────────────────────────────────────────────────

class AgentRunRequest(BaseModel):
    user_prompt: Optional[str] = "Analyze my finances and optimize savings."

class BudgetUpdateRequest(BaseModel):
    category: str
    new_budget: float

class SubscriptionActionRequest(BaseModel):
    sub_id: str
    action: str  # "cancel" | "flag" | "keep"

class ApprovalRequest(BaseModel):
    action_id: str
    approved: bool


# ─── ROUTES ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"engine": "Aura Core Engine", "status": "online", "version": "1.0.0"}


@app.get("/api/ledger")
def get_full_ledger():
    """Return the complete JSON ledger."""
    return db.get_ledger()


@app.get("/api/profile")
def get_profile():
    return db.get_user_profile()


@app.get("/api/transactions")
def get_transactions():
    return {"transactions": db.get_transactions()}


@app.get("/api/subscriptions")
def get_subscriptions():
    return {"subscriptions": db.get_subscriptions()}


@app.get("/api/actions/log")
def get_action_log():
    return {"actions": db.get_agent_actions()}


@app.get("/api/tools/fetch")
def tool_fetch_data():
    """Run fetch_data() and return snapshot."""
    return fetch_data()


@app.get("/api/tools/analyze")
def tool_analyze_trends():
    """Run analyze_trends() and return overspend analysis."""
    return analyze_trends()


@app.post("/api/tools/execute")
def tool_execute(action_type: str, category: str = None, new_budget: float = None,
                 sub_id: str = None, amount: float = None):
    """Run execute_action() with given params."""
    kwargs = {}
    if category: kwargs["category"] = category
    if new_budget is not None: kwargs["new_budget"] = new_budget
    if sub_id: kwargs["sub_id"] = sub_id
    if amount is not None: kwargs["amount"] = amount
    return execute_action(action_type, **kwargs)


@app.post("/api/agent/run")
def run_agent(request: AgentRunRequest):
    """
    Trigger the full LangGraph agent workflow.
    Returns: thought, plan, actions, ui_message — structured output
    for the frontend to parse and render.
    """
    result = run_agent_workflow(request.user_prompt)
    return result


@app.post("/api/budget/update")
def update_budget(req: BudgetUpdateRequest):
    """Directly update a budget category."""
    return db.update_budget(req.category, req.new_budget)


@app.post("/api/subscriptions/action")
def subscription_action(req: SubscriptionActionRequest):
    """Approve or reject a subscription action."""
    return db.flag_subscription(req.sub_id, req.action)


# ─── GOAL ENGINE ROUTES ───────────────────────────────────────────────────────

@app.get("/api/goal/forecast")
def goal_forecast():
    """Return savings forecast with 3 scenarios + milestones."""
    return compute_goal_forecast()

@app.get("/api/goal/required")
def goal_required():
    """Return required monthly savings to hit goal by deadline."""
    return compute_required_monthly_savings()

class GoalUpdateRequest(BaseModel):
    new_goal: float
    new_deadline: Optional[str] = None

@app.post("/api/goal/set")
def goal_set(req: GoalUpdateRequest):
    """Update the savings goal."""
    return set_savings_goal(req.new_goal, req.new_deadline)


# ─── MOUNT AUTH ROUTER ────────────────────────────────────────────────────────

if _auth_available:
    from backend.auth import auth_router
    app.include_router(auth_router)
