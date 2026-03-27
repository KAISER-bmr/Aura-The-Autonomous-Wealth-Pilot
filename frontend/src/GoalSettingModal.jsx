// frontend/src/GoalSettingModal.jsx
// Aura — Goal Setting Modal

import { useState, useEffect } from "react";

export default function GoalSettingModal({ token, onClose, onUpdated }) {
  const API = import.meta.env?.VITE_API_URL || "http://localhost:8000";
  const [form, setForm] = useState({ savings_goal: "", current_savings: "", goal_deadline: "" });
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadGoal() {
      try {
        const res = await fetch(`${API}/api/goal`, {
          headers: { "Authorization": `Bearer ${token}` }
        });
        const data = await res.json();
        setForm({
          savings_goal: data.savings_goal || "",
          current_savings: data.current_savings || "",
          goal_deadline: data.goal_deadline?.split("T")[0] || ""
        });
      } catch (e) {}
      setFetching(false);
    }
    loadGoal();
  }, []);

  const update = (k, v) => setForm(f => ({ ...f, [k]: v }));

  async function handleSubmit() {
    setLoading(true); setError("");
    try {
      const res = await fetch(`${API}/api/goal/update`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({
          savings_goal: parseFloat(form.savings_goal),
          current_savings: parseFloat(form.current_savings),
          goal_deadline: form.goal_deadline
        })
      });
      if (!res.ok) throw new Error("Failed to update goal");
      setSuccess(true);
      setTimeout(() => { onUpdated(); onClose(); }, 1200);
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  }

  const gap = parseFloat(form.savings_goal) - parseFloat(form.current_savings);
  const pct = parseFloat(form.current_savings) / parseFloat(form.savings_goal) * 100;

  return (
    <div style={{ position: "fixed", inset: 0, background: "#000000aa", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}
         onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={{ background: "#080f1e", border: "1px solid #0d2040", borderRadius: 16, padding: "28px", width: "100%", maxWidth: 420, fontFamily: "'DM Mono', monospace" }}>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
          <div>
            <div style={{ fontFamily: "'Syne',sans-serif", fontSize: 18, fontWeight: 700, color: "#fff" }}>Savings Goal</div>
            <div style={{ fontSize: 10, color: "#3a5a7a", letterSpacing: ".1em" }}>SET YOUR TARGET</div>
          </div>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "#3a5a7a", fontSize: 20, cursor: "pointer" }}>✕</button>
        </div>

        {success ? (
          <div style={{ textAlign: "center", padding: "20px 0" }}>
            <div style={{ fontSize: 32, color: "#00f5c4" }}>✓</div>
            <div style={{ color: "#00f5c4", marginTop: 8, fontSize: 14 }}>Goal updated!</div>
          </div>
        ) : fetching ? (
          <div style={{ textAlign: "center", padding: "20px 0", color: "#3a5a7a" }}>Loading...</div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div>
              <div style={{ fontSize: 10, color: "#3a5a7a", letterSpacing: ".1em", marginBottom: 6 }}>SAVINGS GOAL (₹)</div>
              <input type="number" value={form.savings_goal} onChange={e => update("savings_goal", e.target.value)}
                placeholder="300000"
                style={{ width: "100%", background: "#0a1525", border: "1px solid #0d2040", borderRadius: 8, padding: "11px 14px", color: "#c8d8f0", fontFamily: "inherit", fontSize: 13, outline: "none" }} />
            </div>

            <div>
              <div style={{ fontSize: 10, color: "#3a5a7a", letterSpacing: ".1em", marginBottom: 6 }}>CURRENT SAVINGS (₹)</div>
              <input type="number" value={form.current_savings} onChange={e => update("current_savings", e.target.value)}
                placeholder="187500"
                style={{ width: "100%", background: "#0a1525", border: "1px solid #0d2040", borderRadius: 8, padding: "11px 14px", color: "#c8d8f0", fontFamily: "inherit", fontSize: 13, outline: "none" }} />
            </div>

            <div>
              <div style={{ fontSize: 10, color: "#3a5a7a", letterSpacing: ".1em", marginBottom: 6 }}>DEADLINE</div>
              <input type="date" value={form.goal_deadline} onChange={e => update("goal_deadline", e.target.value)}
                style={{ width: "100%", background: "#0a1525", border: "1px solid #0d2040", borderRadius: 8, padding: "11px 14px", color: "#c8d8f0", fontFamily: "inherit", fontSize: 13, outline: "none" }} />
            </div>

            {/* Live preview */}
            {form.savings_goal && form.current_savings && !isNaN(pct) && (
              <div style={{ background: "#0a1525", borderRadius: 10, padding: "14px", border: "1px solid #0d2040" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginBottom: 8 }}>
                  <span style={{ color: "#5a7090" }}>Progress</span>
                  <span style={{ color: "#00f5c4" }}>{Math.min(pct, 100).toFixed(1)}%</span>
                </div>
                <div style={{ background: "#0d1e30", borderRadius: 4, height: 6, overflow: "hidden" }}>
                  <div style={{ height: "100%", width: `${Math.min(pct, 100)}%`, background: "linear-gradient(90deg,#0088ff,#00f5c4)", borderRadius: 4, transition: "width .5s" }} />
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, marginTop: 8 }}>
                  <span style={{ color: "#5a7090" }}>Gap remaining</span>
                  <span style={{ color: gap > 0 ? "#ff4d6a" : "#00f5c4" }}>₹{Math.max(gap, 0).toLocaleString()}</span>
                </div>
              </div>
            )}

            {error && (
              <div style={{ background: "#1a0a0a", border: "1px solid #ff4d6a44", borderRadius: 8, padding: "10px 12px", fontSize: 12, color: "#ff8c9a" }}>✗ {error}</div>
            )}

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 4 }}>
              <button onClick={onClose} style={{ background: "#0a1525", border: "1px solid #0d2040", borderRadius: 10, padding: "12px", color: "#5a7090", fontFamily: "inherit", fontSize: 12, cursor: "pointer" }}>Cancel</button>
              <button onClick={handleSubmit} disabled={loading} style={{ background: "linear-gradient(135deg,#00f5c4,#0088ff)", border: "none", borderRadius: 10, padding: "12px", color: "#060d1a", fontFamily: "'Syne',sans-serif", fontWeight: 700, fontSize: 12, cursor: loading ? "not-allowed" : "pointer", opacity: loading ? .6 : 1 }}>
                {loading ? "⟳ SAVING..." : "UPDATE GOAL"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}