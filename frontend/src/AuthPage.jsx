// frontend/src/AuthPage.jsx
// Aura — Login & Signup Page

import { useState } from "react";

const API = import.meta.env?.VITE_API_URL || "http://localhost:8000";

const CSS = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@700;800&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  .auth-input {
    width: 100%; background: #0a1525; border: 1px solid #0d2040;
    border-radius: 8px; padding: 12px 14px; color: #c8d8f0;
    font-family: 'DM Mono', monospace; font-size: 13px; outline: none;
    transition: border-color .2s;
  }
  .auth-input:focus { border-color: #00f5c4; }
  .auth-input::placeholder { color: #2a4a6a; }
  .auth-btn {
    width: 100%; background: linear-gradient(135deg,#00f5c4,#0088ff);
    color: #060d1a; border: none; border-radius: 10px; padding: 14px;
    font-family: 'Syne', sans-serif; font-weight: 700; font-size: 14px;
    cursor: pointer; letter-spacing: .06em;
    box-shadow: 0 0 24px #00f5c433; transition: all .2s;
  }
  .auth-btn:hover { opacity: .9; transform: translateY(-1px); }
  .auth-btn:disabled { opacity: .5; cursor: not-allowed; transform: none; }
  .fade-in { animation: fi .4s ease forwards; }
  @keyframes fi { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
  .shake { animation: shake .3s ease; }
  @keyframes shake { 0%,100%{transform:translateX(0)} 25%{transform:translateX(-8px)} 75%{transform:translateX(8px)} }
`;

export default function AuthPage({ onAuth }) {
  const [mode, setMode] = useState("login"); // "login" | "signup"
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [shake, setShake] = useState(false);

  const [form, setForm] = useState({
    username: "", email: "", password: "", full_name: "", monthly_income: ""
  });

  const update = (k, v) => setForm(f => ({ ...f, [k]: v }));

  async function handleSubmit() {
    setError(""); setLoading(true);
    try {
      let res, data;
      if (mode === "login") {
        const body = new URLSearchParams();
        body.append("username", form.username);
        body.append("password", form.password);
        res = await fetch(`${API}/auth/token`, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body
        });
      } else {
        res = await fetch(`${API}/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            username: form.username, email: form.email,
            password: form.password, full_name: form.full_name,
            monthly_income: parseFloat(form.monthly_income) || 0
          })
        });
      }
      data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Something went wrong");
      }
      // Fetch full profile to ensure monthly_income is included
      let userObj = data.user;
      try {
        const meRes = await fetch(`${API}/auth/me`, {
          headers: { "Authorization": "Bearer " + data.access_token }
        });
        if (meRes.ok) {
          const meData = await meRes.json();
          userObj = { ...userObj, ...meData };
        }
      } catch (e) {}
      localStorage.setItem("aura_token", data.access_token);
      localStorage.setItem("aura_user", JSON.stringify(userObj));
      onAuth(data.access_token, userObj);
    } catch (e) {
      setError(e.message);
      setShake(true);
      setTimeout(() => setShake(false), 400);
    }
    setLoading(false);
  }

  return (
    <div style={{
      fontFamily: "'DM Mono', monospace", background: "#060d1a",
      minHeight: "100vh", display: "flex", alignItems: "center",
      justifyContent: "center", color: "#c8d8f0"
    }}>
      <style>{CSS}</style>

      {/* Background glow */}
      <div style={{ position: "fixed", top: "20%", left: "50%", transform: "translateX(-50%)", width: 400, height: 400, background: "radial-gradient(circle, #00f5c415 0%, transparent 70%)", pointerEvents: "none" }} />

      <div className="fade-in" style={{ width: "100%", maxWidth: 420, padding: "0 20px" }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <div style={{ width: 52, height: 52, borderRadius: "50%", background: "linear-gradient(135deg,#00f5c4,#0088ff)", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px", boxShadow: "0 0 30px #00f5c455", fontSize: 24 }}>✦</div>
          <div style={{ fontFamily: "'Syne',sans-serif", fontSize: 28, fontWeight: 800, color: "#fff", letterSpacing: "-.02em" }}>AURA</div>
          <div style={{ fontSize: 10, color: "#3a5a7a", letterSpacing: ".2em", marginTop: 4 }}>AUTONOMOUS WEALTH PILOT</div>
        </div>

        {/* Card */}
        <div className={shake ? "shake" : ""} style={{ background: "#080f1e", border: "1px solid #0d2040", borderRadius: 16, padding: "32px 28px" }}>
          {/* Tabs */}
          <div style={{ display: "flex", gap: 4, marginBottom: 28, background: "#0a1525", borderRadius: 10, padding: 4 }}>
            {["login", "signup"].map(m => (
              <button key={m} onClick={() => { setMode(m); setError(""); }} style={{
                flex: 1, background: mode === m ? "#00f5c422" : "none",
                color: mode === m ? "#00f5c4" : "#3a5a7a", border: "none",
                borderRadius: 8, padding: "8px", fontFamily: "inherit",
                fontSize: 12, cursor: "pointer", letterSpacing: ".08em",
                transition: "all .2s", fontWeight: mode === m ? 500 : 400
              }}>
                {m === "login" ? "SIGN IN" : "CREATE ACCOUNT"}
              </button>
            ))}
          </div>

          {/* Fields */}
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {mode === "signup" && (
              <>
                <div>
                  <div style={{ fontSize: 10, color: "#3a5a7a", letterSpacing: ".1em", marginBottom: 6 }}>FULL NAME</div>
                  <input className="auth-input" placeholder="Priya Sharma" value={form.full_name} onChange={e => update("full_name", e.target.value)} />
                </div>
                <div>
                  <div style={{ fontSize: 10, color: "#3a5a7a", letterSpacing: ".1em", marginBottom: 6 }}>EMAIL</div>
                  <input className="auth-input" type="email" placeholder="priya@email.com" value={form.email} onChange={e => update("email", e.target.value)} />
                </div>
              </>
            )}

            <div>
              <div style={{ fontSize: 10, color: "#3a5a7a", letterSpacing: ".1em", marginBottom: 6 }}>USERNAME</div>
              <input className="auth-input" placeholder="priya" value={form.username} onChange={e => update("username", e.target.value)} onKeyDown={e => e.key === "Enter" && handleSubmit()} />
            </div>

            <div>
              <div style={{ fontSize: 10, color: "#3a5a7a", letterSpacing: ".1em", marginBottom: 6 }}>PASSWORD</div>
              <input className="auth-input" type="password" placeholder="••••••••" value={form.password} onChange={e => update("password", e.target.value)} onKeyDown={e => e.key === "Enter" && handleSubmit()} />
            </div>

            {mode === "signup" && (
              <div>
                <div style={{ fontSize: 10, color: "#3a5a7a", letterSpacing: ".1em", marginBottom: 6 }}>MONTHLY INCOME (₹)</div>
                <input className="auth-input" type="number" placeholder="85000" value={form.monthly_income} onChange={e => update("monthly_income", e.target.value)} />
              </div>
            )}
          </div>

          {/* Error */}
          {error && (
            <div style={{ marginTop: 14, background: "#1a0a0a", border: "1px solid #ff4d6a44", borderRadius: 8, padding: "10px 12px", fontSize: 12, color: "#ff8c9a" }}>
              ✗ {error}
            </div>
          )}

          {/* Submit */}
          <button className="auth-btn" style={{ marginTop: 20 }} onClick={handleSubmit} disabled={loading}>
            {loading ? "⟳ LOADING..." : mode === "login" ? "SIGN IN TO AURA" : "CREATE ACCOUNT"}
          </button>

          {mode === "login" && (
            <div style={{ marginTop: 16, textAlign: "center", fontSize: 11, color: "#3a5a7a" }}>
              Demo: username <span style={{ color: "#00f5c4" }}>priya</span> / password <span style={{ color: "#00f5c4" }}>aura2025</span>
            </div>
          )}
        </div>

        <div style={{ textAlign: "center", marginTop: 20, fontSize: 10, color: "#1a3a5a" }}>
          BUILT BY 3G2B · ORCHESTRON 2025
        </div>
      </div>
    </div>
  );
}