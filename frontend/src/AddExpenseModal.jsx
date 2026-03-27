// frontend/src/AddExpenseModal.jsx
// Aura — Add Expense Modal

import { useState } from "react";

const CATEGORIES = [
  "Dining Out", "Groceries", "Entertainment", "Transport",
  "Subscriptions", "Utilities", "Shopping", "Healthcare", "Other"
];

export default function AddExpenseModal({ token, onClose, onAdded }) {
  const API = import.meta.env?.VITE_API_URL || "http://localhost:8000";
  const [form, setForm] = useState({
    category: "Dining Out", description: "", amount: "", date: new Date().toISOString().split("T")[0]
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const update = (k, v) => setForm(f => ({ ...f, [k]: v }));

  async function handleSubmit() {
    if (!form.description || !form.amount) {
      setError("Please fill in all fields."); return;
    }
    setLoading(true); setError("");
    try {
      const res = await fetch(`${API}/api/transactions/add`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ ...form, amount: parseFloat(form.amount) })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to add expense");
      setSuccess(true);
      setTimeout(() => { onAdded(); onClose(); }, 1200);
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  }

  return (
    <div style={{ position: "fixed", inset: 0, background: "#000000aa", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}
         onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={{ background: "#080f1e", border: "1px solid #0d2040", borderRadius: 16, padding: "28px", width: "100%", maxWidth: 400, fontFamily: "'DM Mono', monospace" }}>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
          <div>
            <div style={{ fontFamily: "'Syne',sans-serif", fontSize: 18, fontWeight: 700, color: "#fff" }}>Add Expense</div>
            <div style={{ fontSize: 10, color: "#3a5a7a", letterSpacing: ".1em" }}>LOG A NEW TRANSACTION</div>
          </div>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "#3a5a7a", fontSize: 20, cursor: "pointer" }}>✕</button>
        </div>

        {success ? (
          <div style={{ textAlign: "center", padding: "20px 0" }}>
            <div style={{ fontSize: 32 }}>✓</div>
            <div style={{ color: "#00f5c4", marginTop: 8, fontSize: 14 }}>Expense added!</div>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {/* Category */}
            <div>
              <div style={{ fontSize: 10, color: "#3a5a7a", letterSpacing: ".1em", marginBottom: 6 }}>CATEGORY</div>
              <select value={form.category} onChange={e => update("category", e.target.value)}
                style={{ width: "100%", background: "#0a1525", border: "1px solid #0d2040", borderRadius: 8, padding: "11px 14px", color: "#c8d8f0", fontFamily: "inherit", fontSize: 13, outline: "none" }}>
                {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            {/* Description */}
            <div>
              <div style={{ fontSize: 10, color: "#3a5a7a", letterSpacing: ".1em", marginBottom: 6 }}>DESCRIPTION</div>
              <input value={form.description} onChange={e => update("description", e.target.value)}
                placeholder="e.g. Swiggy Order"
                style={{ width: "100%", background: "#0a1525", border: "1px solid #0d2040", borderRadius: 8, padding: "11px 14px", color: "#c8d8f0", fontFamily: "inherit", fontSize: 13, outline: "none" }} />
            </div>

            {/* Amount + Date row */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <div>
                <div style={{ fontSize: 10, color: "#3a5a7a", letterSpacing: ".1em", marginBottom: 6 }}>AMOUNT (₹)</div>
                <input type="number" value={form.amount} onChange={e => update("amount", e.target.value)}
                  placeholder="500"
                  style={{ width: "100%", background: "#0a1525", border: "1px solid #0d2040", borderRadius: 8, padding: "11px 14px", color: "#c8d8f0", fontFamily: "inherit", fontSize: 13, outline: "none" }} />
              </div>
              <div>
                <div style={{ fontSize: 10, color: "#3a5a7a", letterSpacing: ".1em", marginBottom: 6 }}>DATE</div>
                <input type="date" value={form.date} onChange={e => update("date", e.target.value)}
                  style={{ width: "100%", background: "#0a1525", border: "1px solid #0d2040", borderRadius: 8, padding: "11px 14px", color: "#c8d8f0", fontFamily: "inherit", fontSize: 13, outline: "none" }} />
              </div>
            </div>

            {error && (
              <div style={{ background: "#1a0a0a", border: "1px solid #ff4d6a44", borderRadius: 8, padding: "10px 12px", fontSize: 12, color: "#ff8c9a" }}>✗ {error}</div>
            )}

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginTop: 4 }}>
              <button onClick={onClose} style={{ background: "#0a1525", border: "1px solid #0d2040", borderRadius: 10, padding: "12px", color: "#5a7090", fontFamily: "inherit", fontSize: 12, cursor: "pointer" }}>
                Cancel
              </button>
              <button onClick={handleSubmit} disabled={loading} style={{ background: "linear-gradient(135deg,#00f5c4,#0088ff)", border: "none", borderRadius: 10, padding: "12px", color: "#060d1a", fontFamily: "'Syne',sans-serif", fontWeight: 700, fontSize: 12, cursor: loading ? "not-allowed" : "pointer", opacity: loading ? .6 : 1 }}>
                {loading ? "⟳ SAVING..." : "ADD EXPENSE"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}