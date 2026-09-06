import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError } from "../api";
import { useApp } from "../context";

export function LoginPage() {
  const { login, register } = useApp();
  const navigate = useNavigate();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (mode === "register") await register(email, fullName, password);
      else await login(email, password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ошибка сети");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-screen">
      <div className="card auth">
        <div className="auth-brand">AiSpace</div>
        <p className="muted auth-sub">Бронирование переговорных комнат</p>
        <h2>{mode === "login" ? "Вход" : "Регистрация"}</h2>
        <form onSubmit={submit}>
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          {mode === "register" && (
            <label>
              Имя
              <input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            </label>
          )}
          <label>
            Пароль
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={6}
              required
            />
          </label>
          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={busy}>
            {busy ? "…" : mode === "login" ? "Войти" : "Зарегистрироваться"}
          </button>
        </form>
        <p className="muted switch">
          {mode === "login" ? "Нет аккаунта?" : "Уже есть аккаунт?"}{" "}
          <button
            className="link"
            onClick={() => {
              setMode(mode === "login" ? "register" : "login");
              setError(null);
            }}
          >
            {mode === "login" ? "Регистрация" : "Вход"}
          </button>
        </p>
      </div>
    </div>
  );
}
