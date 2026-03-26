"""
backend/tools.py
Aura — Backend Tool Suite (Reet's Domain)
fetch_data(), analyze_trends(), execute_action()
These are the callable tools invoked by the LangGraph agent.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database import db
from collections import defaultdict
from typing import Any


# ─── TOOL 1: fetch_data ────────────────────────────────────────────────────────

def fetch_data() -> dict:
    """
    Reads the full ledger and returns a structured snapshot
    including the savings gap and per-category spend totals.
    """
    ledger = db.get_ledger()
    profile = ledger["user_profile"]
    transactions = ledger["transactions"]
    budget = ledger["budget"]
    subscriptions = ledger["subscriptions"]

    # Aggregate spending by category
    spend_by_category = defaultdict(float)
    for txn in transactions:
        spend_by_category[txn["category"]] += txn["amount"]

    # Compute savings gap
    savings_gap = profile["savings_goal"] - profile["current_savings"]
    savings_pct = round(profile["current_savings"] / profile["savings_goal"] * 100, 1)

    # Total monthly spend
    total_spent = sum(spend_by_category.values())
    total_budget = sum(budget.values())

    return {
        "user_profile": profile,
        "savings_gap": savings_gap,
        "savings_pct": savings_pct,
        "total_spent": total_spent,
        "total_budget": total_budget,
        "spend_by_category": dict(spend_by_category),
        "budget": budget,
        "subscriptions": subscriptions,
        "transactions_count": len(transactions),
    }


# ─── TOOL 2: analyze_trends ───────────────────────────────────────────────────

def analyze_trends() -> dict:
    """
    Identifies overspending categories, unused subscriptions,
    and calculates potential monthly savings.
    Returns a structured analysis for the agent's reasoning loop.
    """
    data = fetch_data()
    spend = data["spend_by_category"]
    budget = data["budget"]
    subs = data["subscriptions"]

    overspend = []
    underspend = []

    for category, budgeted in budget.items():
        actual = spend.get(category, 0)
        diff = actual - budgeted
        pct_over = round((diff / budgeted) * 100, 1) if budgeted > 0 else 0

        if diff > 0:
            overspend.append({
                "category": category,
                "budgeted": budgeted,
                "actual": actual,
                "overspend_amount": diff,
                "overspend_pct": pct_over,
                "severity": "high" if pct_over > 30 else "medium" if pct_over > 10 else "low"
            })
        else:
            underspend.append({
                "category": category,
                "budgeted": budgeted,
                "actual": actual,
                "savings_potential": abs(diff)
            })

    # Sort by overspend amount descending
    overspend.sort(key=lambda x: x["overspend_amount"], reverse=True)

    # Flag unused/low-use subscriptions (unused > 14 days)
    flagged_subs = [
        s for s in subs
        if s.get("days_since_use", 0) > 14 and s["status"] != "cancel"
    ]

    total_overspend = sum(o["overspend_amount"] for o in overspend)
    total_sub_waste = sum(s["amount"] for s in flagged_subs)
    total_recoverable = total_overspend + total_sub_waste

    return {
        "overspend_categories": overspend,
        "underspend_categories": underspend,
        "flagged_subscriptions": flagged_subs,
        "total_monthly_overspend": total_overspend,
        "total_subscription_waste": total_sub_waste,
        "total_recoverable_monthly": total_recoverable,
        "savings_gap": data["savings_gap"],
        "months_to_goal_current": round(data["savings_gap"] / max(data["user_profile"]["monthly_income"] - data["total_spent"], 1)),
        "months_to_goal_optimized": round(data["savings_gap"] / max(data["user_profile"]["monthly_income"] - data["total_spent"] + total_recoverable, 1)),
    }


# ─── TOOL 3: execute_action ───────────────────────────────────────────────────

def execute_action(action_type: str, **kwargs) -> dict:
    """
    Executes an autonomous corrective action on the ledger.

    action_type options:
      - "budget_cut"      : kwargs: category (str), new_budget (float)
      - "sub_cancel"      : kwargs: sub_id (str)
      - "sub_flag"        : kwargs: sub_id (str)
      - "savings_update"  : kwargs: amount (float)

    Returns execution result dict with status, detail, and impact.
    """
    results = []

    if action_type == "budget_cut":
        category = kwargs.get("category")
        new_budget = kwargs.get("new_budget")
        if not category or new_budget is None:
            return {"status": "error", "message": "category and new_budget required"}

        current_budget = db.get_budget().get(category, 0)
        savings = current_budget - new_budget
        result = db.update_budget(category, new_budget)
        result["monthly_savings"] = savings
        result["action_type"] = "budget_cut"
        return result

    elif action_type == "sub_cancel":
        sub_id = kwargs.get("sub_id")
        if not sub_id:
            return {"status": "error", "message": "sub_id required"}
        subs = db.get_subscriptions()
        sub = next((s for s in subs if s["id"] == sub_id), None)
        if not sub:
            return {"status": "error", "message": f"Subscription {sub_id} not found"}
        result = db.flag_subscription(sub_id, "cancel")
        result["monthly_savings"] = sub["amount"]
        result["action_type"] = "sub_cancel"
        return result

    elif action_type == "sub_flag":
        sub_id = kwargs.get("sub_id")
        if not sub_id:
            return {"status": "error", "message": "sub_id required"}
        result = db.flag_subscription(sub_id, "flagged")
        result["action_type"] = "sub_flag"
        return result

    elif action_type == "savings_update":
        amount = kwargs.get("amount")
        if amount is None:
            return {"status": "error", "message": "amount required"}
        result = db.update_savings(amount)
        result["action_type"] = "savings_update"
        return result

    else:
        return {"status": "error", "message": f"Unknown action_type: {action_type}"}


# ─── TOOL REGISTRY (for LangGraph / API exposure) ────────────────────────────

TOOL_REGISTRY = {
    "fetch_data": fetch_data,
    "analyze_trends": analyze_trends,
    "execute_action": execute_action,
}


if __name__ == "__main__":
    print("=== fetch_data ===")
    data = fetch_data()
    print(f"  Savings Gap: ₹{data['savings_gap']:,}")
    print(f"  Total Spent: ₹{data['total_spent']:,}")

    print("\n=== analyze_trends ===")
    trends = analyze_trends()
    print(f"  Overspend categories: {len(trends['overspend_categories'])}")
    print(f"  Total recoverable: ₹{trends['total_recoverable_monthly']:,}")
    for o in trends["overspend_categories"]:
        print(f"    {o['category']}: +₹{o['overspend_amount']} ({o['overspend_pct']}% over)")
