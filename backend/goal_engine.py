"""
backend/goal_engine.py
Aura — Goal-Setting & Forecasting Engine
Computes projections, milestones, and deadline risk for the agent's planning loop.
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database import db
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import List, Dict


# ─── CORE FORECASTING ─────────────────────────────────────────────────────────

def compute_goal_forecast(monthly_savings_rate: float = None) -> Dict:
    """
    Projects how long until the savings goal is reached.
    Computes 3 scenarios: pessimistic, current, optimistic.

    Returns milestone schedule and deadline risk flag.
    """
    profile = db.get_user_profile()
    budget  = db.get_budget()

    current_savings = profile["current_savings"]
    savings_goal    = profile["savings_goal"]
    monthly_income  = profile["monthly_income"]
    deadline_str    = profile.get("goal_deadline", "2025-12-31")
    deadline        = date.fromisoformat(deadline_str)
    today           = date.today()

    total_budget = sum(budget.values())

    # Default rate = income minus total budget
    if monthly_savings_rate is None:
        monthly_savings_rate = max(monthly_income - total_budget, 1)

    gap = savings_goal - current_savings

    # Three scenarios
    pessimistic_rate  = monthly_savings_rate * 0.75
    current_rate      = monthly_savings_rate
    optimistic_rate   = monthly_savings_rate * 1.25

    def months_to_goal(rate):
        return gap / rate if rate > 0 else float("inf")

    def reach_date(months):
        if months == float("inf"):
            return None
        return today + relativedelta(months=int(months) + 1)

    pess_months = months_to_goal(pessimistic_rate)
    curr_months = months_to_goal(current_rate)
    opti_months = months_to_goal(optimistic_rate)

    pess_date = reach_date(pess_months)
    curr_date = reach_date(curr_months)
    opti_date = reach_date(opti_months)

    # Deadline risk
    on_track        = curr_date is not None and curr_date <= deadline
    months_to_deadline = (deadline.year - today.year) * 12 + (deadline.month - today.month)
    deadline_gap_months = curr_months - months_to_deadline  # positive = behind schedule

    # Monthly milestones — next 6 months
    milestones = []
    for i in range(1, 7):
        projected = current_savings + current_rate * i
        projected_pct = min(round(projected / savings_goal * 100, 1), 100)
        milestone_date = today + relativedelta(months=i)
        milestones.append({
            "month": milestone_date.strftime("%b %Y"),
            "projected_savings": round(projected),
            "projected_pct": projected_pct,
            "on_track": projected_pct <= 100
        })

    return {
        "current_savings":        current_savings,
        "savings_goal":           savings_goal,
        "gap":                    gap,
        "gap_pct":                round(gap / savings_goal * 100, 1),
        "monthly_savings_rate":   round(current_rate),
        "scenarios": {
            "pessimistic": {
                "monthly_rate":  round(pessimistic_rate),
                "months_to_goal": round(pess_months, 1),
                "reach_date":    pess_date.isoformat() if pess_date else None,
            },
            "current": {
                "monthly_rate":  round(current_rate),
                "months_to_goal": round(curr_months, 1),
                "reach_date":    curr_date.isoformat() if curr_date else None,
            },
            "optimistic": {
                "monthly_rate":  round(optimistic_rate),
                "months_to_goal": round(opti_months, 1),
                "reach_date":    opti_date.isoformat() if opti_date else None,
            }
        },
        "deadline":              deadline_str,
        "months_to_deadline":    months_to_deadline,
        "on_track":              on_track,
        "deadline_slip_months":  round(max(deadline_gap_months, 0), 1),
        "milestones":            milestones,
    }


def set_savings_goal(new_goal: float, new_deadline: str = None) -> Dict:
    """Update the savings goal and/or deadline."""
    data = db.get_ledger()
    old_goal = data["user_profile"]["savings_goal"]
    data["user_profile"]["savings_goal"] = new_goal
    if new_deadline:
        data["user_profile"]["goal_deadline"] = new_deadline
    db._save(data)
    return {
        "status": "success",
        "old_goal": old_goal,
        "new_goal": new_goal,
        "new_deadline": new_deadline or data["user_profile"]["goal_deadline"]
    }


def compute_required_monthly_savings() -> Dict:
    """
    Calculate how much the user MUST save per month to hit
    the goal exactly by the deadline.
    """
    profile  = db.get_user_profile()
    gap      = profile["savings_goal"] - profile["current_savings"]
    deadline = date.fromisoformat(profile.get("goal_deadline", "2025-12-31"))
    today    = date.today()
    months   = max((deadline.year - today.year) * 12 + (deadline.month - today.month), 1)
    required = round(gap / months)
    current_capacity = profile["monthly_income"] - sum(db.get_budget().values())

    return {
        "required_monthly_savings": required,
        "current_monthly_capacity": round(current_capacity),
        "shortfall_per_month":      max(required - current_capacity, 0),
        "surplus_per_month":        max(current_capacity - required, 0),
        "months_remaining":         months,
        "feasible":                 current_capacity >= required
    }


if __name__ == "__main__":
    fc = compute_goal_forecast()
    print(f"On track: {fc['on_track']}")
    print(f"Current scenario reaches goal: {fc['scenarios']['current']['reach_date']}")
    print(f"Deadline slip: {fc['deadline_slip_months']} months")
    req = compute_required_monthly_savings()
    print(f"Required savings/month: ₹{req['required_monthly_savings']:,}")
    print(f"Feasible: {req['feasible']}")
