import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiJson } from "../api/client";
import { publicAssetUrl } from "../lib/publicAssetUrl";

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@demo.local");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await apiJson("/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: email.trim(), password }),
      });
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-panel">
        <div className="login-brand">
          <img
            src={publicAssetUrl("intentcenter-logo.svg")}
            alt="IntentCenter"
            className="login-wordmark"
            width={280}
            height={56}
          />
          <p className="brand-tagline login-brand-tagline">The operator console for intent-based networks</p>
        </div>
        <h2>Sign in</h2>
      {error ? <div className="error-banner">{error}</div> : null}
      <form onSubmit={onSubmit}>
        <label className="muted" htmlFor="email">
          Email
        </label>
        <input
          id="email"
          className="input"
          style={{ marginTop: "0.35rem", marginBottom: "0.75rem" }}
          type="email"
          autoComplete="username"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <label className="muted" htmlFor="password">
          Password
        </label>
        <input
          id="password"
          className="input"
          style={{ marginTop: "0.35rem", marginBottom: "1rem" }}
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button type="submit" className="btn btn-primary" disabled={loading || !email.trim() || !password}>
          {loading ? "Signing in…" : "Continue"}
        </button>
      </form>
      </div>
    </div>
  );
}
