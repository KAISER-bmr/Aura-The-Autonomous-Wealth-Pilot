// frontend/src/AuraDashboard.jsx
// Aura — React Dashboard (Shreeya's Domain)
// Connects to FastAPI backend at VITE_API_URL

import { useState, useEffect, useRef, useCallback } from "react";

const API = import.meta.env?.VITE_API_URL || "http://localhost:8000";

// ─── UTILITIES ────────────────────────────────────────────────────────────────

async function apiFetch(path, options = {}) {
  try {
    const res = await fetch(`${API}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    return await res.json();
  } catch {
    // Return mock data if API not running
    return null;
  }
}

// ─── SUB-COMPONENTS ───────────────────────────────────────────────────────────

function GlowRing({ value, max, size = 130, color = "#00f5c4" }) {
  const pct = Math.min(value / max, 1);
  const r = size / 2 - 10;
  const circ = 2 * Math.PI * r;
  const dash = circ * pct;
  return (
    <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#1a2235" strokeWidth={9} />
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={9}
        strokeDasharray={`${dash} ${circ}`} strokeLinecap="round"
        style={{ filter: `drop-shadow(0 0 8px ${color})`, transition: "stroke-dasharray 1.2s ease" }} />
    </svg>
  );
}

function TypewriterText({ text, speed = 14, triggerKey }) {
  const [out, setOut] = useState("");
  const idx = useRef(0);
  useEffect(() => {
    idx.current = 0; setOut("");
    const iv = setInterval(() => {
      idx.current++;
      setOut(text.slice(0, idx.current));
      if (idx.current >= text.length) clearInterval(iv);
    }, speed);
    return () => clearInterval(iv);
  }, [triggerKey]);
  return <span>{out}<span style={{ opacity: out.length < text.length ? 1 : 0, color: "#00f5c4" }}>▋</span></span>;
}

function NodePill({ label, state }) {
  const colors = { idle: { bg: "#0a1525", border: "#0d2040", text: "#1a3a5a" }, active: { bg: "#00f5c4", border: "#00f5c4", text: "#060d1a" }, done: { bg: "#0a2a1a", border: "#00f5c466", text: "#00f5c4" } };
  const c = colors[state] || colors.idle;
  return (
    <div style={{ padding: "7px 16px", borderRadius: 20, border: `1px solid ${c.border}`, background: c.bg, color: c.text, fontSize: 11, letterSpacing: ".1em", fontWeight: state === "active" ? 600 : 400, boxShadow: state === "active" ? "0 0 16px #00f5c488" : "none", transition: "all .3s" }}>
      {state === "done" ? "✓ " : state === "active" ? "⟳ " : "○ "}{label}
    </div>
  );
}

// ─── MAIN COMPONENT ───────────────────────────────────────────────────────────

export default function AuraDashboard() {
  const [snapshot, setSnapshot] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [agentResult, setAgentResult] = useState(null);
  const [running, setRunning] = useState(false);
  const [activeNode, setActiveNode] = useState(-1);
  const [tab, setTab] = useState("thought");
  const [actionLog, setActionLog] = useState([]);
  const [approvals, setApprovals] = useState({});
  const [prompt, setPrompt] = useState("Analyze my spending and optimize my savings.");

  const NODES = ["ANALYZE", "PLAN", "REVIEW", "EXECUTE"];

  // Load initial data
  useEffect(() => {
    apiFetch("/api/tools/fetch").then(d => d && setSnapshot(d));
    apiFetch("/api/tools/analyze").then(d => d && setAnalysis(d));
  }, []);

  const runAgent = useCallback(async () => {
    setRunning(true); setActiveNode(0); setAgentResult(null); setActionLog([]);
    // Animate through nodes
    for (let i = 0; i < NODES.length; i++) {
      setActiveNode(i);
      await new Promise(r => setTimeout(r, 900 + i * 200));
    }
    const result = await apiFetch("/api/agent/run", { method: "POST", body: JSON.stringify({ user_prompt: prompt }) });
    if (result) {
      setAgentResult(result);
      const log = [
        { ts: now(), msg: "fetch_data() → ledger loaded", type: "info" },
        { ts: now(), msg: "analyze_trends() → analysis complete", type: "info" },
      ];
      for (const a of result.ACTION || []) {
        log.push({ ts: now(), msg: `${a.label} → ${a.result?.status?.toUpperCase() || "DONE"}`, type: a.result?.status === "success" ? "ok" : "warn" });
      }
      for (const p of result.PENDING_APPROVALS || []) {
        log.push({ ts: now(), msg: `${p.label} → PENDING APPROVAL`, type: "warn" });
      }
      setActionLog(log);
    }
    setRunning(false);
    setActiveNode(NODES.length);
  }, [prompt]);

  const handleApproval = async (pending, approved) => {
    setApprovals(prev => ({ ...prev, [pending.id]: approved ? "approved" : "rejected" }));
    if (approved) {
      await apiFetch(`/api/tools/execute?action_type=${pending.type}&sub_id=${pending.sub_id || ""}`, { method: "POST", body: "{}" });
      setActionLog(l => [...l, { ts: now(), msg: `${pending.label} → APPROVED → SUCCESS`, type: "ok" }]);
    } else {
      setActionLog(l => [...l, { ts: now(), msg: `${pending.label} → REJECTED`, type: "warn" }]);
    }
  };

  const now = () => new Date().toLocaleTimeString("en-IN", { hour12: false });
  const profile = snapshot?.user_profile || {};
  const gap = snapshot?.savings_gap || 0;
  const pct = snapshot?.savings_pct || 0;
  const nodeState = (i) => activeNode > i || (!running && agentResult) ? "done" : activeNode === i ? "active" : "idle";

  const CSS = `
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@700;800&display=swap');
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #060d1a; color: #c8d8f0; font-family: 'DM Mono', monospace; }
    ::-webkit-scrollbar { width: 4px; } ::-webkit-scrollbar-track { background: #0a1525; } ::-webkit-scrollbar-thumb { background: #00f5c4; border-radius: 2px; }
    .bar-fill { transition: width 1.4s cubic-bezier(.4,0,.2,1); }
    .fade-in { animation: fi .4s ease forwards; }
    @keyframes fi { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }
    .pulse { animation: pa 2s infinite; }
    @keyframes pa { 0%,100%{opacity:1} 50%{opacity:.3} }
    textarea { resize: none; background: #0a1525; border: 1px solid #0d2040; color: #c8d8f0; border-radius: 8px; padding: 10px; font-family: 'DM Mono', monospace; font-size: 12px; width: 100%; outline: none; }
    textarea:focus { border-color: #00f5c466; }
  `;

  return (
    <div style={{ fontFamily: "'DM Mono', monospace", background: "#060d1a", minHeight: "100vh", color: "#c8d8f0" }}>
      <style>{CSS}</style>

      {/* HEADER */}
      <div style={{ background: "#080f1e", borderBottom: "1px solid #0d2040", padding: "14px 28px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 34, height: 34, borderRadius: "50%", background: "linear-gradient(135deg,#00f5c4,#0088ff)", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 0 18px #00f5c455", fontSize: 16 }}>✦</div>
          <div>
            <div style={{ fontFamily: "'Syne',sans-serif", fontSize: 18, fontWeight: 800, color: "#fff", letterSpacing: "-.02em" }}>AURA</div>
            <div style={{ fontSize: 9, color: "#3a5a7a", letterSpacing: ".15em" }}>AUTONOMOUS WEALTH PILOT</div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <span style={{ fontSize: 12, color: "#5a7090" }}>{profile.name || "Loading..."}</span>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <div style={{ width: 7, height: 7, borderRadius: "50%", background: running ? "#f5a500" : agentResult ? "#00f5c4" : "#1a3a5a", boxShadow: running ? "0 0 8px #f5a500" : agentResult ? "0 0 8px #00f5c4" : "none" }} className={running ? "pulse" : ""} />
            <span style={{ fontSize: 10, color: running ? "#f5a500" : agentResult ? "#00f5c4" : "#3a5a7a", letterSpacing: ".1em" }}>{running ? "PROCESSING" : agentResult ? "COMPLETE" : "STANDBY"}</span>
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "260px 1fr 290px", height: "calc(100vh - 62px)" }}>

        {/* LEFT PANEL */}
        <div style={{ background: "#080f1e", borderRight: "1px solid #0d2040", padding: "20px 16px", overflowY: "auto", display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Ring */}
          <div style={{ textAlign: "center" }}>
            <div style={{ position: "relative", display: "inline-block" }}>
              <GlowRing value={profile.current_savings || 0} max={profile.savings_goal || 1} size={130} />
              <div style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%,-50%)", textAlign: "center" }}>
                <div style={{ fontSize: 20, fontWeight: 500, color: "#00f5c4", fontFamily: "'Syne',sans-serif" }}>{pct}%</div>
                <div style={{ fontSize: 8, color: "#3a5a7a", letterSpacing: ".1em" }}>TO GOAL</div>
              </div>
            </div>
            <div style={{ marginTop: 10 }}>
              <div style={{ fontSize: 10, color: "#5a7090" }}>GOAL</div>
              <div style={{ fontSize: 22, fontFamily: "'Syne',sans-serif", fontWeight: 700, color: "#fff" }}>₹{(profile.savings_goal || 0).toLocaleString()}</div>
              <div style={{ fontSize: 10, color: "#3a5a7a" }}>by {profile.goal_deadline?.slice(0, 7) || "—"}</div>
            </div>
          </div>

          {/* Stats Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            {[
              { l: "SAVED", v: `₹${((profile.current_savings || 0)/1000).toFixed(0)}K`, c: "#00f5c4" },
              { l: "GAP", v: `₹${(gap/1000).toFixed(0)}K`, c: "#ff4d6a" },
              { l: "INCOME", v: `₹${((profile.monthly_income || 0)/1000).toFixed(0)}K`, c: "#0088ff" },
              { l: "SPENT", v: `₹${((snapshot?.total_spent || 0)/1000).toFixed(0)}K`, c: "#f5a500" },
            ].map(s => (
              <div key={s.l} style={{ background: "#0a1525", borderRadius: 10, padding: "10px 8px", border: "1px solid #0d2040", textAlign: "center" }}>
                <div style={{ fontSize: 8, color: "#3a5a7a", letterSpacing: ".12em" }}>{s.l}</div>
                <div style={{ fontSize: 16, fontFamily: "'Syne',sans-serif", fontWeight: 700, color: s.c, marginTop: 3 }}>{s.v}</div>
              </div>
            ))}
          </div>

          {/* Category Bars */}
          <div>
            <div style={{ fontSize: 9, color: "#3a5a7a", letterSpacing: ".12em", marginBottom: 10 }}>CATEGORY SPEND</div>
            {(analysis?.overspend_categories || []).concat(analysis?.underspend_categories || []).slice(0, 6).map(cat => {
              const over = cat.overspend_amount > 0;
              const w = Math.min(((cat.actual || 0) / ((cat.budgeted || 1) * 1.4)) * 100, 100);
              return (
                <div key={cat.category} style={{ marginBottom: 9 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, marginBottom: 3 }}>
                    <span style={{ color: over ? "#ff4d6a" : "#7a9ab8" }}>{cat.category}</span>
                    <span style={{ color: over ? "#ff4d6a" : "#4a6a5a" }}>{over ? "+" : ""}₹{(over ? cat.overspend_amount : -(cat.savings_potential || 0)).toLocaleString()}</span>
                  </div>
                  <div style={{ background: "#0d1e30", borderRadius: 3, height: 4, overflow: "hidden" }}>
                    <div className="bar-fill" style={{ height: "100%", width: `${w}%`, background: over ? "linear-gradient(90deg,#ff4d6a,#ff8c00)" : "linear-gradient(90deg,#0088ff,#00f5c4)", borderRadius: 3 }} />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Prompt */}
          <textarea rows={3} value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="Agent prompt..." />

          {/* Run Button */}
          <button onClick={runAgent} disabled={running} style={{ background: running ? "#0a1525" : "linear-gradient(135deg,#00f5c4,#0088ff)", color: running ? "#3a5a7a" : "#060d1a", border: "none", borderRadius: 10, padding: "13px", fontFamily: "'Syne',sans-serif", fontWeight: 700, fontSize: 12, cursor: running ? "not-allowed" : "pointer", letterSpacing: ".08em", boxShadow: running ? "none" : "0 0 24px #00f5c433", transition: "all .3s" }}>
            {running ? "⟳ RUNNING..." : "▶ RUN AURA AGENT"}
          </button>
        </div>

        {/* CENTER PANEL */}
        <div style={{ padding: "20px 24px", overflowY: "auto", display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Node Flow */}
          <div style={{ background: "#0a1525", borderRadius: 12, border: "1px solid #0d2040", padding: "14px 18px" }}>
            <div style={{ fontSize: 9, color: "#3a5a7a", letterSpacing: ".15em", marginBottom: 12 }}>LANGGRAPH STATE MACHINE</div>
            <div style={{ display: "flex", alignItems: "center", gap: 0 }}>
              {NODES.map((n, i) => (
                <div key={n} style={{ display: "flex", alignItems: "center", flex: i < NODES.length - 1 ? 1 : "none" }}>
                  <NodePill label={n} state={nodeState(i)} />
                  {i < NODES.length - 1 && <div style={{ flex: 1, height: 1, background: activeNode > i || (!running && agentResult) ? "#00f5c466" : "#0d2040", margin: "0 4px", transition: "background .5s" }} />}
                </div>
              ))}
            </div>
          </div>

          {/* Tabs */}
          <div style={{ display: "flex", gap: 4 }}>
            {[["thought","🧠 THOUGHT"],["plan","📋 PLAN"],["log","⚡ LOG"]].map(([t,l]) => (
              <button key={t} onClick={() => setTab(t)} style={{ background: tab===t ? "#00f5c422" : "none", color: tab===t ? "#00f5c4" : "#5a7090", border: "none", cursor: "pointer", padding: "7px 16px", borderRadius: 6, fontFamily: "inherit", fontSize: 11, letterSpacing: ".08em", transition: "all .2s" }}>{l}</button>
            ))}
          </div>

          {/* Tab Content */}
          {tab === "thought" && (
            <div style={{ background: "#0a1525", borderRadius: 12, border: "1px solid #0d2040", borderLeft: "3px solid #00f5c4", padding: "18px", flex: 1 }}>
              <div style={{ fontSize: 9, color: "#3a5a7a", letterSpacing: ".15em", marginBottom: 12 }}>[THOUGHT] — INTERNAL REASONING</div>
              {agentResult ? (
                <div style={{ fontSize: 12, lineHeight: 1.9, color: "#8ab0d0" }}>
                  <TypewriterText text={agentResult.THOUGHT} triggerKey={agentResult.timestamp} />
                </div>
              ) : <div style={{ fontSize: 12, color: "#1a3a5a", fontStyle: "italic" }}>Waiting for agent execution...</div>}
            </div>
          )}

          {tab === "plan" && (
            <div style={{ background: "#0a1525", borderRadius: 12, border: "1px solid #0d2040", padding: "18px", flex: 1 }}>
              <div style={{ fontSize: 9, color: "#3a5a7a", letterSpacing: ".15em", marginBottom: 12 }}>[PLAN] — STRATEGY</div>
              {agentResult?.PLAN?.length ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  {agentResult.PLAN.map((p, i) => (
                    <div key={i} className="fade-in" style={{ display: "flex", gap: 12, alignItems: "flex-start", animationDelay: `${i*.15}s` }}>
                      <div style={{ minWidth: 26, height: 26, borderRadius: "50%", background: "#0d2a40", border: "1px solid #00f5c466", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, color: "#00f5c4", fontFamily: "'Syne',sans-serif", fontWeight: 700 }}>{i+1}</div>
                      <div style={{ fontSize: 12, color: "#8ab0d0", lineHeight: 1.7, paddingTop: 4 }}>{p}</div>
                    </div>
                  ))}
                </div>
              ) : <div style={{ fontSize: 12, color: "#1a3a5a", fontStyle: "italic" }}>No plan yet...</div>}
            </div>
          )}

          {tab === "log" && (
            <div style={{ background: "#0a1525", borderRadius: 12, border: "1px solid #0d2040", padding: "18px", flex: 1, overflowY: "auto" }}>
              <div style={{ fontSize: 9, color: "#3a5a7a", letterSpacing: ".15em", marginBottom: 12 }}>[ACTION LOG] — EXECUTION TRACE</div>
              {actionLog.length ? actionLog.map((l, i) => (
                <div key={i} className="fade-in" style={{ display: "flex", gap: 10, alignItems: "flex-start", paddingBottom: 8, animationDelay: `${i*.08}s` }}>
                  <span style={{ fontSize: 9, color: "#3a5a7a", whiteSpace: "nowrap", paddingTop: 2 }}>{l.ts}</span>
                  <div style={{ width: 6, height: 6, borderRadius: "50%", marginTop: 4, background: l.type==="ok" ? "#00f5c4" : l.type==="warn" ? "#f5a500" : "#0088ff", boxShadow: `0 0 5px ${l.type==="ok"?"#00f5c4":l.type==="warn"?"#f5a500":"#0088ff"}` }} />
                  <span style={{ fontSize: 11, color: l.type==="ok"?"#00c49a":l.type==="warn"?"#f5a500":"#6a9abf" }}>{l.msg}</span>
                </div>
              )) : <div style={{ fontSize: 12, color: "#1a3a5a", fontStyle: "italic" }}>No log entries yet...</div>}
            </div>
          )}

          {/* UI Message */}
          {agentResult && (
            <div className="fade-in" style={{ background: "linear-gradient(135deg,#0a2a1a,#0a1a2a)", borderRadius: 12, border: "1px solid #00f5c422", padding: "14px 18px" }}>
              <div style={{ fontSize: 9, color: "#00f5c466", letterSpacing: ".15em", marginBottom: 6 }}>[UI_MESSAGE]</div>
              <div style={{ fontSize: 13, color: "#c8e8d8", lineHeight: 1.7 }}>{agentResult.UI_MESSAGE}</div>
            </div>
          )}
        </div>

        {/* RIGHT PANEL */}
        <div style={{ background: "#080f1e", borderLeft: "1px solid #0d2040", padding: "20px 16px", overflowY: "auto", display: "flex", flexDirection: "column", gap: 18 }}>
          <div style={{ fontSize: 9, color: "#3a5a7a", letterSpacing: ".15em" }}>[ACTION] — AUTONOMOUS EXECUTION</div>

          {agentResult?.ACTION?.length ? agentResult.ACTION.map((a, i) => (
            <div key={i} className="fade-in" style={{ background: "#0a1525", borderRadius: 10, padding: "12px", border: "1px solid #00f5c422", animationDelay: `${i*.2}s` }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <span style={{ fontSize: 10, color: "#00f5c4", letterSpacing: ".08em" }}>{a.label}</span>
                <span style={{ fontSize: 8, background: "#0a2a1a", color: "#00f5c4", padding: "2px 7px", borderRadius: 10 }}>AUTO</span>
              </div>
              <div style={{ fontSize: 10, color: "#3a5a7a" }}>{a.type} → {a.result?.status || "executed"}</div>
              {a.monthly_savings && <div style={{ fontSize: 10, color: "#00f5c4", marginTop: 4 }}>+₹{a.monthly_savings.toLocaleString()}/mo saved</div>}
            </div>
          )) : <div style={{ fontSize: 11, color: "#1a3a5a", fontStyle: "italic" }}>No actions yet.</div>}

          {/* Approvals */}
          {agentResult?.PENDING_APPROVALS?.filter(p => !approvals[p.id]).map((p, i) => (
            <div key={i} className="fade-in" style={{ background: "#1a0a0a", borderRadius: 12, border: "1px solid #ff4d6a44", padding: "14px" }}>
              <div style={{ fontSize: 9, color: "#ff4d6a", letterSpacing: ".15em", marginBottom: 6 }}>⚠ APPROVAL REQUIRED</div>
              <div style={{ fontSize: 12, color: "#c8a0a0", marginBottom: 3 }}>{p.label}</div>
              <div style={{ fontSize: 10, color: "#7a5050", marginBottom: 12 }}>₹{p.monthly_savings.toLocaleString()}/mo · {p.reason}</div>
              <div style={{ display: "flex", gap: 8 }}>
                <button onClick={() => handleApproval(p, true)} style={{ flex: 1, background: "#00f5c4", color: "#060d1a", border: "none", borderRadius: 6, padding: "8px", fontFamily: "inherit", fontWeight: 700, fontSize: 11, cursor: "pointer" }}>✓ Approve</button>
                <button onClick={() => handleApproval(p, false)} style={{ flex: 1, background: "#1a0a0a", color: "#ff4d6a", border: "1px solid #ff4d6a44", borderRadius: 6, padding: "8px", fontFamily: "inherit", fontSize: 11, cursor: "pointer" }}>✗ Reject</button>
              </div>
            </div>
          ))}

          {/* Subscriptions */}
          <div style={{ fontSize: 9, color: "#3a5a7a", letterSpacing: ".15em", marginTop: 4 }}>SUBSCRIPTIONS</div>
          {(snapshot?.subscriptions || []).map(s => (
            <div key={s.id} style={{ background: "#0a1525", borderRadius: 8, padding: "10px 12px", border: `1px solid ${s.status==="flagged"?"#ff4d6a33":"#0d2040"}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ fontSize: 12, color: s.status==="flagged"?"#ff8c9a":"#7a9ab8" }}>{s.name}</div>
                <div style={{ fontSize: 10, color: "#3a5a7a" }}>₹{s.amount}/mo · {s.days_since_use}d ago</div>
              </div>
              <div style={{ fontSize: 8, padding: "3px 8px", borderRadius: 10, background: s.status==="flagged"?"#2a0a0a":"#0a2020", color: s.status==="flagged"?"#ff4d6a":"#3a6a5a" }}>{s.status.toUpperCase()}</div>
            </div>
          ))}

          <div style={{ marginTop: "auto", background: "#0a1525", borderRadius: 10, padding: "12px", border: "1px solid #0d2040", textAlign: "center" }}>
            <div style={{ fontSize: 9, color: "#3a5a7a", letterSpacing: ".15em" }}>BUILT BY</div>
            <div style={{ fontSize: 13, fontFamily: "'Syne',sans-serif", fontWeight: 700, color: "#fff", marginTop: 3 }}>3G2B</div>
            <div style={{ fontSize: 9, color: "#3a5a7a" }}>Orchestron Competition 2025</div>
          </div>
        </div>
      </div>
    </div>
  );
}
