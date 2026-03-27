import { useState } from "react";
import ReactDOM from "react-dom/client";
import AuthPage from "./AuthPage.jsx";
import AuraDashboard from "./AuraDashboard.jsx";

function App() {
  const [token, setToken] = useState(localStorage.getItem("aura_token"));
  const [user, setUser] = useState(() => {
    const u = localStorage.getItem("aura_user");
    return u ? JSON.parse(u) : null;
  });

  function handleAuth(t, u) { setToken(t); setUser(u); }

  function handleLogout() {
    localStorage.removeItem("aura_token");
    localStorage.removeItem("aura_user");
    setToken(null); setUser(null);
  }

  if (!token || !user) return <AuthPage onAuth={handleAuth} />;
  return <AuraDashboard token={token} user={user} onLogout={handleLogout} />;
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);