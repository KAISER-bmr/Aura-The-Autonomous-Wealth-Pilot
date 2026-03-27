"""
backend/api_v2.py
Aura — FastAPI v2 with MySQL, Auth, Expenses, Goals, Notifications
Run: uvicorn backend.api_v2:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database.mysql_db import (
    setup_database, create_user, get_user_by_username, get_user_by_id,
    verify_password, get_user_goal, update_user_goal,
    add_transaction, get_transactions, get_spend_by_category,
    get_budgets, update_budget,
    get_notifications, mark_notifications_read
)
from backend.tools import fetch_data, analyze_trends, execute_action
from agent.workflow import run_agent_workflow

# ─── INIT ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Aura Core Engine API v2",
    description="Autonomous Wealth Pilot — 3G2B Team",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup DB on startup
@app.on_event("startup")
def on_startup():
    try:
        setup_database()
        print("[AURA] MySQL database ready!")
    except Exception as e:
        print(f"[AURA] DB setup warning: {e}")

SECRET_KEY = os.getenv("AURA_SECRET_KEY", "aura-3g2b-2025")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60 * 8

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# ─── REQUEST MODELS ───────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    monthly_income: Optional[float] = 0

class TransactionRequest(BaseModel):
    category: str
    description: str
    amount: float
    date: Optional[str] = None

class GoalUpdateRequest(BaseModel):
    savings_goal: Optional[float] = None
    current_savings: Optional[float] = None
    goal_deadline: Optional[str] = None

class BudgetUpdateRequest(BaseModel):
    category: str
    new_budget: float

class AgentRunRequest(BaseModel):
    user_prompt: Optional[str] = "Analyze my finances and optimize savings."


# ─── AUTH HELPERS ─────────────────────────────────────────────────────────────

def create_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    exc = HTTPException(status_code=401, detail="Invalid credentials",
                        headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise exc
    except JWTError:
        raise exc
    user = get_user_by_id(int(user_id))
    if not user:
        raise exc
    return user


# ─── AUTH ROUTES ──────────────────────────────────────────────────────────────

@app.post("/auth/register")
def register(req: RegisterRequest):
    result = create_user(req.username, req.email, req.password,
                         req.full_name, req.monthly_income)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    token = create_token({"sub": str(result["user_id"])})
    user_data = get_user_by_id(result["user_id"])
    return {"access_token": token, "token_type": "bearer",
            "user": {"username": req.username, "full_name": req.full_name, "user_id": result["user_id"], "monthly_income": req.monthly_income or 0}}

@app.post("/auth/token")
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_username(form.username)
    if not user or not verify_password(form.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = create_token({"sub": str(user["id"])})
    return {"access_token": token, "token_type": "bearer",
            "user": {"username": user["username"], "full_name": user["full_name"],
                     "user_id": user["id"], "monthly_income": float(user.get("monthly_income") or 0)}}

@app.get("/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


# ─── GOAL ROUTES ──────────────────────────────────────────────────────────────

@app.get("/api/goal")
def get_goal(current_user: dict = Depends(get_current_user)):
    goal = get_user_goal(current_user["id"])
    if not goal:
        raise HTTPException(status_code=404, detail="No goal found")
    return goal

@app.post("/api/goal/update")
def update_goal(req: GoalUpdateRequest, current_user: dict = Depends(get_current_user)):
    return update_user_goal(
        current_user["id"],
        req.savings_goal,
        req.current_savings,
        req.goal_deadline
    )


# ─── TRANSACTION ROUTES ───────────────────────────────────────────────────────

@app.post("/api/transactions/add")
def add_expense(req: TransactionRequest, current_user: dict = Depends(get_current_user)):
    result = add_transaction(
        current_user["id"], req.category,
        req.description, req.amount, req.date
    )
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result

@app.get("/api/transactions")
def list_transactions(month: Optional[str] = None,
                      current_user: dict = Depends(get_current_user)):
    txns = get_transactions(current_user["id"], month)
    return {"transactions": txns}

@app.get("/api/transactions/summary")
def transaction_summary(month: Optional[str] = None,
                        current_user: dict = Depends(get_current_user)):
    month = month or datetime.now().strftime("%Y-%m")
    spend = get_spend_by_category(current_user["id"], month)
    budgets = get_budgets(current_user["id"])
    goal = get_user_goal(current_user["id"])

    summary = []
    for cat, budget in budgets.items():
        spent = spend.get(cat, 0)
        summary.append({
            "category": cat,
            "budget": budget,
            "spent": spent,
            "remaining": budget - spent,
            "pct_used": round((spent / budget * 100) if budget > 0 else 0, 1),
            "overspent": spent > budget
        })

    return {
        "month": month,
        "summary": summary,
        "total_spent": sum(spend.values()),
        "total_budget": sum(budgets.values()),
        "goal": goal
    }


# ─── BUDGET ROUTES ────────────────────────────────────────────────────────────

@app.get("/api/budgets")
def list_budgets(current_user: dict = Depends(get_current_user)):
    return {"budgets": get_budgets(current_user["id"])}

@app.post("/api/budgets/update")
def update_budget_route(req: BudgetUpdateRequest,
                        current_user: dict = Depends(get_current_user)):
    return update_budget(current_user["id"], req.category, req.new_budget)


# ─── NOTIFICATION ROUTES ──────────────────────────────────────────────────────

@app.get("/api/notifications")
def list_notifications(unread_only: bool = False,
                       current_user: dict = Depends(get_current_user)):
    notifs = get_notifications(current_user["id"], unread_only)
    return {"notifications": notifs, "unread_count": sum(1 for n in notifs if not n["is_read"])}

@app.post("/api/notifications/read")
def read_notifications(current_user: dict = Depends(get_current_user)):
    return mark_notifications_read(current_user["id"])


# ─── AGENT ROUTE ──────────────────────────────────────────────────────────────

@app.post("/api/agent/run")
def run_agent(req: AgentRunRequest, current_user: dict = Depends(get_current_user)):
    from database.mysql_db import get_user_goal, get_spend_by_category, get_budgets
    from datetime import datetime

    user_id = current_user["id"]
    goal = get_user_goal(user_id)
    month = datetime.now().strftime("%Y-%m")
    spend = get_spend_by_category(user_id, month)
    budgets = get_budgets(user_id)

    user_context = {
        "name": current_user.get("full_name") or current_user.get("username") or "User",
        "monthly_income": float(current_user.get("monthly_income") or 0),
        "current_savings": float(goal.get("current_savings") or 0) if goal else 0,
        "savings_goal": float(goal.get("savings_goal") or 0) if goal else 0,
        "goal_deadline": str(goal.get("goal_deadline") or "") if goal else "",
        "spend_by_category": spend,
        "budgets": budgets,
    }

    result = run_agent_workflow(req.user_prompt, user_context=user_context)
    return result


# ─── LEGACY ROUTES (backward compat) ─────────────────────────────────────────

@app.get("/")
def root():
    return {"engine": "Aura Core Engine", "version": "2.0.0", "status": "online"}

@app.get("/api/tools/fetch")
def tool_fetch():
    return fetch_data()

@app.get("/api/tools/analyze")
def tool_analyze():
    return analyze_trends()