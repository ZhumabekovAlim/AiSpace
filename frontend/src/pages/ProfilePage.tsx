import { useState } from "react";
import { ApiError, api } from "../api";
import { useApp } from "../context";

export function ProfilePage() {
  const { user, refreshUser } = useApp();
  const [phone, setPhone] = useState(user?.phone ?? "");
  const [code, setCode] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  const savePhone = async () => {
    setMsg(null);
    setBusy(true);
    try {
      await api.updateMe({ phone: phone || null });
      await refreshUser();
      setMsg({ ok: true, text: "Телефон сохранён." });
    } catch (e) {
      setMsg({ ok: false, text: e instanceof ApiError ? e.message : "Ошибка" });
    } finally {
      setBusy(false);
    }
  };

  const getCode = async () => {
    setBusy(true);
    try {
      const r = await api.telegramCode();
      setCode(r.code);
    } catch (e) {
      setMsg({ ok: false, text: e instanceof ApiError ? e.message : "Ошибка" });
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Профиль</h1>
          <p className="muted">Контакты и привязка Telegram</p>
        </div>
      </div>

      <section className="card profile-card">
        <div className="profile-row">
          <span className="muted">Имя</span>
          <span>{user?.full_name}</span>
        </div>
        <div className="profile-row">
          <span className="muted">Email</span>
          <span>{user?.email}</span>
        </div>
        <label>
          Телефон <span className="muted">(общий для веба и Telegram)</span>
          <div className="nl-row">
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+7 700 123 45 67"
            />
            <button onClick={savePhone} disabled={busy}>
              Сохранить
            </button>
          </div>
        </label>
        {msg && <p className={msg.ok ? "ok" : "error"}>{msg.text}</p>}
      </section>

      <section className="card">
        <h3>Telegram</h3>
        {user?.telegram_linked ? (
          <p className="ok">✓ Telegram привязан к этому аккаунту.</p>
        ) : (
          <>
            <p className="muted">
              Два способа привязать бота, чтобы бронировать голосом и получать пуши:
            </p>
            <ol className="link-steps">
              <li>
                <b>По телефону:</b> откройте бота и нажмите «📱 Поделиться номером»
                (номер должен совпадать с указанным выше).
              </li>
              <li>
                <b>Кодом:</b> получите код ниже и отправьте боту{" "}
                <code>/link КОД</code>.
              </li>
            </ol>
            {code ? (
              <div className="link-code">
                Ваш код: <b>{code}</b> — отправьте боту <code>/link {code}</code>
                <div className="muted small">Код действует 15 минут.</div>
              </div>
            ) : (
              <button onClick={getCode} disabled={busy}>
                Получить код привязки
              </button>
            )}
          </>
        )}
      </section>
    </>
  );
}
