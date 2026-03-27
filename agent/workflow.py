"""
agent/workflow.py
Aura — LangGraph State Machine (Prathamesh's Domain)
Nodes: [Analyze] → [Plan] → [Review] → [Execute]
Now powered by NVIDIA Nemotron via OpenRouter for real AI reasoning.
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from typing import TypedDict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─── LangGraph ────────────────────────────────────────────────────────────────
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

# ─── OpenRouter (NVIDIA Nemotron) ────────────────────────────────────────────
import requests as _requests
CLAUDE_AVAILABLE = bool(os.getenv("OPENROUTER_API_KEY"))

from backend.tools import fetch_data, analyze_trends, execute_action


# ─── STATE SCHEMA ─────────────────────────────────────────────────────────────

class AuraState(TypedDict):
    user_prompt: str
    user_name: str
    snapshot: dict
    analysis: dict
    thought: str
    plan: List[str]
    actions_proposed: List[dict]
    actions_executed: List[dict]
    pending_approvals: List[dict]
    ui_message: str
    node_trace: List[str]
    error: Optional[str]


# ─── AI HELPER (OpenRouter with fallback models) ─────────────────────────────

# Try models in order until one works
FALLBACK_MODELS = [
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "nvidia/nemotron-nano-9b-v2:free",
    "google/gemma-3-27b-it:free",
]

def ask_claude(system_prompt: str, user_message: str, max_tokens: int = 1024) -> str:
    """Call LLM via OpenRouter with automatic model fallback."""
    if not CLAUDE_AVAILABLE:
        return None

    for model in FALLBACK_MODELS:
        try:
            response = _requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": "Bearer " + os.getenv("OPENROUTER_API_KEY"),
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "Aura Wealth Pilot"
                },
                json={
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ]
                },
                timeout=30
            )
            data = response.json()
            if "choices" in data:
                print(f"[AURA] AI response from: {model}")
                return data["choices"][0]["message"]["content"]
            elif "error" in data and data["error"].get("code") == 429:
                print(f"[AURA] {model} rate limited, trying next...")
                continue
            else:
                print(f"[AURA] {model} error: {data.get('error', 'unknown')}")
                continue
        except Exception as e:
            print(f"[AURA] {model} exception: {e}")
            continue

    print("[AURA] All models exhausted, using rule-based fallback.")
    return None


# ─── NODE 1: ANALYZE ──────────────────────────────────────────────────────────

def node_analyze(state: AuraState) -> AuraState:
    print("[AURA] → NODE: ANALYZE")
    state["node_trace"].append("ANALYZE")

    # Use MySQL data if already loaded, else fall back to ledger.json
    if state["snapshot"] and state["snapshot"].get("user_profile"):
        snapshot = state["snapshot"]
        # Build analysis from MySQL spend data
        spend = snapshot.get("spend_by_category", {})
        budget = snapshot.get("budget", {})
        overspend_cats = []
        for cat, bgt in budget.items():
            spent = spend.get(cat, 0)
            if spent > bgt:
                pct_over = round((spent - bgt) / bgt * 100, 1) if bgt > 0 else 0
                overspend_cats.append({
                    "category": cat, "budgeted": bgt, "actual": spent,
                    "overspend_amount": spent - bgt, "overspend_pct": pct_over,
                    "severity": "high" if pct_over > 30 else "medium" if pct_over > 10 else "low"
                })
        overspend_cats.sort(key=lambda x: x["overspend_amount"], reverse=True)
        analysis = {
            "overspend_categories": overspend_cats,
            "underspend_categories": [],
            "flagged_subscriptions": [],
            "total_monthly_overspend": sum(o["overspend_amount"] for o in overspend_cats),
            "total_subscription_waste": 0,
            "total_recoverable_monthly": sum(o["overspend_amount"] for o in overspend_cats),
            "savings_gap": snapshot.get("savings_gap", 0),
        }
        state["analysis"] = analysis
    else:
        snapshot = fetch_data()
        analysis = analyze_trends()
        state["snapshot"] = snapshot
        state["analysis"] = analysis

    gap = snapshot.get("savings_gap", 0)
    pct = snapshot.get("savings_pct", 0)
    profile = snapshot.get("user_profile", {})
    overspend_cats = state["analysis"].get("overspend_categories", [])
    flagged = state["analysis"].get("flagged_subscriptions", [])

    claude_thought = ask_claude(
        system_prompt=(
            "You are Aura, an autonomous AI wealth pilot. You analyse a user's financial data "
            "and reason deeply about their savings gap. Be concise, insightful, and specific. "
            "Respond in 2-3 sentences max. Use Rs for currency. No bullet points."
        ),
        user_message=(
            f"User: {state['user_name']}\n"
            f"Monthly income: Rs{profile['monthly_income']:,}\n"
            f"Current savings: Rs{profile['current_savings']:,} ({pct}% of goal)\n"
            f"Savings goal: Rs{profile['savings_goal']:,} by {profile['goal_deadline']}\n"
            f"Savings gap: Rs{gap:,}\n"
            f"Overspending in: {', '.join(o['category'] + ' (+Rs' + str(o['overspend_amount']) + ')' for o in overspend_cats)}\n"
            f"Flagged subscriptions: {', '.join(s['name'] + ' (unused ' + str(s['days_since_use']) + ' days)' for s in flagged)}\n"
            f"User prompt: {state['user_prompt']}\n\n"
            "Describe what you observe about this user's financial situation."
        )
    )

    state["thought"] = claude_thought or (
        f"Fetched ledger via fetch_data(). "
        f"Current savings: Rs{profile['current_savings']:,} ({pct}% of goal). "
        f"Savings gap: Rs{gap:,}. "
        f"Detected overspending in: {', '.join(o['category'] for o in overspend_cats) or 'none'}. "
        f"Total monthly leak: Rs{analysis['total_monthly_overspend']:,}. "
        f"Flagged subscriptions: {len(flagged)}."
    )

    return state


# ─── NODE 2: PLAN ─────────────────────────────────────────────────────────────

def node_plan(state: AuraState) -> AuraState:
    print("[AURA] → NODE: PLAN")
    state["node_trace"].append("PLAN")

    analysis = state["analysis"]
    overspend = analysis["overspend_categories"]
    flagged = analysis["flagged_subscriptions"]

    proposed_actions = []
    plan_steps = []

    if overspend:
        top = overspend[0]
        recommended_budget = round(top["budgeted"] * 0.85)
        savings = top["budgeted"] - recommended_budget
        proposed_actions.append({
            "id": "act_001", "type": "budget_cut",
            "label": f"Reduce {top['category']} budget",
            "category": top["category"], "new_budget": recommended_budget,
            "monthly_savings": savings, "auto_execute": savings <= 10000,
            "severity": top["severity"]
        })
        plan_steps.append(f"Cut {top['category']} budget from Rs{top['budgeted']:,} to Rs{recommended_budget:,} (saves Rs{savings:,}/mo)")

    if len(overspend) > 1:
        second = overspend[1]
        rec2 = round(second["budgeted"] * 0.90)
        savings2 = second["budgeted"] - rec2
        proposed_actions.append({
            "id": "act_002", "type": "budget_cut",
            "label": f"Cap {second['category']} budget",
            "category": second["category"], "new_budget": rec2,
            "monthly_savings": savings2, "auto_execute": savings2 <= 10000,
            "severity": second["severity"]
        })
        plan_steps.append(f"Cap {second['category']} budget at Rs{rec2:,} (saves Rs{savings2:,}/mo)")

    if flagged:
        worst_sub = max(flagged, key=lambda s: s["amount"])
        proposed_actions.append({
            "id": "act_003", "type": "sub_cancel",
            "label": f"Cancel {worst_sub['name']} (unused {worst_sub['days_since_use']} days)",
            "sub_id": worst_sub["id"], "sub_name": worst_sub["name"],
            "monthly_savings": worst_sub["amount"],
            "auto_execute": worst_sub["amount"] <= 100,
            "days_since_use": worst_sub["days_since_use"]
        })
        plan_steps.append(f"Cancel {worst_sub['name']} (Rs{worst_sub['amount']}/mo, unused {worst_sub['days_since_use']} days)")

    state["actions_proposed"] = proposed_actions
    state["plan"] = plan_steps

    total_recoverable = sum(a["monthly_savings"] for a in proposed_actions)

    claude_plan_thought = ask_claude(
        system_prompt=(
            "You are Aura, an autonomous AI wealth pilot. Given a financial analysis and proposed actions, "
            "explain your planning reasoning in 2 sentences. Be specific, use Rs. No bullet points."
        ),
        user_message=(
            f"Proposed actions:\n" +
            "\n".join(f"- {s}" for s in plan_steps) +
            f"\nTotal recoverable: Rs{total_recoverable:,}/month\n"
            f"Savings gap: Rs{state['snapshot']['savings_gap']:,}\n\n"
            "Explain why you chose these actions and their impact."
        )
    )

    state["thought"] += " | " + (claude_plan_thought or
        f"PLAN: {len(proposed_actions)} corrective tasks identified. Total recoverable: Rs{total_recoverable:,}/mo.")

    return state


# ─── NODE 3: REVIEW ───────────────────────────────────────────────────────────

def node_review(state: AuraState) -> AuraState:
    print("[AURA] → NODE: REVIEW")
    state["node_trace"].append("REVIEW")

    auto_actions, pending = [], []
    for action in state["actions_proposed"]:
        if action["auto_execute"]:
            auto_actions.append(action)
        else:
            pending.append({**action, "requires_approval": True,
                            "reason": f"Impact > Rs100/mo (Rs{action['monthly_savings']:,})"})

    state["actions_proposed"] = auto_actions
    state["pending_approvals"] = pending
    state["thought"] += (
        f" | REVIEW: {len(auto_actions)} actions cleared for auto-execution. "
        f"{len(pending)} routed to Human-in-the-Loop."
    )
    return state


# ─── NODE 4: EXECUTE ──────────────────────────────────────────────────────────

def node_execute(state: AuraState) -> AuraState:
    print("[AURA] → NODE: EXECUTE")
    state["node_trace"].append("EXECUTE")

    executed = []
    for action in state["actions_proposed"]:
        if action["type"] == "budget_cut":
            result = execute_action("budget_cut", category=action["category"], new_budget=action["new_budget"])
        elif action["type"] == "sub_cancel":
            result = execute_action("sub_cancel", sub_id=action["sub_id"])
        else:
            result = {"status": "skipped"}
        executed.append({**action, "result": result})

    state["actions_executed"] = executed

    total_saved = sum(a["monthly_savings"] for a in executed if a.get("result", {}).get("status") == "success")
    pending_total = sum(a["monthly_savings"] for a in state["pending_approvals"])
    actions_done = len(executed)
    pending_count = len(state["pending_approvals"])
    pending_names = ", ".join(a.get("sub_name", a.get("category", "item")) for a in state["pending_approvals"])

    claude_message = ask_claude(
        system_prompt=(
            "You are Aura, a friendly autonomous wealth pilot. Write a short, encouraging 1-2 sentence "
            "message to the user summarising what you just did. Be specific with numbers. Use Rs."
        ),
        user_message=(
            f"Actions executed: {actions_done} (saved Rs{total_saved:,}/month automatically)\n"
            f"Pending approvals: {pending_count} ({pending_names}) - potential Rs{pending_total:,}/month\n"
            f"User's savings gap: Rs{state['snapshot'].get('savings_gap', 0):,}\n\n"
            "Write the UI message for the user."
        )
    )

    fallback_parts = []
    if actions_done > 0:
        fallback_parts.append(f"I've autonomously applied {actions_done} budget optimization(s), recovering Rs{total_saved:,}/month.")
    if pending_count > 0:
        fallback_parts.append(f"{pending_count} action(s) need your approval ({pending_names}) - potential Rs{pending_total:,}/month saved.")
    if not fallback_parts:
        fallback_parts.append("Your finances look well-optimized this month. Keep it up!")

    state["ui_message"] = claude_message or " ".join(fallback_parts)
    state["thought"] += (
        f" | EXECUTE: {actions_done} action(s) executed. "
        f"Rs{total_saved:,} saved/mo. {pending_count} pending approval."
    )

    return state


# ─── GRAPH BUILDER ────────────────────────────────────────────────────────────

def build_graph():
    if not LANGGRAPH_AVAILABLE:
        return None
    graph = StateGraph(AuraState)
    graph.add_node("node_analyze", node_analyze)
    graph.add_node("node_plan", node_plan)
    graph.add_node("node_review", node_review)
    graph.add_node("node_execute", node_execute)
    graph.set_entry_point("node_analyze")
    graph.add_edge("node_analyze", "node_plan")
    graph.add_edge("node_plan", "node_review")
    graph.add_edge("node_review", "node_execute")
    graph.add_edge("node_execute", END)
    return graph.compile()


# ─── PUBLIC RUNNER ────────────────────────────────────────────────────────────

def run_agent_workflow(user_prompt: str = "Analyze my finances.", user_name: str = "User") -> dict:
    print(f"[AURA] Claude available: {CLAUDE_AVAILABLE}")

    initial_state: AuraState = {
        "user_prompt": user_prompt,
        "user_name": user_name,
        "snapshot": {}, "analysis": {},
        "thought": "", "plan": [],
        "actions_proposed": [], "actions_executed": [],
        "pending_approvals": [], "ui_message": "",
        "node_trace": [], "error": None
    }

    if LANGGRAPH_AVAILABLE:
        app = build_graph()
        final_state = app.invoke(initial_state)
    else:
        print("[AURA] LangGraph not installed - running nodes manually.")
        state = initial_state
        for node_fn in [node_analyze, node_plan, node_review, node_execute]:
            state = node_fn(state)
        final_state = state

    return {
        "THOUGHT": final_state["thought"],
        "PLAN": final_state["plan"],
        "ACTION": final_state["actions_executed"],
        "PENDING_APPROVALS": final_state["pending_approvals"],
        "UI_MESSAGE": final_state["ui_message"],
        "node_trace": final_state["node_trace"],
        "timestamp": datetime.now().isoformat(),
        "ai_powered": CLAUDE_AVAILABLE
    }