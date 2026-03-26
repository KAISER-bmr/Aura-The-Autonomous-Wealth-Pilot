"""
database/db.py
Aura — JSON Ledger Manager (Gokul's Domain)
Handles all read/write operations to ledger.json
"""

import json
import os
from datetime import datetime
from typing import Any

LEDGER_PATH = os.path.join(os.path.dirname(__file__), "ledger.json")


def _load() -> dict:
    """Load the full ledger from disk."""
    with open(LEDGER_PATH, "r") as f:
        return json.load(f)


def _save(data: dict) -> None:
    """Persist the ledger back to disk."""
    with open(LEDGER_PATH, "w") as f:
        json.dump(data, f, indent=2)


# ─── READ OPERATIONS ───────────────────────────────────────────────────────────

def get_ledger() -> dict:
    """Return the full ledger."""
    return _load()


def get_user_profile() -> dict:
    return _load()["user_profile"]


def get_transactions() -> list:
    return _load()["transactions"]


def get_budget() -> dict:
    return _load()["budget"]


def get_subscriptions() -> list:
    return _load()["subscriptions"]


def get_agent_actions() -> list:
    return _load()["agent_actions"]


# ─── WRITE OPERATIONS ──────────────────────────────────────────────────────────

def update_budget(category: str, new_amount: float) -> dict:
    """Update the budget for a category."""
    data = _load()
    old_amount = data["budget"].get(category, 0)
    data["budget"][category] = new_amount
    _log_action(data, {
        "type": "budget_update",
        "category": category,
        "old_value": old_amount,
        "new_value": new_amount,
        "timestamp": datetime.now().isoformat()
    })
    _save(data)
    return {"status": "success", "category": category, "new_budget": new_amount}


def flag_subscription(sub_id: str, action: str) -> dict:
    """Flag or cancel a subscription. action: 'flag' | 'cancel' | 'keep'"""
    data = _load()
    for sub in data["subscriptions"]:
        if sub["id"] == sub_id:
            old_status = sub["status"]
            sub["status"] = action
            _log_action(data, {
                "type": "subscription_action",
                "sub_id": sub_id,
                "sub_name": sub["name"],
                "old_status": old_status,
                "new_status": action,
                "amount_saved": sub["amount"] if action == "cancel" else 0,
                "timestamp": datetime.now().isoformat()
            })
            _save(data)
            return {"status": "success", "subscription": sub["name"], "action": action}
    return {"status": "error", "message": f"Subscription {sub_id} not found"}


def update_savings(new_amount: float) -> dict:
    """Update current savings value."""
    data = _load()
    old = data["user_profile"]["current_savings"]
    data["user_profile"]["current_savings"] = new_amount
    _log_action(data, {
        "type": "savings_update",
        "old_value": old,
        "new_value": new_amount,
        "timestamp": datetime.now().isoformat()
    })
    _save(data)
    return {"status": "success", "new_savings": new_amount}


def add_transaction(category: str, description: str, amount: float) -> dict:
    """Add a new transaction to the ledger."""
    data = _load()
    txn_id = f"txn_{len(data['transactions']) + 1:03d}"
    txn = {
        "id": txn_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "category": category,
        "description": description,
        "amount": amount,
        "type": "debit"
    }
    data["transactions"].append(txn)
    _save(data)
    return {"status": "success", "transaction": txn}


def _log_action(data: dict, action: dict) -> None:
    """Append an action to the agent_actions log."""
    data["agent_actions"].append(action)
