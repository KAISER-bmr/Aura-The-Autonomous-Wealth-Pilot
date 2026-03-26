"""
frontend/streamlit_app.py
Aura — Streamlit Dashboard (Shreeya's Domain)
Displays: Thought Trace (Brain), Action Log (Autonomy), Budget UI, Approval Panel
Run: streamlit run frontend/streamlit_app.py
"""

import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json
import time
import requests
from datetime import datetime

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Aura — Autonomous Wealth Pilot",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CUSTOM CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@700;800&display=swap');

* { font-family: 'DM Mono', monospace !important; }
h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

.stApp { background: #060d1a; color: #c8d8f0; }

.metric-card {
    background: #0a1525;
    border: 1px solid #0d2040;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
}
.thought-box {
    background: #0a1525;
    border: 1px solid #0d2040;
    border-left: 3px solid #00f5c4;
    border-radius: 8px;
    padding: 16px;
    font-size: 13px;
    color: #8ab0d0;
    line-height: 1.8;
}
.action-card {
    background: #0a1525;
    border: 1px solid #00f5c422;
    border-radius: 10px;
    padding: 12px;
    margin-bottom: 8px;
    font-size: 12px;
}
.pending-card {
    background: #1a0a0a;
    border: 1px solid #ff4d6a44;
    border-radius: 10px;
    padding: 12px;
    margin-bottom: 8px;
}
.log-entry {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    padding: 4px 0;
    border-bottom: 1px solid #0d2040;
}
.node-active { color: #00f5c4; font-weight: 600; }
.node-done { color: #3a6a5a; }
.node-pending { color: #1a3a5a; }
.overspend { color: #ff4d6a; }
.ok { color: #00f5c4; }
.warn { color: #f5a500; }
</style>
""", unsafe_allow_html=True)

# ─── API CONFIG ───────────────────────────────────────────────────────────────

API_BASE = os.getenv("AURA_API_URL", "http://localhost:8000")

def call_api(endpoint: str, method="GET", data=None):
    """Call the FastAPI backend, fall back to direct tool calls."""
    try:
        url = f"{API_BASE}{endpoint}"
        if method == "GET":
            r = requests.get(url, timeout=5)
        else:
            r = requests.post(url, json=data, timeout=10)
        return r.json()
    except Exception:
        # Direct import fallback (for demo without running API)
        from backend.tools import fetch_data, analyze_trends
        from agent.workflow import run_agent_workflow
        if endpoint == "/api/tools/fetch":
            return fetch_data()
        elif endpoint == "/api/tools/analyze":
            return analyze_trends()
        elif endpoint == "/api/agent/run":
            return run_agent_workflow(data.get("user_prompt", "Analyze finances.") if data else "Analyze finances.")
        return {}

# ─── SESSION STATE ────────────────────────────────────────────────────────────

if "agent_result" not in st.session_state:
    st.session_state.agent_result = None
if "node_idx" not in st.session_state:
    st.session_state.node_idx = -1
if "approvals" not in st.session_state:
    st.session_state.approvals = {}
if "action_log" not in st.session_state:
    st.session_state.action_log = []

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ✦ AURA")
    st.markdown("*Autonomous Wealth Pilot*")
    st.divider()

    snapshot = call_api("/api/tools/fetch")
    profile = snapshot.get("user_profile", {})

    st.markdown(f"**User:** {profile.get('name', 'N/A')}")
    st.markdown(f"**Goal:** ₹{profile.get('savings_goal', 0):,}")
    st.markdown(f"**Saved:** ₹{profile.get('current_savings', 0):,}")

    gap = snapshot.get("savings_gap", 0)
    pct = snapshot.get("savings_pct", 0)
    st.progress(pct / 100, text=f"{pct}% to goal")
    st.markdown(f"**Gap:** ₹{gap:,}")
    st.divider()

    user_prompt = st.text_area(
        "Agent Prompt",
        value="Analyze my spending and optimize my savings.",
        height=80
    )

    if st.button("▶ RUN AURA AGENT", type="primary", use_container_width=True):
        with st.spinner("Agent running..."):
            for i in range(4):
                st.session_state.node_idx = i
                time.sleep(0.8)
            result = call_api("/api/agent/run", method="POST", data={"user_prompt": user_prompt})
            st.session_state.agent_result = result
            st.session_state.action_log = [
                {"ts": datetime.now().strftime("%H:%M:%S"), "msg": "fetch_data() → ledger loaded", "type": "info"},
                {"ts": datetime.now().strftime("%H:%M:%S"), "msg": "analyze_trends() → analysis complete", "type": "info"},
            ]
            for a in result.get("ACTION", []):
                r = a.get("result", {})
                st.session_state.action_log.append({
                    "ts": datetime.now().strftime("%H:%M:%S"),
                    "msg": f"{a['label']} → {r.get('status', 'unknown').upper()}",
                    "type": "ok" if r.get("status") == "success" else "warn"
                })
            for p in result.get("PENDING_APPROVALS", []):
                st.session_state.action_log.append({
                    "ts": datetime.now().strftime("%H:%M:%S"),
                    "msg": f"{p['label']} → PENDING HUMAN APPROVAL",
                    "type": "warn"
                })
        st.rerun()

    st.divider()
    st.markdown("**Built by:** 3G2B")
    st.markdown("*Orchestron Competition 2025*")

# ─── MAIN CONTENT ─────────────────────────────────────────────────────────────

st.markdown("# ✦ AURA CORE ENGINE")
st.markdown("*Autonomous Wealth Pilot — Goal-Driven Financial Agent*")
st.divider()

# ─── METRICS ROW ──────────────────────────────────────────────────────────────

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Current Savings", f"₹{snapshot.get('user_profile', {}).get('current_savings', 0):,}", delta=None)
with col2:
    st.metric("Savings Gap", f"₹{snapshot.get('savings_gap', 0):,}")
with col3:
    st.metric("Monthly Spend", f"₹{snapshot.get('total_spent', 0):,}")
with col4:
    st.metric("Monthly Budget", f"₹{snapshot.get('total_budget', 0):,}")

st.divider()

# ─── LANGGRAPH NODE TRACE ─────────────────────────────────────────────────────

st.markdown("### 🔄 LANGGRAPH STATE MACHINE")
nodes = ["ANALYZE", "PLAN", "REVIEW", "EXECUTE"]
cols = st.columns(len(nodes))
result = st.session_state.agent_result
node_trace = result.get("node_trace", []) if result else []

for i, (col, node) in enumerate(zip(cols, nodes)):
    with col:
        done = node in node_trace
        css = "node-active" if done else "node-pending"
        icon = "✓" if done else "○"
        st.markdown(f'<div class="{css}" style="text-align:center;padding:10px;background:#0a1525;border-radius:8px;border:1px solid {"#00f5c444" if done else "#0d2040"}">{icon} {node}</div>', unsafe_allow_html=True)

st.divider()

# ─── TWO COLUMN LAYOUT ────────────────────────────────────────────────────────

left, right = st.columns([3, 2])

with left:
    # THOUGHT TRACE
    st.markdown("### 🧠 [THOUGHT] — Brain")
    if result:
        st.markdown(f'<div class="thought-box">{result.get("THOUGHT", "")}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="thought-box" style="color:#1a3a5a;font-style:italic;">Run the agent to see reasoning trace...</div>', unsafe_allow_html=True)

    st.markdown("### 📋 [PLAN] — Strategy")
    if result and result.get("PLAN"):
        for i, step in enumerate(result["PLAN"], 1):
            st.markdown(f"**{i}.** {step}")
    else:
        st.markdown("*No plan generated yet.*")

    # UI MESSAGE
    if result:
        st.divider()
        st.markdown("### 💬 [UI_MESSAGE]")
        st.info(result.get("UI_MESSAGE", ""))

with right:
    # ACTION LOG
    st.markdown("### ⚡ [ACTION] — Execution Log")
    if st.session_state.action_log:
        for entry in st.session_state.action_log:
            color = "#00f5c4" if entry["type"] == "ok" else "#f5a500" if entry["type"] == "warn" else "#0088ff"
            st.markdown(
                f'<div class="log-entry"><span style="color:#3a5a7a">{entry["ts"]}</span> '
                f'<span style="color:{color}">●</span> {entry["msg"]}</div>',
                unsafe_allow_html=True
            )
    else:
        st.markdown("*No actions logged yet.*")

    # HUMAN-IN-THE-LOOP APPROVALS
    if result and result.get("PENDING_APPROVALS"):
        st.divider()
        st.markdown("### ⚠️ HUMAN APPROVAL REQUIRED")
        for pending in result["PENDING_APPROVALS"]:
            pid = pending["id"]
            with st.container():
                st.markdown(f'<div class="pending-card">', unsafe_allow_html=True)
                st.markdown(f"**{pending['label']}**")
                st.markdown(f"Saves ₹{pending['monthly_savings']:,}/mo · {pending['reason']}")
                a_col, r_col = st.columns(2)
                with a_col:
                    if st.button(f"✓ Approve", key=f"approve_{pid}"):
                        st.session_state.approvals[pid] = "approved"
                        # call API to execute
                        call_api("/api/tools/execute", method="POST",
                                 data={"action_type": pending["type"],
                                       "sub_id": pending.get("sub_id", "")})
                        st.session_state.action_log.append({
                            "ts": datetime.now().strftime("%H:%M:%S"),
                            "msg": f"{pending['label']} → APPROVED → SUCCESS",
                            "type": "ok"
                        })
                        st.success("Action approved and executed!")
                with r_col:
                    if st.button(f"✗ Reject", key=f"reject_{pid}"):
                        st.session_state.approvals[pid] = "rejected"
                        st.session_state.action_log.append({
                            "ts": datetime.now().strftime("%H:%M:%S"),
                            "msg": f"{pending['label']} → REJECTED by user",
                            "type": "warn"
                        })
                        st.warning("Action rejected.")
                st.markdown('</div>', unsafe_allow_html=True)

# ─── SPENDING ANALYSIS TABLE ──────────────────────────────────────────────────

st.divider()
st.markdown("### 📊 SPENDING ANALYSIS")

analysis = call_api("/api/tools/analyze")
overspend = analysis.get("overspend_categories", [])

if overspend:
    import pandas as pd
    df = pd.DataFrame([{
        "Category": o["category"],
        "Budget (₹)": o["budgeted"],
        "Spent (₹)": o["actual"],
        "Over by (₹)": o["overspend_amount"],
        "% Over": f"{o['overspend_pct']}%",
        "Severity": o["severity"].upper()
    } for o in overspend])
    st.dataframe(df, use_container_width=True, hide_index=True)

# ─── SUBSCRIPTIONS ────────────────────────────────────────────────────────────

st.divider()
st.markdown("### 💳 SUBSCRIPTIONS")

subs_data = call_api("/api/subscriptions")
subs = subs_data.get("subscriptions", [])

if subs:
    sub_cols = st.columns(len(subs))
    for col, sub in zip(sub_cols, subs):
        with col:
            color = "#ff4d6a" if sub["status"] == "flagged" else "#00f5c4"
            st.markdown(
                f'<div style="background:#0a1525;border:1px solid {color}33;border-radius:10px;padding:12px;text-align:center">'
                f'<div style="font-size:13px;color:#c8d8f0">{sub["name"]}</div>'
                f'<div style="font-size:18px;color:{color};font-weight:700">₹{sub["amount"]}</div>'
                f'<div style="font-size:10px;color:#3a5a7a">/month</div>'
                f'<div style="font-size:9px;color:{color};margin-top:6px;padding:2px 8px;background:{color}22;border-radius:10px">{sub["status"].upper()}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
