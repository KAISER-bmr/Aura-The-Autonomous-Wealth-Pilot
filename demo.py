"""
demo.py
Aura — Terminal Demo Script
Runs the full agent loop and pretty-prints the output.
No API server needed. Run: python demo.py
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

from agent.workflow import run_agent_workflow
from backend.goal_engine import compute_goal_forecast, compute_required_monthly_savings
from backend.tools import fetch_data, analyze_trends

# ─── COLORS ───────────────────────────────────────────────────────────────────
C  = "\033[0m"       # reset
T  = "\033[38;5;43m" # teal  — #00f5c4 approx
B  = "\033[38;5;69m" # blue
Y  = "\033[38;5;214m"# yellow/orange
R  = "\033[38;5;204m"# red
W  = "\033[97m"      # white
G  = "\033[38;5;71m" # green
DIM= "\033[2m"

def hr(char="─", n=64, color=DIM): print(f"{color}{char*n}{C}")
def header(text): print(f"\n{T}{'▸ ' + text.upper()}{C}")
def kv(k, v, vc=W): print(f"  {DIM}{k:<28}{C}{vc}{v}{C}")

def typewrite(text, delay=0.012):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()

# ─── BANNER ───────────────────────────────────────────────────────────────────

print(f"""
{T}╔══════════════════════════════════════════════════════════════╗
║  ✦  AURA — AUTONOMOUS WEALTH PILOT                          ║
║     3G2B Team · Orchestron Competition 2025                 ║
╚══════════════════════════════════════════════════════════════╝{C}
""")

# ─── STEP 1: LOAD DATA ────────────────────────────────────────────────────────

header("Step 1 · Loading Ledger  →  fetch_data()")
hr()

snapshot = fetch_data()
profile  = snapshot["user_profile"]

kv("User",           profile["name"])
kv("Monthly Income", f"₹{profile['monthly_income']:,}")
kv("Current Savings",f"₹{profile['current_savings']:,}")
kv("Savings Goal",   f"₹{profile['savings_goal']:,}")
kv("Gap",            f"₹{snapshot['savings_gap']:,}", R)
kv("Progress",       f"{snapshot['savings_pct']}%", T)
kv("Total Spent",    f"₹{snapshot['total_spent']:,}", Y)

# ─── STEP 2: ANALYZE ──────────────────────────────────────────────────────────

header("Step 2 · Analyzing Trends  →  analyze_trends()")
hr()

trends = analyze_trends()
print(f"\n  {W}Overspending Categories:{C}")
for o in trends["overspend_categories"]:
    severity_color = R if o["severity"] == "high" else Y
    print(f"  {severity_color}▸{C} {o['category']:<20} over by {severity_color}₹{o['overspend_amount']:,}{C}  ({o['overspend_pct']}%  [{o['severity'].upper()}])")

print(f"\n  {W}Flagged Subscriptions:{C}")
for s in trends["flagged_subscriptions"]:
    print(f"  {Y}▸{C} {s['name']:<20} ₹{s['amount']}/mo  unused {s['days_since_use']} days")

kv("\n  Total Monthly Overspend", f"₹{trends['total_monthly_overspend']:,}", R)
kv("  Recoverable/month",       f"₹{trends['total_recoverable_monthly']:,}", T)

# ─── STEP 3: GOAL FORECAST ────────────────────────────────────────────────────

header("Step 3 · Goal Forecast  →  compute_goal_forecast()")
hr()

fc = compute_goal_forecast()
s  = fc["scenarios"]

print(f"\n  {'Scenario':<16} {'Rate/mo':>12}  {'Months':>8}  {'Reach Date':>12}")
print(f"  {DIM}{'─'*52}{C}")
for name, color in [("pessimistic", R), ("current", Y), ("optimistic", T)]:
    sc = s[name]
    rd = sc["reach_date"][:7] if sc["reach_date"] else "N/A"
    print(f"  {color}{name.capitalize():<16}{C}  ₹{sc['monthly_rate']:>9,}  {sc['months_to_goal']:>7.1f}m  {rd:>12}")

on_track_str = f"{G}✓ ON TRACK{C}" if fc["on_track"] else f"{R}✗ {fc['deadline_slip_months']}mo BEHIND{C}"
print(f"\n  Deadline ({fc['deadline']}):  {on_track_str}")

req = compute_required_monthly_savings()
kv("\n  Required savings/month", f"₹{req['required_monthly_savings']:,}", W)
kv("  Current capacity",       f"₹{req['current_monthly_capacity']:,}", T if req['feasible'] else R)
kv("  Feasible",               "YES" if req["feasible"] else f"NO — shortfall ₹{req['shortfall_per_month']:,}/mo", G if req["feasible"] else R)

# ─── STEP 4: RUN AGENT ────────────────────────────────────────────────────────

header("Step 4 · Running LangGraph Agent")
hr()
print()

nodes = ["ANALYZE", "PLAN", "REVIEW", "EXECUTE"]
for node in nodes:
    sys.stdout.write(f"  {DIM}[{node}]{C} ")
    sys.stdout.flush()
    time.sleep(0.6)
    print(f"{T}✓{C}")

print()
result = run_agent_workflow("Optimize my savings for this month.")

# ─── THOUGHT ──────────────────────────────────────────────────────────────────

header("[ THOUGHT ] — Internal Reasoning")
hr()
typewrite(f"\n  {DIM}" + result["THOUGHT"] + C, delay=0.008)

# ─── PLAN ─────────────────────────────────────────────────────────────────────

header("[ PLAN ] — Strategy")
hr()
for i, step in enumerate(result["PLAN"], 1):
    print(f"\n  {T}{i}.{C} {step}")

# ─── ACTION ───────────────────────────────────────────────────────────────────

header("[ ACTION ] — Autonomous Execution")
hr()
if result["ACTION"]:
    for a in result["ACTION"]:
        status = a.get("result", {}).get("status", "unknown")
        sc = G if status == "success" else Y
        print(f"  {sc}▸{C} {a['label']:<45} [{sc}{status.upper()}{C}]  saves ₹{a.get('monthly_savings',0):,}/mo")
else:
    print(f"  {DIM}No auto-executed actions.{C}")

# ─── PENDING APPROVALS ────────────────────────────────────────────────────────

if result["PENDING_APPROVALS"]:
    header("[ HUMAN-IN-THE-LOOP ] — Awaiting Approval")
    hr()
    for p in result["PENDING_APPROVALS"]:
        print(f"\n  {Y}⚠  {p['label']}{C}")
        print(f"     {DIM}{p['reason']}{C}")
        print(f"     Saves {T}₹{p['monthly_savings']:,}/mo{C}")
        ans = input(f"\n  Approve? (y/n): ").strip().lower()
        if ans == "y":
            from backend.tools import execute_action
            if p["type"] == "sub_cancel":
                res = execute_action("sub_cancel", sub_id=p["sub_id"])
                print(f"  {G}✓ Executed — {res.get('status')}{C}")
        else:
            print(f"  {R}✗ Rejected — action skipped.{C}")

# ─── UI MESSAGE ───────────────────────────────────────────────────────────────

header("[ UI_MESSAGE ] — Aura Says")
hr()
print(f"\n  {W}{result['UI_MESSAGE']}{C}\n")

hr("═")
print(f"{T}  Aura run complete. Timestamp: {result['timestamp']}{C}\n")
