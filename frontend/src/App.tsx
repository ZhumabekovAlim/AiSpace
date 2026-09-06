import { useEffect, useState } from "react";
import { api, tokenStore, type User } from "./api";
import { AuthForm } from "./AuthForm";
import { Dashboard } from "./Dashboard";

export function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // При загрузке пробуем восстановить сессию по сохранённому токену.
  useEffect(() => {
    if (!tokenStore.get()) {
      setLoading(false);
      return;
    }
    api
      .me()
      .then(setUser)
      .catch(() => tokenStore.clear())
      .finally(() => setLoading(false));
  }, []);

  const logout = () => {
    tokenStore.clear();
    setUser(null);
  };

  if (loading) return <div className="center muted">Загрузка…</div>;

  return (
    <div className="app">
      <header className="topbar">
        <span className="brand">AiSpace</span>
        {user && (
          <span className="userbox">
            {user.full_name}
            {user.role === "admin" && <span className="badge">admin</span>}
            <button className="link" onClick={logout}>
              выйти
            </button>
          </span>
        )}
      </header>
      <main>
        {user ? (
          <Dashboard user={user} />
        ) : (
          <AuthForm onAuthed={() => api.me().then(setUser)} />
        )}
      </main>
    </div>
  );
}
