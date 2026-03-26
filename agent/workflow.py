"""
agent/workflow.py
Aura — LangGraph State Machine (Prathamesh's Domain)
Nodes: [Analyze] → [Plan] → [Review] → [Execute]
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from typing import TypedDict, Annotated, List, Optional
from datetime import datetime

# LangGraph imports (install: pip install langgraph)
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

from backend.tools import fetch_data, analyze_trends, execute_action


# ─── STATE SCHEMA ─────────────────────────────────────────────────────────────

class AuraState(TypedDict):
    user_prompt: str
    snapshot: dict           # from fetch_data()
    analysis: dict           # from analyze_trends()
    thought: str             # [THOUGHT] block
    plan: List[str]          # [PLAN] block
    actions_proposed: List[dict]
    actions_executed: List[dict]
    pending_approvals: List[dict]
    ui_message: str          # [UI_MESSAGE] block
    node_trace: List[str]    # which nodes ran
    error: Optional[str]


# ─── NODE 1: ANALYZE ──────────────────────────────────────────────────────────

def node_analyze(state: AuraState) -> AuraState:
    """
    Observation: Fetch data and identify the savings gap.
    """
    print("[AURA] → NODE: ANALYZE")
    state["node_trace"].append("ANALYZE")

    snapshot = fetch_data()
    analysis = analyze_trends()

    state["snapshot"] = snapshot
    state["analysis"] = analysis

    gap = snapshot["savings_gap"]
    pct = snapshot["savings_pct"]
    overspend_cats = [o["category"] for o in analysis["overspend_categories"]]

    state["thought"] = (
        f"Fetched ledger via fetch_data(). "
        f"Current savings: ₹{snapshot['user_profile']['current_savings']:,} "
        f"({pct}% of goal). "
        f"Savings gap: ₹{gap:,}. "
        f"Running analyze_trends() — detected overspending in: {', '.join(overspend_cats) or 'none'}. "
        f"Total monthly leak: ₹{analysis['total_monthly_overspend']:,}. "
        f"Flagged subscriptions: {len(analysis['flagged_subscriptions'])}."
    )

    return state


# ─── NODE 2: PLAN ─────────────────────────────────────────────────────────────

def node_plan(state: AuraState) -> AuraState:
    """
    Reasoning + Task Planning: Create 3 autonomous tasks to close the gap.
    """
    print("[AURA] → NODE: PLAN")
    state["node_trace"].append("PLAN")

    analysis = state["analysis"]
    overspend = analysis["overspend_categories"]
    flagged = analysis["flagged_subscriptions"]

    proposed_actions = []
    plan_steps = []

    # Task 1: Reduce top overspending category
    if overspend:
        top = overspend[0]
        recommended_budget = round(top["budgeted"] * 0.85)
        savings = top["budgeted"] - recommended_budget
        proposed_actions.append({
            "id": "act_001",
            "type": "budget_cut",
            "label": f"Reduce {top['category']} budget",
            "category": top["category"],
            "new_budget": recommended_budget,
            "monthly_savings": savings,
            "auto_execute": savings <= 10000,
            "severity": top["severity"]
        })
        plan_steps.append(
            f"Cut {top['category']} budget from ₹{top['budgeted']:,} → ₹{recommended_budget:,} "
            f"(saves ₹{savings:,}/mo, {top['overspend_pct']}% over budget)"
        )

    # Task 2: Reduce second overspend category if exists
    if len(overspend) > 1:
        second = overspend[1]
        rec2 = round(second["budgeted"] * 0.90)
        savings2 = second["budgeted"] - rec2
        proposed_actions.append({
            "id": "act_002",
            "type": "budget_cut",
            "label": f"Cap {second['category']} budget",
            "category": second["category"],
            "new_budget": rec2,
            "monthly_savings": savings2,
            "auto_execute": savings2 <= 10000,
            "severity": second["severity"]
        })
        plan_steps.append(
            f"Cap {second['category']} budget at ₹{rec2:,} "
            f"(saves ₹{savings2:,}/mo)"
        )

    # Task 3: Cancel highest-waste flagged subscription
    if flagged:
        worst_sub = max(flagged, key=lambda s: s["amount"])
        proposed_actions.append({
            "id": "act_003",
            "type": "sub_cancel",
            "label": f"Cancel {worst_sub['name']} (unused {worst_sub['days_since_use']} days)",
            "sub_id": worst_sub["id"],
            "sub_name": worst_sub["name"],
            "monthly_savings": worst_sub["amount"],
            "auto_execute": worst_sub["amount"] <= 100,   # Human-in-loop for >₹100
            "days_since_use": worst_sub["days_since_use"]
        })
        plan_steps.append(
            f"Cancel {worst_sub['name']} subscription "
            f"(₹{worst_sub['amount']}/mo, unused {worst_sub['days_since_use']} days)"
        )

    state["actions_proposed"] = proposed_actions
    state["plan"] = plan_steps

    total_recoverable = sum(a["monthly_savings"] for a in proposed_actions)
    state["thought"] += (
        f" | PLAN: {len(proposed_actions)} corrective tasks identified. "
        f"Total recoverable: ₹{total_recoverable:,}/mo. "
        f"Highest impact: {proposed_actions[0]['label'] if proposed_actions else 'none'}."
    )

    return state


# ─── NODE 3: REVIEW ───────────────────────────────────────────────────────────

def node_review(state: AuraState) -> AuraState:
    """
    Decision: Separate auto-executable actions from those needing human approval.
    Actions > ₹100 impact require Human-in-the-Loop.
    """
    print("[AURA] → NODE: REVIEW")
    state["node_trace"].append("REVIEW")

    auto_actions = []
    pending = []

    for action in state["actions_proposed"]:
        if action["auto_execute"]:
            auto_actions.append(action)
        else:
            pending.append({**action, "requires_approval": True, "reason": f"Impact > ₹100/mo (₹{action['monthly_savings']:,})"})

    state["actions_proposed"] = auto_actions
    state["pending_approvals"] = pending

    state["thought"] += (
        f" | REVIEW: {len(auto_actions)} actions cleared for auto-execution. "
        f"{len(pending)} action(s) routed to Human-in-the-Loop approval."
    )

    return state


# ─── NODE 4: EXECUTE ──────────────────────────────────────────────────────────

def node_execute(state: AuraState) -> AuraState:
    """
    Execution: Run all auto-approved actions via execute_action().
    Log results. Build final UI message.
    """
    print("[AURA] → NODE: EXECUTE")
    state["node_trace"].append("EXECUTE")

    executed = []

    for action in state["actions_proposed"]:
        if action["type"] == "budget_cut":
            result = execute_action(
                "budget_cut",
                category=action["category"],
                new_budget=action["new_budget"]
            )
        elif action["type"] == "sub_cancel":
            result = execute_action("sub_cancel", sub_id=action["sub_id"])
        else:
            result = {"status": "skipped"}

        executed.append({**action, "result": result})

    state["actions_executed"] = executed

    # Build UI message
    total_saved = sum(a["monthly_savings"] for a in executed if a.get("result", {}).get("status") == "success")
    pending_total = sum(a["monthly_savings"] for a in state["pending_approvals"])
    actions_done = len(executed)
    pending_count = len(state["pending_approvals"])

    msg_parts = []
    if actions_done > 0:
        msg_parts.append(f"I've autonomously applied {actions_done} budget optimization(s), recovering ₹{total_saved:,}/month.")
    if pending_count > 0:
        pending_names = ", ".join(a.get("sub_name", a.get("category", "item")) for a in state["pending_approvals"])
        msg_parts.append(f"{pending_count} action(s) need your approval ({pending_names}) — potential ₹{pending_total:,}/month saved.")
    if not msg_parts:
        msg_parts.append("Your finances look well-optimized this month. Keep it up!")

    state["ui_message"] = " ".join(msg_parts)

    state["thought"] += (
        f" | EXECUTE: {actions_done} action(s) executed successfully. "
        f"Total monthly savings applied: ₹{total_saved:,}. "
        f"{pending_count} pending human approval."
    )

    return state


# ─── GRAPH BUILDER ────────────────────────────────────────────────────────────

def build_graph():
    if not LANGGRAPH_AVAILABLE:
        return None

    graph = StateGraph(AuraState)
    graph.add_node("analyze", node_analyze)
    graph.add_node("plan", node_plan)
    graph.add_node("review", node_review)
    graph.add_node("execute", node_execute)

    graph.set_entry_point("analyze")
    graph.add_edge("analyze", "plan")
    graph.add_edge("plan", "review")
    graph.add_edge("review", "execute")
    graph.add_edge("execute", END)

    return graph.compile()


# ─── PUBLIC RUNNER ────────────────────────────────────────────────────────────

def run_agent_workflow(user_prompt: str = "Analyze my finances.") -> dict:
    """
    Run the full Analyze → Plan → Review → Execute pipeline.
    Returns structured output compatible with frontend parsing.
    """
    initial_state: AuraState = {
        "user_prompt": user_prompt,
        "snapshot": {},
        "analysis": {},
        "thought": "",
        "plan": [],
        "actions_proposed": [],
        "actions_executed": [],
        "pending_approvals": [],
        "ui_message": "",
        "node_trace": [],
        "error": None
    }

    if LANGGRAPH_AVAILABLE:
        app = build_graph()
        final_state = app.invoke(initial_state)
    else:
        # Fallback: run nodes manually without LangGraph
        print("[AURA] LangGraph not installed — running nodes manually.")
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
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    result = run_agent_workflow("Optimize my savings for this month.")
    print("\n" + "="*60)
    print("[THOUGHT]\n", result["THOUGHT"])
    print("\n[PLAN]")
    for i, step in enumerate(result["PLAN"], 1):
        print(f"  {i}. {step}")
    print("\n[ACTION]")
    for a in result["ACTION"]:
        print(f"  • {a['label']} — {a.get('result', {}).get('status', 'unknown')}")
    print("\n[PENDING APPROVALS]")
    for p in result["PENDING_APPROVALS"]:
        print(f"  ⚠ {p['label']} — {p['reason']}")
    print("\n[UI_MESSAGE]\n", result["UI_MESSAGE"])
