import { useState } from "react";
import { ApiError, api } from "./api";

export function AuthForm({ onAuthed }: { onAuthed: () => void }) {
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
      if (mode === "register") {
        await api.register(email, fullName, password);
      }
      await api.login(email, password);
      onAuthed();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ошибка сети");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card auth">
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
  );
}
