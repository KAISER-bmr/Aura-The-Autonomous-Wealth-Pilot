// frontend/src/NotificationPanel.jsx
// Aura — Notification Panel

import { useState, useEffect } from "react";

export default function NotificationPanel({ token, onClose }) {
  const API = import.meta.env?.VITE_API_URL || "http://localhost:8000";
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadNotifications();
  }, []);

  async function loadNotifications() {
    try {
      const res = await fetch(`${API}/api/notifications`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      const data = await res.json();
      setNotifications(data.notifications || []);
      // Mark as read
      await fetch(`${API}/api/notifications/read`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
      });
    } catch (e) {}
    setLoading(false);
  }

  const severityColor = (s) => s === "danger" ? "#ff4d6a" : s === "warning" ? "#f5a500" : "#0088ff";
  const severityBg = (s) => s === "danger" ? "#1a0a0a" : s === "warning" ? "#1a1200" : "#0a1525";
  const severityIcon = (s) => s === "danger" ? "🚨" : s === "warning" ? "⚠️" : "💡";

  return (
    <div style={{ position: "fixed", inset: 0, background: "#000000aa", display: "flex", alignItems: "flex-start", justifyContent: "flex-end", zIndex: 1000, paddingTop: 60, paddingRight: 20 }}
         onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={{ background: "#080f1e", border: "1px solid #0d2040", borderRadius: 16, width: 360, maxHeight: "80vh", overflow: "hidden", display: "flex", flexDirection: "column", fontFamily: "'DM Mono', monospace", boxShadow: "0 20px 60px #00000088" }}>

        <div style={{ padding: "18px 20px", borderBottom: "1px solid #0d2040", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{ fontFamily: "'Syne',sans-serif", fontSize: 16, fontWeight: 700, color: "#fff" }}>Notifications</div>
            <div style={{ fontSize: 10, color: "#3a5a7a", letterSpacing: ".1em" }}>{notifications.length} ALERTS</div>
          </div>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "#3a5a7a", fontSize: 18, cursor: "pointer" }}>✕</button>
        </div>

        <div style={{ overflowY: "auto", flex: 1, padding: "12px" }}>
          {loading ? (
            <div style={{ textAlign: "center", padding: "30px 0", color: "#3a5a7a", fontSize: 12 }}>Loading...</div>
          ) : notifications.length === 0 ? (
            <div style={{ textAlign: "center", padding: "40px 0" }}>
              <div style={{ fontSize: 28, marginBottom: 12 }}>✦</div>
              <div style={{ color: "#3a5a7a", fontSize: 12 }}>All clear! No alerts.</div>
              <div style={{ color: "#1a3a5a", fontSize: 11, marginTop: 4 }}>Add expenses to see spending alerts.</div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {notifications.map((n, i) => (
                <div key={i} style={{ background: severityBg(n.severity), border: `1px solid ${severityColor(n.severity)}33`, borderRadius: 10, padding: "12px 14px" }}>
                  <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                    <span style={{ fontSize: 14 }}>{severityIcon(n.severity)}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 12, color: severityColor(n.severity), fontWeight: 500, marginBottom: 4 }}>{n.title}</div>
                      <div style={{ fontSize: 11, color: "#7a9ab8", lineHeight: 1.6 }}>{n.message}</div>
                      <div style={{ fontSize: 10, color: "#2a4a6a", marginTop: 6 }}>
                        {new Date(n.created_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}